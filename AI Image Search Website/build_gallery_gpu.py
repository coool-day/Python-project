"""GPU 加速的图库构建脚本。

利用 PyTorch 和 transformers 库在 GPU 上进行批处理特征提取，
速度比 NumPy CPU 版本快 10-50 倍。

使用方法：
    python build_gallery_gpu.py --num-images 5000 --batch-size 32
"""
import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm
from transformers import AutoImageProcessor, AutoModel

# 导入 build_gallery.py 中的辅助函数
from build_gallery import (
    _safe_filename,
    download_image,
    _load_csv_first_n,
)

# 特征版本：v4-gpu，表示使用 GPU 批处理提取，并采用 fused 策略
FEATURE_VERSION = "v4-gpu-dinov2-base-fused"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-images", type=int, default=5000, help="要处理的图片数量")
    parser.add_argument("--batch-size", type=int, default=32, help="GPU 特征提取的批处理大小")
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

    # 加载已有图库，实现断点续跑
    existing_metas = []
    existing_urls = set()
    if os.path.exists(metas_path):
        try:
            with open(metas_path, "r", encoding="utf-8") as f:
                raw_meta = json.load(f)
            if isinstance(raw_meta, dict) and "items" in raw_meta:
                existing_metas = raw_meta.get("items", [])
            else:
                existing_metas = raw_meta
            existing_urls = {m.get("url") for m in existing_metas if m.get("url")}
            print(f"检测到已有图库: {len(existing_metas)} 张图片，将跳过已处理的 URL。")
        except Exception as e:
            print(f"警告：加载已有图库失败: {e}")

    df = _load_csv_first_n(csv_path, nrows=args.num_images)

    # 准备待处理列表
    rows_to_process = []
    for _, r in df.iterrows():
        url = str(r["image_url"]).strip()
        if not url or url in existing_urls:
            continue
        filename = _safe_filename(url)
        local_path = os.path.join(images_dir, filename)
        rows_to_process.append({"url": url, "caption": r.get("caption", ""), "local_path": local_path})

    if not rows_to_process:
        print("没有新的图片需要处理。")
        return

    # 下载图片
    print(f"准备下载 {len(rows_to_process)} 张新图片...")
    ok_rows = []
    with tqdm(total=len(rows_to_process), desc="下载图片") as pbar:
        with ThreadPoolExecutor(max_workers=64) as ex:
            futures = {ex.submit(download_image, r["url"], r["local_path"]): r for r in rows_to_process}
            for fut in as_completed(futures):
                ok, _ = fut.result()
                if ok:
                    ok_rows.append(futures[fut])
                pbar.update(1)

    print(f"下载完成，成功 {len(ok_rows)} 张。")
    if not ok_rows:
        return

    # GPU 特征提取
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")
    # 优先使用本地缓存，避免网络超时
    try:
        processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base", local_files_only=True)
        model = AutoModel.from_pretrained("facebook/dinov2-base", local_files_only=True).to(device).eval()
        print("成功从本地缓存加载模型。")
    except Exception as e:
        print(f"从本地缓存加载模型失败: {e}")
        print("请尝试在有网络的环境下运行一次，或手动下载模型到缓存目录。")
        return

    all_feats = []
    all_metas = []
    with torch.no_grad():
        for i in tqdm(range(0, len(ok_rows), args.batch_size), desc="提取特征"):
            batch_rows = ok_rows[i : i + args.batch_size]
            images = []
            valid_rows = []
            for r in batch_rows:
                try:
                    img = Image.open(r["local_path"]).convert("RGB")
                    images.append(img)
                    valid_rows.append(r)
                except Exception:
                    continue
            
            if not images:
                continue

            inputs = processor(images=images, return_tensors="pt").to(device)
            outputs = model(**inputs, output_hidden_states=True)
            last_hidden_state = outputs.last_hidden_state

            # Fused 特征：CLS + Patch Mean
            cls_feat = last_hidden_state[:, 0]
            patch_feat = last_hidden_state[:, 1:].mean(dim=1)
            fused_feat = (cls_feat + patch_feat) / 2.0
            fused_feat = fused_feat / torch.linalg.norm(fused_feat, dim=1, keepdim=True)

            all_feats.append(fused_feat.cpu().numpy())
            all_metas.extend(valid_rows)

    if not all_feats:
        print("特征提取失败。")
        return

    new_feats = np.vstack(all_feats)

    # 合并新旧图库
    if existing_metas:
        existing_feats = np.load(feats_path)
        final_feats = np.vstack([existing_feats, new_feats])
        final_metas = existing_metas + all_metas
    else:
        final_feats = new_feats
        final_metas = all_metas

    # 保存
    np.save(feats_path, final_feats)
    feature_info = {
        "version": FEATURE_VERSION,
        "model": "dinov2-base",
        "feature_mode": "fused",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "num_images": len(final_metas),
    }
    with open(metas_path, "w", encoding="utf-8") as f:
        json.dump({"feature_info": feature_info, "items": final_metas}, f, ensure_ascii=False, indent=2)

    print(f"图库构建完成！本次新增 {len(all_metas)} 张，总计 {len(final_metas)} 张。")

if __name__ == "__main__":
    main()
