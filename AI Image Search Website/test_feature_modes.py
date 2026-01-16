"""测试不同特征提取模式的效果。"""
import os
import numpy as np
from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights
from search_gallery import load_gallery, cosine_topk


def test_feature_modes():
    """测试不同特征模式的效果。"""
    base_dir = os.path.dirname(__file__)
    gallery_dir = os.path.join(base_dir, "gallery")
    
    # 加载图库
    print("加载图库...")
    feats, metas = load_gallery(gallery_dir)
    print(f"图库规模: {len(metas)} 张图片")
    
    # 加载模型
    weights = np.load(os.path.join(base_dir, "vit-dinov2-base.npz"))
    weights = stabilize_weights(weights, layer_idx=8, max_norm=2.0)
    
    # 测试图片（使用图库中的第一张）
    if len(metas) == 0:
        print("图库为空，无法测试")
        return
    
    test_meta = metas[0]
    test_path = test_meta.get("path")
    
    if not test_path or not os.path.exists(test_path):
        print(f"测试图片不存在: {test_path}")
        return
    
    print(f"\n使用测试图片: {test_path}")
    print(f"Caption: {test_meta.get('caption', '')}")
    
    pixel_values = resize_short_side(test_path, target_size=224)
    
    # 测试不同特征模式
    modes = ["cls", "patch_mean", "fused"]
    results = {}
    
    for mode in modes:
        print(f"\n{'='*60}")
        print(f"测试特征模式: {mode}")
        print(f"{'='*60}")
        
        vit = Dinov2Numpy(weights)
        query_feat = vit(pixel_values, feature_mode=mode)[0].astype(np.float32)
        
        # 计算相似度
        idx, sims = cosine_topk(query_feat, feats, k=10)
        
        # 检查查询图片本身是否在 Top-10
        query_idx_in_top10 = np.where(idx == 0)[0]
        if len(query_idx_in_top10) > 0:
            rank = query_idx_in_top10[0] + 1
            print(f"✓ 查询图片本身在 Top-10 的第 {rank} 位（相似度: {sims[query_idx_in_top10[0]]:.4f}）")
        else:
            print("✗ 查询图片本身不在 Top-10")
        
        # 显示 Top-5 结果
        print(f"\nTop-5 结果:")
        for i, (idx_val, sim) in enumerate(zip(idx[:5], sims[:5])):
            is_match = "[MATCH]" if idx_val == 0 else "[     ]"
            caption = metas[idx_val].get("caption", "")[:50]
            print(f"  {i+1}. {is_match} score={sim:.4f}, idx={idx_val}, caption={caption}")
        
        results[mode] = {
            "query_feat_norm": np.linalg.norm(query_feat),
            "top1_score": float(sims[0]),
            "top5_avg_score": float(sims[:5].mean()),
            "query_rank": int(query_idx_in_top10[0]) + 1 if len(query_idx_in_top10) > 0 else None
        }
    
    # 对比结果
    print(f"\n{'='*60}")
    print("对比结果")
    print(f"{'='*60}")
    print(f"{'模式':<15} {'Top-1分数':<12} {'Top-5平均':<12} {'查询排名':<10}")
    print("-" * 60)
    for mode, res in results.items():
        rank_str = str(res["query_rank"]) if res["query_rank"] else "N/A"
        print(f"{mode:<15} {res['top1_score']:<12.4f} {res['top5_avg_score']:<12.4f} {rank_str:<10}")


if __name__ == "__main__":
    test_feature_modes()
