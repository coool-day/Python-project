"""搜索增强功能：查询增强和重排序。"""
import numpy as np
from typing import Tuple


def query_augmentation(
    extract_func,
    pixel_values: np.ndarray,
    scales: list = [0.95, 1.0, 1.05]
) -> np.ndarray:
    """查询增强：对查询图片做多尺度处理，融合多个特征。
    
    参数:
        extract_func: 特征提取函数，接受 pixel_values 返回特征
        pixel_values: (1, C, H, W) 原始图片
        scales: 缩放比例列表
    
    返回:
        (D,) 增强后的特征（多个尺度的平均）
    """
    # 注意：这里简化实现，实际使用时需要修改预处理函数支持多尺度
    # 当前版本：直接使用原始特征（因为 resize_short_side 已经处理了尺寸）
    # 未来可以扩展为真正的多尺度提取
    
    # 提取原始特征
    feat = extract_func(pixel_values)
    if len(feat.shape) > 1:
        feat = feat[0]  # (D,)
    
    # 简化版本：返回原始特征
    # 完整版本需要：
    # 1. 对每个 scale，调整 pixel_values 的尺寸
    # 2. 提取特征
    # 3. 平均融合
    return feat


def rerank_topk_enhanced(
    query: np.ndarray,
    feats: np.ndarray,
    topk_coarse: int = 100,
    topk_final: int = 10,
    use_hybrid: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """两阶段检索：粗检索 + 精细重排序。
    
    参数:
        query: (D,) 查询特征
        feats: (N, D) 图库特征
        topk_coarse: 粗检索返回的候选数量
        topk_final: 最终返回的数量
        use_hybrid: 是否在重排序时使用混合相似度
    
    返回:
        (indices, similarities) Top-K 索引和相似度
    """
    # 归一化
    q_norm = query / (np.linalg.norm(query) + 1e-12)
    f_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
    
    # 第一阶段：快速粗检索（余弦相似度）
    coarse_sims = f_norm @ q_norm
    coarse_idx = np.argsort(-coarse_sims)[:topk_coarse]
    coarse_feats = f_norm[coarse_idx]
    
    # 第二阶段：精细重排序
    if use_hybrid:
        # 使用混合相似度（余弦 + 欧氏距离）
        cosine_sims = coarse_feats @ q_norm
        euclidean_dists = np.linalg.norm(coarse_feats - q_norm[None, :], axis=1)
        euclidean_sims = 1.0 / (1.0 + euclidean_dists)
        
        # 归一化到相同范围
        cosine_sims_norm = (cosine_sims + 1) / 2  # [-1, 1] -> [0, 1]
        euclidean_sims_norm = euclidean_sims  # 已经是 [0, 1]
        
        # 混合（70% 余弦，30% 欧氏）
        fine_sims = 0.7 * cosine_sims_norm + 0.3 * euclidean_sims_norm
    else:
        # 只使用余弦相似度
        fine_sims = coarse_feats @ q_norm
    
    # 获取最终 Top-K
    fine_idx_in_coarse = np.argsort(-fine_sims)[:topk_final]
    final_idx = coarse_idx[fine_idx_in_coarse]
    final_sims = fine_sims[fine_idx_in_coarse]
    
    return final_idx, final_sims
