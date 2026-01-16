import numpy as np
from PIL import Image


def center_crop(img_path, crop_size=224):
    """读取图片并从中心裁剪到固定大小，然后做标准化。

    主要用于 debug：确保输入固定为 224x224，从而与参考特征对齐。

    参数:
        img_path: 图片路径
        crop_size: 裁剪后的边长（默认 224）

    返回:
        pixel_values: (1, 3, crop_size, crop_size)
    """
    # Step 1: load image
    image = Image.open(img_path).convert("RGB")

    # Step 2: center crop
    w, h = image.size
    left = (w - crop_size) // 2
    top = (h - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    image = image.crop((left, top, right, bottom))  # PIL Image, size (224, 224)

    # Step 3: to_numpy
    image = np.array(image).astype(np.float32) / 255.0  # (H, W, C)

    # Step 4: norm
    mean = np.array([0.485, 0.456, 0.406])
    std  = np.array([0.229, 0.224, 0.225])
    image = (image - mean) / std  # (H, W, C)
    image = image.transpose(2, 0, 1) # (C, H, W)
    return image[None] # (1, C, H, W)

# ************* ToDo, resize short side *************
def resize_short_side(img_path, target_size=224):
    """按短边缩放图片到 target_size，并保证输出分辨率适配 ViT patch。

    目标:
        - 短边缩放到 target_size（默认 224）
        - 宽高都对齐到 patch_size=14 的倍数（否则后续切 patch 会失败）

    参数:
        img_path: 图片路径
        target_size: 短边目标长度

    返回:
        pixel_values: (1, 3, H, W)，其中 H/W 都是 14 的倍数
    """
    # Step 1: load image
    image = Image.open(img_path).convert("RGB")

    # Step 2: resize so that the shorter side == target_size
    # and more, ensure both sides are multiples of patch size, e.g., 14
    w, h = image.size
    if w <= h:
        new_w = target_size
        new_h = int(round(h * (target_size / w)))
    else:
        new_h = target_size
        new_w = int(round(w * (target_size / h)))

    patch_size = 14
    new_w = max(patch_size, int(round(new_w / patch_size)) * patch_size)
    new_h = max(patch_size, int(round(new_h / patch_size)) * patch_size)

    image = image.resize((new_w, new_h), resample=Image.BICUBIC)

    # Step 3: to_numpy
    image = np.array(image).astype(np.float32) / 255.0  # (H, W, C)

    # Step 4: norm
    mean = np.array([0.485, 0.456, 0.406])
    std  = np.array([0.229, 0.224, 0.225])
    image = (image - mean) / std  # (H, W, C)
    image = image.transpose(2, 0, 1) # (C, H, W)
    return image[None] # (1, C, H, W)