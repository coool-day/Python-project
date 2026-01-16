"""特征提取工作进程：用于多进程并行提取特征。"""
import os
import numpy as np
from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights


def extract_single_feature(args_tuple):
    """提取单张图片的特征（用于多进程）。
    
    参数:
        args_tuple: (img_path, base_dir, feature_mode, stabilize_max_norm)
    
    返回:
        (success: bool, feat: np.ndarray or None, error: str or None)
    """
    img_path, base_dir, feature_mode, stabilize_max_norm = args_tuple
    
    try:
        # 加载模型（每个进程独立加载，避免共享状态问题）
        weights_path = os.path.join(base_dir, "vit-dinov2-base.npz")
        weights = np.load(weights_path)
        weights = stabilize_weights(weights, layer_idx=8, max_norm=stabilize_max_norm)
        vit = Dinov2Numpy(weights)
        
        # 提取特征
        pixel_values = resize_short_side(img_path, target_size=224)
        feat = vit(pixel_values, feature_mode=feature_mode)
        feat = feat.astype(np.float32)
        
        return True, feat[0], None  # feat[0] 因为 batch_size=1
    except Exception as e:
        return False, None, repr(e)
