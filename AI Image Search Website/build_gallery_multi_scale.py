"""使用多尺度特征构建图库（提升搜索准确率）。

使用方法：
    python build_gallery_multi_scale.py --num-images 5000

注意：这会显著增加特征提取时间（约3倍），但能大幅提升搜索准确率。
"""
import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from PIL import Image

from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights
from multi_scale_features import extract_multi_scale_features

# 导入 build_gallery.py 中的辅助函数
from build_gallery import (
    _safe_filename,
    download_image,
    _load_csv_first_n,
    STABILIZE_MAX_NORM,
)

# 特征版本
FEATURE_VERSION = "v4-dinov2-base-resize224-stabilize-l8-max2.0-fused-multiscale"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-images", type=int, default=5000, help="要处理的图片数量（建议至少5000）")
    parser.add_argument("--quick-test", type=int, default=None, help="快速测试模式：只处理前N张图片")
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "data.csv")

    gallery_dir = os.path.join(base_dir, "gallery")
    images_dir = os.path.join(base_dir, "gallery_images")
    os.makedirs(gallery_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    failures_path = os.path.join(gallery_dir, "download_failures.txt")
    feats_path = os.path.join(gallery_dir, "features.npy")
    metas_path = os.path.join(gallery_dir, "paths.json")

    # 加载已有图库
    existing_feats = None
    existing_metas = []
    existing_urls = set()
    if os.path.exists(feats_path) and os.path.exists(metas_path):
        try:
            existing_feats = np.load(feats_path)
            with open(metas_path, "r", encoding="utf-8") as f:
                raw_meta = json.load(f)
            if isinstance(raw_meta, dict) and "items" in raw_meta:
                existing_metas = raw_meta.get("items", [])
            else:
                existing_metas = raw_meta
            existing_urls = {m.get("url") for m in existing_metas if m.get("url")}
            print(f"检测到已有图库: {len(existing_metas)} 张图片")
        except Exception as e:
            print(f"警告：加载已有图库失败: {e}")

    df = _load_csv_first_n(csv_path, nrows=args.num_images)

    rows = []
    skipped_count = 0
    cached_count = 0
    for _, r in df.iterrows():
        url = str(r["image_url"]).strip()
        caption = "" if pd.isna(r["caption"]) else str(r["caption"]).strip()
        if not url:
            continue
        if url in existing_urls:
            skipped_count += 1
            continue
        filename = _safe_filename(url)
        local_path = os.path.join(images_dir, filename)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            cached_count += 1
            rows.append({"url": url, "caption": caption, "local_path": local_path, "cached": True})
        else:
            rows.append({"url": url, "caption": caption, "local_path": local_path, "cached": False})

    download_count = sum(1 for r in rows if not r.get("cached", False))
    print(f"准备处理: {len(rows)} 张（跳过 {skipped_count}，缓存 {cached_count}，需下载 {download_count}）")

    # 下载图片（如果需要）
    if download_count > 0:
        print(f"开始下载 {download_count} 张图片...")
        download_rows = [r for r in rows if not r.get("cached", False)]
        ok_rows = []
        with ThreadPoolExecutor(max_workers=64) as ex:
            futures = {
                ex.submit(download_image, r["url"], r["local_path"], timeout=30, retries=2): r
                for r in download_rows
            }
            for fut in as_completed(futures):
                r = futures[fut]
                ok, msg = fut.result()
                if ok:
                    ok_rows.append(r)
        rows = [r for r in rows if r.get("cached", False)] + ok_rows

    # 图片质量过滤
    cleaned_rows = []
    for r in rows:
        p = r["local_path"]
        try:
            with Image.open(p) as im:
                w, h = im.size
            if w < 64 or h < 64 or w > 4096 or h > 4096:
                continue
            cleaned_rows.append(r)
        except Exception:
            continue

    if args.quick_test:
        cleaned_rows = cleaned_rows[:args.quick_test]
        print(f"[快速测试] 只处理前 {len(cleaned_rows)} 张")

    # 加载模型
    weights = np.load(os.path.join(base_dir, "vit-dinov2-base.npz"))
    weights = stabilize_weights(weights, layer_idx=8, max_norm=STABILIZE_MAX_NORM)
    vit = Dinov2Numpy(weights)

    # 提取多尺度特征
    print(f"开始提取多尺度特征（尺度: 224, 336, 448）...")
    feats = []
    metas = []
    start_time = time.time()

    for idx, r in enumerate(cleaned_rows, start=1):
        try:
            feat = extract_multi_scale_features(
                vit, r["local_path"],
                scales=[224, 336, 448],
                feature_mode="fused"
            )
            feats.append(feat)
            metas.append({
                "url": r["url"],
                "path": os.path.relpath(r["local_path"], base_dir),
                "caption": r["caption"],
            })
        except Exception as e:
            print(f"特征提取失败 {r['url']}: {e}")
            continue

        if idx % 10 == 0 or idx == len(cleaned_rows):
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (len(cleaned_rows) - idx) / rate if rate > 0 else 0
            print(f"进度: {idx}/{len(cleaned_rows)} ({idx*100//len(cleaned_rows)}%)，速度: {rate:.1f} 张/秒，预计剩余: {eta:.0f} 秒")

    if not feats:
        raise RuntimeError("特征提取全失败")

    new_feats = np.array(feats)

    # 合并旧图库
    if existing_feats is not None and existing_metas:
        all_feats = np.concatenate([existing_feats.astype(np.float32), new_feats.astype(np.float32)], axis=0)
        all_metas = existing_metas + metas
    else:
        all_feats = new_feats.astype(np.float32)
        all_metas = metas

    # 保存
    np.save(feats_path, all_feats)
    feats_checksum = hashlib.sha1(all_feats.astype(np.float32).tobytes()).hexdigest()
    feature_info = {
        "version": FEATURE_VERSION,
        "model": "dinov2-base",
        "preprocess": "multi_scale_224_336_448_fused",
        "weight_stabilize": {"layer_idx": 8, "max_norm": STABILIZE_MAX_NORM},
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "num_images": len(all_metas),
        "feature_dim": int(all_feats.shape[1]),
        "checksum": feats_checksum,
    }

    meta_obj = {
        "feature_info": feature_info,
        "items": all_metas,
    }

    with open(metas_path, "w", encoding="utf-8") as f:
        json.dump(meta_obj, f, ensure_ascii=False, indent=2)

    print(f"完成: 新增 {len(metas)} 张，总计 {len(all_metas)} 张，features={all_feats.shape}")


if __name__ == "__main__":
    main()
