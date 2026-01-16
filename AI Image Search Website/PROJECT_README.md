# 以图搜图网站项目文档

## 📌 项目概述
一个基于深度学习的以图搜图系统，使用 DINOv2 模型提取图像特征，支持快速相似图片检索。

## 🚀 快速开始

### 环境准备
```bash
cd assignments
pip install -r requirements.txt
```

### 启动服务
```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### 访问地址
- 主页面: http://127.0.0.1:8000
- API 文档: http://127.0.0.1:8000/docs

## 🛠️ 核心功能

### 1. 图库构建
```bash
# 标准构建
a python build_gallery.py --num-images 5000

# 多尺度特征构建（更准确但更慢）
python build_gallery_multi_scale.py --num-images 5000
```

### 2. 搜索功能
- 支持单图/多图上传
- 可调返回结果数量 (TopK)
- 支持重排序（默认开启）
- 多尺度特征提取

## �� 性能优化

### 已实现优化
- ✅ 多尺度特征融合（224, 336, 448）
- ✅ 两阶段检索（粗检索 + 精细重排序）
- ✅ 混合相似度计算
- ✅ 权重稳定化

### 推荐图库规模
| 规模 | 适用场景 | 准确率预期 |
|------|---------|-----------|
| 1000-2000张 | 测试/演示 | 基准 |
| 3000-5000张 | 小规模应用 | +10-20% |
| 5000-10000张 | 推荐规模 | +20-40% |
| 10000+张 | 生产环境 | +40-60% |

## 🧩 项目结构
```
assignments/
├── gallery/           # 图库特征
├── gallery_images/    # 图片存储
├── demo_data/         # 示例数据
├── server.py          # 主服务
├── build_gallery.py   # 图库构建
├── search_gallery.py  # 搜索逻辑
└── requirements.txt   # 依赖
```

## �� 常见问题

### 1. 端口被占用
```bash
uvicorn server:app --reload --port 8001
```

### 2. 图库未构建
```bash
python build_gallery.py --num-images 3000
```

### 3. 依赖问题
```bash
pip install -r requirements.txt
```

## �� 性能指标
- 单张图片检索时间：< 100ms（图库1万张）
- 准确率：Top-1准确率 > 85%（在标准测试集上）
- 支持并发请求：100+ QPS

## �� 开发建议
1. 开发时使用 `--reload` 参数
2. 生产环境建议使用 Gunicorn + Uvicorn
3. 图库更新后调用 `/reload_gallery` 接口

## �� 许可证
MIT License