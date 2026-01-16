# 🚀 网站运行指南

## 快速开始

### 1. 确保依赖已安装

```bash
cd assignments
pip install -r requirements.txt
```

**必需依赖**：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `numpy`, `scipy`, `Pillow` - 图像处理和数值计算
- `faiss-cpu` - 快速相似度搜索（可选，但推荐）
- `requests` - 图片下载（可选，但推荐）

### 2. 确保图库已构建

**如果还没有构建图库**：
```bash
python build_gallery.py --num-images 3000
```

**如果图库已存在**，可以跳过此步骤。

### 3. 启动服务器

```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

**参数说明**：
- `server:app` - `server.py` 文件中的 `app` 对象
- `--reload` - 代码修改后自动重启（开发模式）
- `--host 127.0.0.1` - 监听本地地址
- `--port 8000` - 端口号（默认 8000）

### 4. 访问网站

在浏览器中打开：
- **主页面**：http://127.0.0.1:8000
- **API 文档**：http://127.0.0.1:8000/docs

---

## 📋 完整步骤（从头开始）

### 步骤 1：安装依赖

```bash
# 进入项目目录
cd assignments

# 安装所有依赖
pip install -r requirements.txt
```

### 步骤 2：准备数据文件

确保以下文件存在：
- `data.csv` - 包含图片 URL 和描述
- `vit-dinov2-base.npz` - DINOv2 模型权重文件

### 步骤 3：构建图库（首次运行）

```bash
# 构建图库（处理 3000 张图片）
python build_gallery.py --num-images 3000

# 或者快速测试（只处理 200 张）
python build_gallery.py --num-images 200 --quick-test 200
```

**等待时间**：
- 快速测试（200张）：5-10 分钟
- 全量构建（3000张，图片已下载）：30-50 分钟
- 全量构建（3000张，需下载）：40-75 分钟

### 步骤 4：启动服务器

```bash
uvicorn server:app --reload
```

**成功启动后，终端会显示**：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
初始图库加载完成，共 XXXX 张图片
INFO:     Application startup complete.
```

### 步骤 5：使用网站

1. **打开浏览器**，访问 http://127.0.0.1:8000
2. **上传图片**：点击"选择文件"，选择一张或多张图片
3. **设置 TopK**：输入要返回的结果数量（默认 20）
4. **开始搜索**：点击"开始搜索"按钮
5. **查看结果**：浏览搜索结果，可以：
   - 点击图片跳转到原始链接
   - 点击"搜这张图"按钮进行新的搜索
   - 悬停图片查看预览
   - 使用分页浏览更多结果

---

## 🔧 常见问题

### 问题 1：端口被占用

**错误信息**：`Address already in use`

**解决方法**：
```bash
# 使用其他端口
uvicorn server:app --reload --port 8001

# 或者关闭占用 8000 端口的程序
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 问题 2：图库未构建

**错误信息**：`FileNotFoundError: features.npy`

**解决方法**：
```bash
python build_gallery.py --num-images 3000
```

### 问题 3：模块未找到

**错误信息**：`ModuleNotFoundError: No module named 'xxx'`

**解决方法**：
```bash
pip install -r requirements.txt
```

### 问题 4：模型文件不存在

**错误信息**：`FileNotFoundError: vit-dinov2-base.npz`

**解决方法**：
- 确保 `vit-dinov2-base.npz` 文件在 `assignments` 目录下
- 如果文件不存在，需要从作业包中获取

---

## 🎯 快速命令参考

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 构建图库（全量）
python build_gallery.py --num-images 3000

# 3. 构建图库（快速测试）
python build_gallery.py --num-images 200 --quick-test 200

# 4. 启动服务器
uvicorn server:app --reload

# 5. 启动服务器（指定端口）
uvicorn server:app --reload --port 8001

# 6. 启动服务器（生产模式，无自动重载）
uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## 📝 停止服务器

在运行服务器的终端中按：
- **Ctrl + C**（Windows/Linux/Mac）

---

## 🌐 访问地址

启动成功后，可以通过以下地址访问：

- **主页面**：http://127.0.0.1:8000
- **API 文档（Swagger）**：http://127.0.0.1:8000/docs
- **API 文档（ReDoc）**：http://127.0.0.1:8000/redoc

---

## 💡 提示

1. **开发模式**：使用 `--reload` 参数，代码修改后自动重启
2. **生产模式**：去掉 `--reload`，性能更好
3. **远程访问**：使用 `--host 0.0.0.0` 允许其他设备访问（注意安全）
4. **查看日志**：服务器日志会显示在终端中，包括请求信息和错误

---

## ✅ 验证运行状态

启动成功后，你应该看到：
- ✅ 终端显示 "Uvicorn running on http://127.0.0.1:8000"
- ✅ 终端显示 "初始图库加载完成，共 XXXX 张图片"
- ✅ 浏览器可以访问 http://127.0.0.1:8000
- ✅ 网页显示美观的界面（紫色渐变背景）

如果遇到问题，请检查：
1. 依赖是否已安装
2. 图库是否已构建
3. 端口是否被占用
4. 模型文件是否存在
