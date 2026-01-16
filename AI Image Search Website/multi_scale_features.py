"""多尺度特征提取：提升搜索准确率的最有效方法之一。"""
import numpy as np
from typing import List
from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side


def extract_multi_scale_features(
    vit: Dinov2Numpy,
    img_path: str,
    scales: List[int] = [224, 336, 448],
    feature_mode: str = "fused"
) -> np.ndarray:
    """提取多尺度特征并融合。
    
    参数:
        vit: DINOv2 模型实例
        img_path: 图片路径
        scales: 多个目标尺寸列表（短边）
        feature_mode: 特征提取模式（'cls', 'patch_mean', 'fused'）
    
    返回:
        (D,) 融合后的特征向量
    """
    feats = []
    
    for scale in scales:
        try:
            # 对每个尺度提取特征
            pixel_values = resize_short_side(img_path, target_size=scale)
            feat = vit(pixel_values, feature_mode=feature_mode)
            if len(feat.shape) > 1:
                feat = feat[0]  # (D,)
            feats.append(feat.astype(np.float32))
        except Exception as e:
            # 如果某个尺度失败，跳过
            print(f"警告：提取尺度 {scale} 的特征失败: {e}")
            continue
    
    if not feats:
        raise ValueError("所有尺度的特征提取都失败")
    
    # 归一化每个特征
    feats_norm = [f / (np.linalg.norm(f) + 1e-12) for f in feats]
    
    # 平均融合
    fused_feat = np.mean(feats_norm, axis=0)
    
    # 再次归一化
    fused_feat = fused_feat / (np.linalg.norm(fused_feat) + 1e-12)
    
    return fused_feat.astype(np.float32)


def extract_query_augmented_features(
    vit: Dinov2Numpy,
    pixel_values: np.ndarray,
    feature_mode: str = "fused"
) -> np.ndarray:
    """查询增强：对查询图片做数据增强，融合多个版本的特征。
    
    注意：当前简化版本，只使用原始特征。
    完整版本需要对 pixel_values 做数据增强（翻转、旋转、亮度调整等）。
    
    参数:
        vit: DINOv2 模型实例
        pixel_values: (1, C, H, W) 原始图片
        feature_mode: 特征提取模式
    
    返回:
        (D,) 增强后的特征向量
    """
    # 提取原始特征
    feat = vit(pixel_values, feature_mode=feature_mode)
    if len(feat.shape) > 1:
        feat = feat[0]  # (D,)
    
    # TODO: 未来可以添加：
    # 1. 水平翻转增强
    # 2. 轻微旋转增强
    # 3. 亮度调整增强
    # 4. 融合多个增强版本的特征
    
    return feat.astype(np.float32)
