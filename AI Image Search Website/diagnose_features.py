"""诊断特征质量和相似度分布，帮助定位搜索准确率低的问题。"""
import os
import numpy as np
from search_gallery import load_gallery
from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights


def diagnose_features():
    """诊断图库特征的质量和分布。"""
    base_dir = os.path.dirname(__file__)
    gallery_dir = os.path.join(base_dir, "gallery")
    
    print("=" * 60)
    print("特征质量诊断")
    print("=" * 60)
    
    # 加载图库特征
    feats, metas = load_gallery(gallery_dir)
    print(f"\n图库规模: {len(metas)} 张图片")
    print(f"特征维度: {feats.shape[1]}")
    
    # 检查特征范数分布
    norms = np.linalg.norm(feats, axis=1)
    print(f"\n特征向量 L2 范数统计:")
    print(f"  均值: {norms.mean():.4f}")
    print(f"  标准差: {norms.std():.4f}")
    print(f"  最小值: {norms.min():.4f}")
    print(f"  最大值: {norms.max():.4f}")
    print(f"  中位数: {np.median(norms):.4f}")
    
    # 检查归一化后的特征
    feats_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
    norms_norm = np.linalg.norm(feats_norm, axis=1)
    print(f"\n归一化后特征向量 L2 范数统计:")
    print(f"  均值: {norms_norm.mean():.6f}")
    print(f"  标准差: {norms_norm.std():.6f}")
    print(f"  最小值: {norms_norm.min():.6f}")
    print(f"  最大值: {norms_norm.max():.6f}")
    
    # 检查特征值的分布
    print(f"\n特征值统计（原始特征）:")
    print(f"  均值: {feats.mean():.6f}")
    print(f"  标准差: {feats.std():.6f}")
    print(f"  最小值: {feats.min():.6f}")
    print(f"  最大值: {feats.max():.6f}")
    
    # 检查特征之间的相似度分布（随机采样）
    if len(feats) > 100:
        sample_size = min(1000, len(feats))
        indices = np.random.choice(len(feats), sample_size, replace=False)
        sample_feats = feats_norm[indices]
        
        # 计算随机样本之间的相似度
        sims = sample_feats @ sample_feats.T
        # 去掉对角线（自己与自己的相似度）
        mask = ~np.eye(sample_size, dtype=bool)
        sims_off_diag = sims[mask]
        
        print(f"\n随机样本间相似度分布（采样 {sample_size} 张）:")
        print(f"  均值: {sims_off_diag.mean():.4f}")
        print(f"  标准差: {sims_off_diag.std():.4f}")
        print(f"  最小值: {sims_off_diag.min():.4f}")
        print(f"  最大值: {sims_off_diag.max():.4f}")
        print(f"  中位数: {np.median(sims_off_diag):.4f}")
    
    # 测试查询特征提取
    print(f"\n" + "=" * 60)
    print("测试查询特征提取")
    print("=" * 60)
    
    # 尝试从图库中随机选一张图片作为查询
    if len(metas) > 0:
        test_idx = 0
        test_meta = metas[test_idx]
        test_path = test_meta.get("path")
        
        if test_path and os.path.exists(test_path):
            print(f"\n使用图库中的图片作为查询: {test_path}")
            
            # 加载模型（与 server.py 一致）
            STABILIZE_MAX_NORM = 2.0  # 与 build_gallery.py 和 server.py 保持一致
            weights = np.load(os.path.join(base_dir, "vit-dinov2-base.npz"))
            weights = stabilize_weights(weights, layer_idx=8, max_norm=STABILIZE_MAX_NORM)
            vit = Dinov2Numpy(weights)
            
            pixel_values = resize_short_side(test_path, target_size=224)
            query_feat = vit(pixel_values)[0].astype(np.float32)
            
            print(f"查询特征 L2 范数: {np.linalg.norm(query_feat):.4f}")
            
            # 计算与图库的相似度
            query_norm = query_feat / (np.linalg.norm(query_feat) + 1e-12)
            feats_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
            sims = feats_norm @ query_norm
            
            top10_idx = np.argsort(-sims)[:10]
            top10_sims = sims[top10_idx]
            
            print(f"\nTop-10 相似度:")
            for i, (idx, sim) in enumerate(zip(top10_idx, top10_sims)):
                is_match = "[MATCH]" if idx == test_idx else "[     ]"
                print(f"  {i+1}. {is_match} score={sim:.4f}, idx={idx}")
            
            print(f"\n预期: idx={test_idx} 应该是最高分（或接近最高分）")
            if test_idx not in top10_idx[:3]:
                print("[WARNING] 查询图片本身不在 Top-3，可能存在特征提取不一致的问题！")
        else:
            print(f"⚠️  无法找到测试图片: {test_path}")
    else:
        print("⚠️  图库为空，无法进行测试")


if __name__ == "__main__":
    diagnose_features()
