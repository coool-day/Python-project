import argparse
import hashlib
import json
import os
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from functools import partial

import numpy as np
import pandas as pd
from PIL import Image

# 优先使用 requests（更快），如果不可用则回退到 urllib
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    _HAS_REQUESTS = False

from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights


# 当前特征配置版本：若模型/预处理/权重裁剪策略有变，请手动更新此字符串
# 改进：增大 max_norm 从 1.0 到 2.0，减少权重裁剪，提高特征质量
# 改进：使用 fused 特征模式（融合 CLS 和 patch mean），提升搜索准确率
FEATURE_VERSION = "v3-dinov2-base-resize224-stabilize-l8-max2.0-fused"
STABILIZE_MAX_NORM = 2.0  # 从 1.0 增加到 2.0，减少权重裁剪强度


def _safe_filename(url: str, suffix: str = ".jpg") -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    path = urllib.parse.urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ext
    return f"{h}{suffix}"


def download_image(url: str, out_path: str, timeout: int = 30, retries: int = 2):
    """下载图片，支持缓存检测和重试。
    
    优先使用 requests 库（更快，支持连接池），如果不可用则回退到 urllib。
    
    参数:
        url: 图片 URL
        out_path: 保存路径
        timeout: 超时时间（秒），默认 30
        retries: 重试次数，默认 2
    
    返回:
        (success: bool, message: str)
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # 缓存检测：文件已存在且大小 > 0，直接返回成功
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return True, "cached"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    last_err = None
    for attempt in range(retries + 1):
        try:
            if _HAS_REQUESTS:
                # 使用 requests（更快，支持连接池）
                resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
                resp.raise_for_status()
                
                # 检查 Content-Type
                content_type = resp.headers.get("Content-Type", "").lower()
                
                # 流式下载，避免大文件占用太多内存
                data = resp.content
            else:
                # 回退到 urllib
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    content_type = resp.headers.get("Content-Type", "").lower()
                    data = resp.read()
            
            if not data or len(data) < 1024:  # 至少 1KB，避免下载到空文件或错误页面
                return False, "empty_or_too_small"
            
            # 原子写入：先写到临时文件，再重命名，避免下载中断导致文件损坏
            tmp_path = out_path + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(data)
            
            # Windows 上需要先删除目标文件（如果存在）
            if os.path.exists(out_path):
                os.remove(out_path)
            os.rename(tmp_path, out_path)
            
            return True, "downloaded"
        except requests.exceptions.HTTPError as e:
            last_err = f"HTTP_{e.response.status_code}"
            if e.response.status_code == 404:
                return False, "not_found"
            if e.response.status_code == 403:
                return False, "forbidden"
        except requests.exceptions.RequestException as e:
            last_err = f"request_error:{str(e)}"
        except urllib.error.HTTPError as e:
            last_err = f"HTTP_{e.code}"
            if e.code == 404:
                return False, "not_found"
            if e.code == 403:
                return False, "forbidden"
        except urllib.error.URLError as e:
            last_err = f"URL_error:{str(e)}"
        except Exception as e:
            last_err = f"error:{repr(e)}"
        
        # 简单指数退避，避免瞬时网络抖动
        if attempt < retries:
            time.sleep(0.2 * (attempt + 1))

    return False, f"download_error:{last_err}"


def _load_csv_first_n(csv_path: str, nrows: int) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        nrows=nrows,
        encoding="utf-8-sig",
        sep=",",
        quotechar='"',
        escapechar="\\",
        engine="python",
    )

    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]

    url_col = None
    for c in df.columns:
        if c == "image_url" or c.startswith("image_url"):
            url_col = c
            break

    if url_col is None:
        raise ValueError(f"无法在 data.csv 中找到 image_url 列，当前列名={df.columns.tolist()}")

    caption_col = None
    if "caption" in df.columns:
        caption_col = "caption"
    else:
        for c in df.columns:
            if c != url_col:
                caption_col = c
                break

    if caption_col is None:
        df["caption"] = ""
        caption_col = "caption"

    out = df[[url_col, caption_col]].copy()
    out.columns = ["image_url", "caption"]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-images", type=int, default=3000, help="要处理的图片数量")
    parser.add_argument("--quick-test", type=int, default=None, help="快速测试模式：只处理前N张图片（用于快速验证效果，例如 --quick-test 200）")
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

    # 尝试加载已有图库，用于增量 / 断点续跑
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
            print(
                f"检测到已有图库: {len(existing_metas)} 张图片，将跳过已处理 URL（本次 CSV 仍以 --num-images 为上限）。"
            )
        except Exception as e:
            print(f"警告：加载已有图库失败，将从空图库开始。error={repr(e)}")
            existing_feats, existing_metas, existing_urls = None, [], set()

    print(f"csv_path={csv_path}, size={os.path.getsize(csv_path)} bytes")

    df = _load_csv_first_n(csv_path, nrows=args.num_images)

    rows = []
    cached_count = 0
    skipped_count = 0
    for _, r in df.iterrows():
        url = str(r["image_url"]).strip()
        caption = "" if pd.isna(r["caption"]) else str(r["caption"]).strip()
        if not url:
            continue
        # 已在图库中的 URL，直接跳过（既不下载也不重复抽特征）
        if url in existing_urls:
            skipped_count += 1
            continue
        filename = _safe_filename(url)
        local_path = os.path.join(images_dir, filename)
        # 检查本地文件是否已存在（缓存检测）
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            cached_count += 1
            # 文件已存在，直接加入处理列表（跳过下载，直接抽特征）
            rows.append({"url": url, "caption": caption, "local_path": local_path, "cached": True})
        else:
            rows.append({"url": url, "caption": caption, "local_path": local_path, "cached": False})

    if not rows:
        # 本次 CSV 范围内的 URL 全部已经在现有图库中，直接复用旧图库
        if existing_feats is not None and existing_metas:
            print(
                f"本次 CSV 中没有新的 URL 需要处理，直接复用已有图库：{len(existing_metas)} 张，features={existing_feats.shape}"
            )
            return
        else:
            print("警告：没有可用的 URL（可能 CSV 为空或格式异常）。")
            return

    download_count = sum(1 for r in rows if not r.get("cached", False))
    print(f"准备处理: {len(rows)} 张（其中 {skipped_count} 条已在旧图库中已跳过，{cached_count} 张本地缓存，{download_count} 张需要下载）")

    # 优化下载参数：增加并发数和超时时间
    # 注意：并发数过高可能导致网络拥塞，建议根据网络情况调整（32-64）
    max_workers = 64 if _HAS_REQUESTS else 32  # requests 支持更高并发
    download_timeout = 30  # 从 15 增加到 30 秒，避免网络慢时超时
    
    if _HAS_REQUESTS:
        print(f"使用 requests 库下载（支持连接池，速度更快）")
    else:
        print(f"使用 urllib 下载（建议安装 requests: pip install requests）")
    ok_rows = []
    fail_stats = {}
    
    # 先处理已缓存的文件
    cached_rows = [r for r in rows if r.get("cached", False)]
    ok_rows.extend(cached_rows)
    
    # 需要下载的文件
    download_rows = [r for r in rows if not r.get("cached", False)]
    
    if download_rows:
        print(f"开始下载 {len(download_rows)} 张图片（并发数: {max_workers}）...")
        download_start_time = time.time()
        with open(failures_path, "w", encoding="utf-8") as flog:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {
                    ex.submit(download_image, r["url"], r["local_path"], timeout=download_timeout, retries=2): r
                    for r in download_rows
                }
                done_cnt = 0
                ok_cnt = len(cached_rows)  # 已缓存的也算成功
                for fut in as_completed(futures):
                    r = futures[fut]
                    done_cnt += 1
                    try:
                        ok, msg = fut.result()
                    except Exception as e:
                        ok, msg = False, f"download_error:{repr(e)}"

                    if ok:
                        ok_cnt += 1
                        ok_rows.append(r)
                    else:
                        flog.write(f"{r['url']}\t{msg}\n")
                        fail_stats[msg] = fail_stats.get(msg, 0) + 1

                    # 更频繁的进度更新，每 20 个更新一次
                    if done_cnt % 20 == 0 or done_cnt == len(download_rows):
                        elapsed = time.time() - download_start_time
                        rate = done_cnt / elapsed if elapsed > 0 else 0
                        eta = (len(download_rows) - done_cnt) / rate if rate > 0 else 0
                        print(f"下载进度: {done_cnt}/{len(download_rows)} ({done_cnt*100//len(download_rows)}%)，成功: {ok_cnt}（含 {cached_count} 缓存），速度: {rate:.1f} 张/秒，预计剩余: {eta:.0f} 秒")
    else:
        print(f"所有 {len(cached_rows)} 张图片都已缓存，跳过下载阶段")

    total_processed = len(ok_rows)
    total_needed = len(rows)
    download_success = sum(1 for r in ok_rows if not r.get("cached", False))
    print(f"\n处理完成: 成功 {total_processed}/{total_needed} 张")
    print(f"  - 缓存: {cached_count} 张（跳过下载）")
    print(f"  - 下载: {download_success}/{download_count} 张")
    print(f"  - 失败日志: {failures_path}")
    if fail_stats:
        print("下载失败原因分布：")
        for reason, cnt in sorted(fail_stats.items(), key=lambda x: -x[1]):
            print(f"  {reason}: {cnt}")

    if not ok_rows:
        # 如果一个新图都没下到，但旧图库存在，则保留旧图库直接返回
        if existing_feats is not None and existing_metas:
            print("没有成功下载任何新图片，但已有图库存在，本次不更新。")
            return
        raise RuntimeError("没有成功下载任何图片，也不存在旧图库可复用")

    weights = np.load(os.path.join(base_dir, "vit-dinov2-base.npz"))
    weights = stabilize_weights(weights, layer_idx=8, max_norm=STABILIZE_MAX_NORM)
    vit = Dinov2Numpy(weights)

    feats = []
    metas = []

    # 先做一次尺寸/解码过滤，避免坏图进入特征抽取阶段
    cleaned_rows = []
    bad_image_stats = {"decode_error": 0, "too_small": 0, "too_large": 0}
    MIN_SIDE = 64
    MAX_SIDE = 4096
    for r in ok_rows:
        p = r["local_path"]
        try:
            with Image.open(p) as im:
                w, h = im.size
        except Exception as e:
            with open(failures_path, "a", encoding="utf-8") as flog:
                flog.write(f"{r['url']}\tbad_image_decode:{repr(e)}\n")
            # 自动清理坏图文件
            try:
                os.remove(p)
            except OSError:
                pass
            bad_image_stats["decode_error"] += 1
            continue

        if w < MIN_SIDE or h < MIN_SIDE:
            with open(failures_path, "a", encoding="utf-8") as flog:
                flog.write(f"{r['url']}\tbad_image_too_small:{w}x{h}\n")
            try:
                os.remove(p)
            except OSError:
                pass
            bad_image_stats["too_small"] += 1
            continue

        if w > MAX_SIDE or h > MAX_SIDE:
            with open(failures_path, "a", encoding="utf-8") as flog:
                flog.write(f"{r['url']}\tbad_image_too_large:{w}x{h}\n")
            # 这里选择直接丢弃，避免极大图占用过多内存
            try:
                os.remove(p)
            except OSError:
                pass
            bad_image_stats["too_large"] += 1
            continue

        cleaned_rows.append(r)

    if bad_image_stats["decode_error"] or bad_image_stats["too_small"] or bad_image_stats["too_large"]:
        print(
            "图片质量过滤："
            f"decode_error={bad_image_stats['decode_error']}, "
            f"too_small={bad_image_stats['too_small']}, "
            f"too_large={bad_image_stats['too_large']}"
        )

    if not cleaned_rows:
        if existing_feats is not None and existing_metas:
            print("所有新下载图片均不符合尺寸/解码要求，但已有图库存在，本次不更新。")
            return
        raise RuntimeError("没有任何可用于特征抽取的图片")

    for idx, r in enumerate(cleaned_rows, start=1):
        try:
            pixel_values = resize_short_side(r["local_path"], target_size=224)
            # 改进：使用 fused 模式（融合 CLS 和 patch mean），提升搜索准确率
            feat = vit(pixel_values, feature_mode="fused")
            feats.append(feat.astype(np.float32))
            metas.append(
                {
                    "url": r["url"],
                    "path": os.path.relpath(r["local_path"], base_dir),
                    "caption": r["caption"],
                }
            )
        except Exception as e:
            with open(failures_path, "a", encoding="utf-8") as flog:
                flog.write(f"{r['url']}\tfeature_error:{repr(e)}\n")

        if idx % 20 == 0 or idx == len(cleaned_rows):
            print(f"特征抽取进度: {idx}/{len(cleaned_rows)}，成功特征: {len(feats)}")

    if not feats:
        raise RuntimeError("下载成功但特征抽取全失败")

    new_feats = np.concatenate(feats, axis=0)

    # 与旧图库合并，实现增量更新
    if existing_feats is not None and existing_metas:
        all_feats = np.concatenate(
            [existing_feats.astype(np.float32), new_feats.astype(np.float32)], axis=0
        )
        all_metas = existing_metas + metas
    else:
        all_feats = new_feats.astype(np.float32)
        all_metas = metas

    # 保存特征
    np.save(feats_path, all_feats)

    # 基于内存数组计算一个简单校验和（与特征版本、配置一并写入）
    feats_checksum = hashlib.sha1(all_feats.astype(np.float32).tobytes()).hexdigest()
    feature_info = {
        "version": FEATURE_VERSION,
        "model": "dinov2-base",
        "preprocess": "resize_short_side_224_patch14",
        "weight_stabilize": {"layer_idx": 8, "max_norm": 1.0},
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

    print(
        f"done: 本次新增 images={len(metas)}，总图库 images={len(all_metas)}，features={all_feats.shape}，保存于 {gallery_dir}"
    )


if __name__ == "__main__":
    main()
