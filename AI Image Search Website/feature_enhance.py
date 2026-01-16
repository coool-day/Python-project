"""特征增强模块：提供多种特征提取和相似度计算策略。"""
import numpy as np
from typing import Optional, Tuple, List


def extract_patch_mean_feature(model_output: np.ndarray) -> np.ndarray:
    """提取所有 patch tokens 的平均特征（排除 CLS token）。
    
    参数:
        model_output: (B, N+1, D)，其中 N+1 是序列长度（1 个 CLS + N 个 patch）
    
    返回:
        (B, D) 平均特征
    """
    # model_output[:, 1:] 是除 CLS 外的所有 patch tokens
    return model_output[:, 1:].mean(axis=1)


def extract_cls_feature(model_output: np.ndarray) -> np.ndarray:
    """提取 CLS token 特征（当前默认方式）。
    
    参数:
        model_output: (B, N+1, D)
    
    返回:
        (B, D) CLS 特征
    """
    return model_output[:, 0]


def extract_fused_feature(model_output: np.ndarray, cls_weight: float = 0.5) -> np.ndarray:
    """融合 CLS token 和 patch tokens 的平均特征。
    
    参数:
        model_output: (B, N+1, D)
        cls_weight: CLS token 的权重（0-1），默认 0.5
    
    返回:
        (B, D) 融合特征
    """
    cls_feat = model_output[:, 0]  # (B, D)
    patch_feat = model_output[:, 1:].mean(axis=1)  # (B, D)
    fused = cls_weight * cls_feat + (1 - cls_weight) * patch_feat
    return fused


def cosine_similarity_weighted(
    query: np.ndarray,
    feats: np.ndarray,
    weights: Optional[np.ndarray] = None
) -> np.ndarray:
    """加权余弦相似度。
    
    参数:
        query: (D,) 查询特征
        feats: (N, D) 图库特征
        weights: (D,) 维度权重，如果为 None 则使用均匀权重
    
    返回:
        (N,) 相似度分数
    """
    if weights is None:
        weights = np.ones(query.shape[0], dtype=np.float32)
    
    # 归一化
    q_norm = query / (np.linalg.norm(query) + 1e-12)
    f_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
    
    # 加权内积
    weighted_q = q_norm * weights
    weighted_f = f_norm * weights[None, :]
    
    sims = (weighted_f @ weighted_q) / (np.linalg.norm(weighted_q) + 1e-12)
    return sims


def euclidean_similarity(
    query: np.ndarray,
    feats: np.ndarray,
    normalize: bool = True
) -> np.ndarray:
    """欧氏距离相似度（距离越小，相似度越高）。
    
    参数:
        query: (D,) 查询特征
        feats: (N, D) 图库特征
        normalize: 是否先归一化特征
    
    返回:
        (N,) 相似度分数（已转换为相似度，值越大越相似）
    """
    if normalize:
        q = query / (np.linalg.norm(query) + 1e-12)
        f = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
    else:
        q, f = query, feats
    
    # 计算欧氏距离
    dists = np.linalg.norm(f - q[None, :], axis=1)
    
    # 转换为相似度（距离越小，相似度越高）
    # 使用负指数或倒数
    sims = 1.0 / (1.0 + dists)
    return sims


def hybrid_similarity(
    query: np.ndarray,
    feats: np.ndarray,
    cosine_weight: float = 0.7
) -> np.ndarray:
    """混合相似度：余弦相似度 + 欧氏距离。
    
    参数:
        query: (D,) 查询特征
        feats: (N, D) 图库特征
        cosine_weight: 余弦相似度的权重（0-1）
    
    返回:
        (N,) 混合相似度分数
    """
    # 归一化
    q_norm = query / (np.linalg.norm(query) + 1e-12)
    f_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
    
    # 余弦相似度
    cosine_sims = f_norm @ q_norm
    
    # 欧氏距离相似度
    euclidean_sims = euclidean_similarity(q_norm, f_norm, normalize=False)
    
    # 归一化到相同范围
    cosine_sims = (cosine_sims + 1) / 2  # [-1, 1] -> [0, 1]
    
    # 混合
    hybrid = cosine_weight * cosine_sims + (1 - cosine_weight) * euclidean_sims
    return hybrid


def query_augmentation_single(
    extract_func,
    pixel_values: np.ndarray,
    scales: List[float] = [0.9, 1.0, 1.1]
) -> np.ndarray:
    """对单张图片做多尺度查询增强（需要模型支持不同分辨率输入）。
    
    注意：这个函数需要模型能够处理不同分辨率的输入。
    当前实现是简化版本，实际使用时需要修改预处理函数。
    
    参数:
        extract_func: 特征提取函数，接受 pixel_values 返回特征
        pixel_values: (1, C, H, W) 原始图片
        scales: 缩放比例列表
    
    返回:
        (D,) 增强后的特征（多个尺度的平均）
    """
    # 注意：这里需要修改预处理函数支持多尺度
    # 当前只是示例，实际使用时需要实现多尺度预处理
    feats = []
    for scale in scales:
        # 这里需要根据 scale 调整 pixel_values
        # 简化版本：直接使用原始特征
        feat = extract_func(pixel_values)
        feats.append(feat[0])  # (D,)
    
    # 平均融合
    return np.mean(feats, axis=0)


def rerank_topk(
    query: np.ndarray,
    feats: np.ndarray,
    topk_coarse: int = 100,
    topk_final: int = 10,
    coarse_sim_func=None,
    fine_sim_func=None
) -> Tuple[np.ndarray, np.ndarray]:
    """两阶段检索：粗检索 + 精细重排序。
    
    参数:
        query: (D,) 查询特征
        feats: (N, D) 图库特征
        topk_coarse: 粗检索返回的候选数量
        topk_final: 最终返回的数量
        coarse_sim_func: 粗检索相似度函数（默认余弦相似度）
        fine_sim_func: 精细检索相似度函数（默认混合相似度）
    
    返回:
        (indices, similarities) Top-K 索引和相似度
    """
    if coarse_sim_func is None:
        # 默认粗检索：快速余弦相似度
        q_norm = query / (np.linalg.norm(query) + 1e-12)
        f_norm = feats / (np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12)
        coarse_sims = f_norm @ q_norm
    else:
        coarse_sims = coarse_sim_func(query, feats)
    
    # 粗检索 Top-K
    coarse_idx = np.argsort(-coarse_sims)[:topk_coarse]
    coarse_feats = feats[coarse_idx]
    
    # 精细检索（使用更复杂的相似度函数）
    if fine_sim_func is None:
        fine_sims = hybrid_similarity(query, coarse_feats)
    else:
        fine_sims = fine_sim_func(query, coarse_feats)
    
    # 获取最终 Top-K
    fine_idx_in_coarse = np.argsort(-fine_sims)[:topk_final]
    final_idx = coarse_idx[fine_idx_in_coarse]
    final_sims = fine_sims[fine_idx_in_coarse]
    
    return final_idx, final_sims
