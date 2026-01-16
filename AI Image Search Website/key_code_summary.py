# ==============================================================================
# AI以图搜图网站 - 关键代码汇总 (Key Code Summary)
#
# 本文件旨在摘录并展示项目的核心代码片段，便于快速理解项目实现。
# 文件本身不可直接运行，仅供阅读和评审。
# ==============================================================================

# --- 1. Web服务与核心API (源文件: assignments/server.py) ---
# 作用：使用FastAPI搭建Web服务，提供/search接口，并实现了查询特征缓存。
# 这是连接用户、前端和后端算法的桥梁。
# ------------------------------------------------------------------------------

import os
import time
import hashlib
from collections import OrderedDict
from typing import List, Dict, Any, Optional

import numpy as np
from fastapi import FastAPI, UploadFile, File

# -- 1.1 查询特征缓存 (源文件: assignments/server.py) --
# 作用：对上传图片计算哈希，缓存其特征向量，避免对同一图片重复进行耗时的模型推理。
# 采用LRU (最近最少使用) + TTL (过期时间) 策略。
_FEATURE_CACHE: "OrderedDict[str, tuple[float, np.ndarray]]" = OrderedDict()
_FEATURE_CACHE_MAX_ITEMS = 256
_FEATURE_CACHE_TTL_SEC = 3600

def _feature_cache_get(key: str) -> Optional[np.ndarray]:
    """从缓存中获取特征，如果不存在或已过期则返回None。"""
    item = _FEATURE_CACHE.get(key)
    if item is None: return None
    ts, feat = item
    if time.time() - ts > _FEATURE_CACHE_TTL_SEC:
        _FEATURE_CACHE.pop(key, None)
        return None
    _FEATURE_CACHE.move_to_end(key) # LRU: 触碰则移动到末尾
    return feat

def _feature_cache_set(key: str, feat: np.ndarray) -> None:
    """将特征存入缓存，并维护缓存大小。"""
    _FEATURE_CACHE[key] = (time.time(), feat)
    while len(_FEATURE_CACHE) > _FEATURE_CACHE_MAX_ITEMS:
        _FEATURE_CACHE.popitem(last=False) # 弹出最久未使用的

# -- 1.2 核心搜索接口 (源文件: assignments/server.py) --
# 作用：接收上传图片，处理特征提取（含缓存）、FAISS召回、重排序，并返回JSON结果。
@app.post("/search")
async def search_api(file: UploadFile = File(...), topk: int = 10, rerank: bool = True, multi_scale: bool = False) -> List[Dict[str, Any]]:
    content = await file.read()

    # 1. 查询特征（优先走缓存）
    content_hash = hashlib.sha1(content).hexdigest()
    q_feat = _feature_cache_get(content_hash)
    if q_feat is None:
        # 缓存未命中：提取特征并存入缓存
        q_feat = extract_feature_from_upload(content, use_multi_scale=multi_scale)
        _feature_cache_set(content_hash, q_feat)

    # 2. 检索（FAISS召回 + 可选重排序）
    if rerank:
        # 两阶段：先用FAISS快速召回200个候选，再对候选集做精排
        topk_coarse = min(200, len(GALLERY_METAS))
        idx_coarse, _ = cosine_topk(q_feat, GALLERY_FEATS, k=topk_coarse)
        feats_coarse = GALLERY_FEATS[idx_coarse]
        
        # 在候选集上执行重排序
        from search_enhancements import rerank_topk_enhanced
        idx_in_coarse, sims = rerank_topk_enhanced(q_feat, feats_coarse, topk_final=topk)
        final_indices = idx_coarse[idx_in_coarse]
    else:
        # 单阶段：直接用FAISS返回Top-K
        final_indices, sims = cosine_topk(q_feat, GALLERY_FEATS, k=topk)

    # 3. 组装并返回结果
    results = []
    for i, s in zip(final_indices.tolist(), sims.tolist()):
        meta = GALLERY_METAS[i]
        img_path = meta.get("path") or meta.get("local_path")
        results.append({
            "score": float(s),
            "image": "/images/" + os.path.basename(img_path) if img_path else None,
            # ... 其他元数据
        })
    return results

# --- 2. 离线图库构建 (源文件: assignments/build_gallery_gpu.py) ---
# 作用：从data.csv读取数据，并发下载图片，并用GPU批量抽取特征，最后保存为图库文件。
# 实现了断点续跑和增量更新。
# ------------------------------------------------------------------------------

def build_gallery_main(): # 伪代码，展示核心逻辑
    # 1. 加载已有图库，获取已处理的URL集合，实现断点续跑
    existing_urls = load_existing_urls("gallery/paths.json")

    # 2. 读取data.csv，筛选出新图片
    new_rows = read_csv_and_filter("data.csv", existing_urls)

    # 3. 多线程并发下载新图片
    # with ThreadPoolExecutor(max_workers=64) as ex:
    #     futures = {ex.submit(download_image, r['url'], r['local_path']): r for r in new_rows}
    #     # ... (处理下载结果)
    ok_rows = concurrent_download(new_rows)

    # 4. GPU批量特征提取
    # device = "cuda"
    # model = AutoModel.from_pretrained("facebook/dinov2-base").to(device).eval()
    # with torch.no_grad():
    #     for batch in batches(ok_rows):
    #         inputs = processor(images=batch, return_tensors="pt").to(device)
    #         outputs = model(**inputs)
    #         # ... (提取并融合特征)
    new_feats = extract_features_gpu(ok_rows)

    # 5. 合并新旧图库并保存
    # final_feats = np.vstack([existing_feats, new_feats])
    # final_metas = existing_metas + new_metas
    # np.save("gallery/features.npy", final_feats)
    # json.dump(final_metas, open("gallery/paths.json", "w"))
    pass

