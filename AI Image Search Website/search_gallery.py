import hashlib
import json
import os
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights

# 可选：导入混合相似度函数（提升搜索准确率）
try:
    from feature_enhance import hybrid_similarity
    _HAS_HYBRID_SIM = True
except ImportError:
    _HAS_HYBRID_SIM = False

try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except ImportError:  # pragma: no cover - 环境没有安装 faiss 时的备用路径
    faiss = None  # type: ignore
    _HAS_FAISS = False


_FAISS_INDEX = None
_FAISS_DIM: Optional[int] = None
_FEATURE_INFO: Optional[Dict[str, Any]] = None


def load_gallery(gallery_dir: str) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    加载图库特征与元数据；若环境安装了 faiss，则顺便构建内存向量索引。

    同时读取 feature_info（版本号、配置、校验和等），并做基本一致性检查：
    - feats.shape[0] 是否等于 metas 数量
    - 若 paths.json 中带有 checksum，则与当前 feats 计算值比对。
    """
    global _FAISS_INDEX, _FAISS_DIM, _FEATURE_INFO

    feats = np.load(os.path.join(gallery_dir, "features.npy")).astype(np.float32)
    with open(os.path.join(gallery_dir, "paths.json"), "r", encoding="utf-8") as f:
        raw_meta = json.load(f)

    feature_info: Optional[Dict[str, Any]] = None
    if isinstance(raw_meta, dict) and "items" in raw_meta:
        metas = raw_meta.get("items", [])
        feature_info = raw_meta.get("feature_info")
    else:
        # 兼容旧版本：直接就是列表
        metas = raw_meta

    metas = list(metas)
    _FEATURE_INFO = feature_info

    # 一致性检查：数量是否匹配
    if len(metas) != feats.shape[0]:
        print(
            f"[FeatureCheck] 警告：features 行数({feats.shape[0]}) 与 metas 数量({len(metas)}) 不一致。"
        )

    # 一致性检查：校验和（若存在）
    if feature_info and "checksum" in feature_info:
        cur_checksum = hashlib.sha1(feats.astype(np.float32).tobytes()).hexdigest()
        if cur_checksum != feature_info["checksum"]:
            print(
                "[FeatureCheck] 警告：features.npy 与 paths.json 里的 checksum 不一致，"
                "可能是特征文件与元数据未同步。"
            )
        else:
            print(
                f"[FeatureCheck] checksum 校验通过，version={feature_info.get('version')}，"
                f"num_images={feature_info.get('num_images')}，dim={feature_info.get('feature_dim')}"
            )

    if _HAS_FAISS:
        # 使用余弦相似度：先 L2 归一化，然后在 Inner Product 空间做最近邻
        dim = feats.shape[1]
        feats_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
        index = faiss.IndexFlatIP(dim)  # type: ignore[attr-defined]
        index.add(feats_norm)
        _FAISS_INDEX = index
        _FAISS_DIM = dim
        print(f"[FAISS] 索引已构建：N={feats.shape[0]}, dim={dim}")
    else:
        print("[FAISS] 未安装 faiss-cpu，将使用 NumPy 逐批计算相似度。")

    return feats, metas


def extract_feature(img_path: str, base_dir: str) -> np.ndarray:
    # 改进：使用与 build_gallery.py 相同的 max_norm=2.0，确保特征一致性
    STABILIZE_MAX_NORM = 2.0  # 与 build_gallery.py 保持一致
    weights = np.load(os.path.join(base_dir, "vit-dinov2-base.npz"))
    weights = stabilize_weights(weights, layer_idx=8, max_norm=STABILIZE_MAX_NORM)
    vit = Dinov2Numpy(weights)

    pixel_values = resize_short_side(img_path, target_size=224)
    # 改进：使用 fused 模式（融合 CLS 和 patch mean），提升搜索准确率
    feat = vit(pixel_values, feature_mode="fused")[0].astype(np.float32)
    return feat


def cosine_topk(query: np.ndarray, feats: np.ndarray, k: int = 10):
    """
    计算 Top-K 相似图片：
    - 若已构建 FAISS 索引，则优先走 FAISS（适合大规模图库）。
    - 否则退回 NumPy 实现，对中小规模图库同样适用。
    """
    global _FAISS_INDEX, _FAISS_DIM

    q = query.astype(np.float32)
    if _HAS_FAISS and _FAISS_INDEX is not None and _FAISS_DIM is not None:
        # 归一化后用 Inner Product 做余弦相似度
        q = q / (np.linalg.norm(q) + 1e-12)
        D, I = _FAISS_INDEX.search(q[None, :], k)  # type: ignore[union-attr]
        sims = D[0]
        idx = I[0]
        return idx, sims

    # 回退路径：NumPy 直接算相似度
    F = feats.astype(np.float32)
    q = q / (np.linalg.norm(q) + 1e-12)
    F = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-12)
    
    # 改进：使用混合相似度（余弦 + 欧氏距离），提升搜索准确率
    if _HAS_HYBRID_SIM:
        sims = hybrid_similarity(q, F, cosine_weight=0.7)
    else:
        # 回退到标准余弦相似度
        sims = F @ q
    
    idx = np.argsort(-sims)[:k]
    return idx, sims[idx]


def search(img_path: str, topk: int = 10) -> List[Dict[str, Any]]:
    base_dir = os.path.dirname(__file__)
    gallery_dir = os.path.join(base_dir, "gallery")

    feats, metas = load_gallery(gallery_dir)
    q = extract_feature(img_path, base_dir)

    idx, sims = cosine_topk(q, feats, k=min(topk, len(metas)))
    results = []
    for i, s in zip(idx.tolist(), sims.tolist()):
        m = metas[i]
        results.append(
            {
                "score": float(s),
                "url": m.get("url"),
                "path": m.get("path"),
                "caption": m.get("caption", ""),
            }
        )
    return results


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="查询图片路径")
    parser.add_argument("--topk", type=int, default=10)
    args = parser.parse_args()

    res = search(args.query, topk=args.topk)
    for r in res:
        print(f"{r['score']:.4f}\t{r['path']}\t{r['url']}\t{r['caption']}")


if __name__ == "__main__":
    main()
