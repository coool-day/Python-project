from transformers import AutoImageProcessor, AutoModel

print("开始下载 DINOv2 模型...")
AutoImageProcessor.from_pretrained("facebook/dinov2-base")
AutoModel.from_pretrained("facebook/dinov2-base")
print("模型下载完成并已缓存。")