# --- 3. 向量检索与FAISS (源文件: assignments/search_gallery.py) ---
# 作用：封装了向量检索的核心能力，包括加载图库特征、构建FAISS索引和执行Top-K搜索。
# ------------------------------------------------------------------------------

# import faiss

_FAISS_INDEX = None

def load_gallery(gallery_dir: str):
    """加载特征和元数据，并构建FAISS索引。"""
    global _FAISS_INDEX
    feats = np.load(os.path.join(gallery_dir, "features.npy")).astype(np.float32)
    # ... (加载 paths.json)
    
    # 使用余弦相似度：先对库中所有特征L2归一化
    feats_norm = feats / np.linalg.norm(feats, axis=1, keepdims=True)
    
    # 构建FAISS索引，使用内积（IP）计算相似度
    index = faiss.IndexFlatIP(feats.shape[1])
    index.add(feats_norm)
    _FAISS_INDEX = index
    print(f"[FAISS] 索引已构建：N={feats.shape[0]}, dim={feats.shape[1]}")
    # ... (返回feats, metas)

def cosine_topk(query: np.ndarray, feats: np.ndarray, k: int = 10):
    """使用FAISS索引执行Top-K余弦相似度搜索。"""
    # 1. 对查询向量也做L2归一化
    q_norm = query / np.linalg.norm(query)
    
    # 2. 在FAISS索引中搜索
    # FAISS的内积搜索等价于对归一化向量的余弦相似度搜索
    distances, indices = _FAISS_INDEX.search(q_norm[None, :], k)
    
    return indices[0], distances[0]

# --- 4. 检索增强：重排序 (源文件: assignments/search_enhancements.py) ---
# 作用：在FAISS快速召回的候选集上，使用更精细的混合相似度进行重排序，提升精度。
# ------------------------------------------------------------------------------

def rerank_topk_enhanced(query: np.ndarray, feats: np.ndarray, topk_final: int = 10) -> tuple:
    """两阶段检索的第二阶段：精细重排序。"""
    # 1. 归一化查询向量和候选集特征
    q_norm = query / (np.linalg.norm(query) + 1e-12)
    f_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
    
    # 2. 计算混合相似度
    # a. 余弦相似度 (Cosine)
    cosine_sims = f_norm @ q_norm
    
    # b. 欧氏距离相似度 (Euclidean)
    euclidean_dists = np.linalg.norm(f_norm - q_norm, axis=1)
    euclidean_sims = 1.0 / (1.0 + euclidean_dists)
    
    # c. 归一化到[0,1]范围并加权融合
    cosine_sims_norm = (cosine_sims + 1) / 2
    hybrid_sims = 0.7 * cosine_sims_norm + 0.3 * euclidean_sims_norm
    
    # 3. 在候选集内按混合相似度排序，并返回最终的Top-K
    fine_idx_in_coarse = np.argsort(-hybrid_sims)[:topk_final]
    
    return fine_idx_in_coarse, hybrid_sims[fine_idx_in_coarse]

# --- 5. 模型推理 (源文件: assignments/dinov2_numpy.py) ---
# 作用：用NumPy手工实现Vision Transformer的核心模块，特别是Transformer Block。
# ------------------------------------------------------------------------------

class Attention:
    """多头自注意力机制的NumPy实现。"""
    def __call__(self, x: np.ndarray) -> np.ndarray:
        B, N, C = x.shape
        # 1. 线性变换得到 q, k, v
        qkv = x @ self.qkv_weight.T + self.qkv_bias
        qkv = qkv.reshape(B, N, 3, self.num_heads, C // self.num_heads).transpose(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # 2. 计算注意力分数 (scaled dot-product)
        attn = (q @ k.transpose(0, 1, 3, 2)) * self.scale
        attn = np.apply_along_axis(lambda x: np.exp(x - np.max(x)) / np.sum(np.exp(x - np.max(x))), -1, attn) # Softmax

        # 3. 加权求和
        x = (attn @ v).transpose(0, 2, 1, 3).reshape(B, N, C)

        # 4. 输出线性变换
        x = x @ self.proj_weight.T + self.proj_bias
        return x

class Block:
    """一个完整的Transformer Block的NumPy实现。"""
    def __call__(self, x: np.ndarray) -> np.ndarray:
        # 1. 自注意力分支 (含LayerNorm, LayerScale和残差连接)
        x = x + self.scale1(self.attn(self.norm1(x)))
        
        # 2. MLP分支 (含LayerNorm, LayerScale和残差连接)
        x = x + self.scale2(self.mlp(self.norm2(x)))
        return x

# --- 6. 数值稳定 (源文件: assignments/weight_stabilize.py) ---
# 作用：通过权重裁剪解决DINOv2在NumPy推理时遇到的数值爆炸问题。
# ------------------------------------------------------------------------------

def stabilize_weights(weights: dict, layer_idx: int = 8, max_norm: float = 2.0) -> dict:
    """对指定层的MLP权重进行行范数裁剪。"""
    key = f"encoder.layer.{layer_idx}.mlp.fc1.weight"
    w = weights[key].astype(np.float64)
    
    # 计算每一行的L2范数
    row_norms = np.linalg.norm(w, axis=1)
    
    # 找到需要裁剪的行
    clip_indices = np.where(row_norms > max_norm)[0]
    
    # 对这些行进行缩放
    for i in clip_indices:
        w[i] *= max_norm / row_norms[i]
        
    stabilized_weights = weights.copy()
    stabilized_weights[key] = w.astype(weights[key].dtype)
    return stabilized_weights
