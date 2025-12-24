# SSL 协议错误修复指南

## ✅ 服务器配置已正确

检查结果显示：
- `DEBUG: True` ✅
- `SECURE_SSL_REDIRECT: False` ✅

Django 服务器配置是正确的，SSL 重定向已被禁用。

## 🔍 问题原因

Edge 浏览器可能：
1. 缓存了之前的 HTTPS 重定向
2. 启用了 HSTS（HTTP Strict Transport Security）预加载
3. 自动将 HTTP 升级为 HTTPS

## 🛠️ 解决方案

### 方案 1：清除 Edge 浏览器的 HSTS 缓存（推荐）

1. 在 Edge 浏览器地址栏输入：`edge://net-internals/#hsts`
2. 在 "Delete domain security policies" 部分：
   - 输入：`127.0.0.1`
   - 点击 "Delete" 按钮
   - 输入：`localhost`
   - 点击 "Delete" 按钮
3. 清除浏览器缓存：
   - 按 `Ctrl + Shift + Delete`
   - 选择"所有时间"
   - 勾选"缓存的图像和文件"
   - 点击"立即清除"

### 方案 2：使用 localhost 而不是 127.0.0.1

访问：`http://localhost:8000`（而不是 `http://127.0.0.1:8000`）

### 方案 3：使用隐私模式

1. 按 `Ctrl + Shift + N` 打开隐私窗口
2. 访问：`http://127.0.0.1:8000`

### 方案 4：重置 Edge 浏览器设置

如果以上方法都不行：
1. 打开 Edge 设置
2. 重置浏览器设置
3. 清除所有浏览数据

### 方案 5：使用其他浏览器测试

- Chrome: `http://127.0.0.1:8000`
- Firefox: `http://127.0.0.1:8000`

## 📝 验证步骤

1. 确保 Django 服务器正在运行：
   ```bash
   python manage.py runserver
   ```

2. 在浏览器中访问：
   - ✅ `http://127.0.0.1:8000`（使用 HTTP，不是 HTTPS）
   - ✅ `http://localhost:8000`（备选）

3. 如果仍然看到 SSL 错误：
   - 检查浏览器地址栏是否显示 `https://`
   - 如果是，手动改为 `http://`
   - 清除浏览器缓存后重试

## ⚠️ 注意事项

- **不要使用 HTTPS**：开发服务器只支持 HTTP
- **确保使用 http://**：不是 https://
- **清除浏览器缓存**：这很重要！

## 🔧 如果问题仍然存在

运行检查脚本验证设置：
```bash
python check_settings.py
```

应该看到：
```
DEBUG: True
SECURE_SSL_REDIRECT: False
```

如果设置正确但仍有问题，请尝试：
1. 重启 Django 开发服务器
2. 使用不同的端口：`python manage.py runserver 8001`
3. 访问：`http://127.0.0.1:8001`

