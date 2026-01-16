# 🚀 快速重建图库指南

## 问题
重新构建图库需要重新下载和提取特征，速度较慢。

## 💡 解决方案

### 方案 1：快速测试模式（推荐）⭐⭐⭐⭐⭐

**只处理部分图片，快速验证改进效果，如果效果好再全量重建。**

```bash
# 只处理前 200 张图片进行快速测试
python build_gallery.py --num-images 200 --quick-test 200
```

**优点**：
- 速度快（几分钟内完成）
- 可以快速验证改进效果
- 如果效果好，再全量重建

**缺点**：
- 图库规模小，但足以测试效果

---

### 方案 2：增量更新（如果图片已下载）⭐⭐⭐⭐

**如果图片已经下载，只重新提取特征，跳过下载阶段。**

当前代码已经支持增量更新：
- 已下载的图片会跳过下载
- 只对需要处理的图片提取特征

```bash
# 如果图片已下载，直接运行（会自动跳过已下载的图片）
python build_gallery.py --num-images 3000
```

**优化**：可以手动删除旧的特征文件，保留图片文件：
```bash
# 只删除特征文件，保留图片
Remove-Item gallery\features.npy -ErrorAction SilentlyContinue
Remove-Item gallery\paths.json -ErrorAction SilentlyContinue

# 重新运行（会跳过已下载的图片，只提取特征）
python build_gallery.py --num-images 3000
```

---

### 方案 3：分批处理 ⭐⭐⭐

**分批处理，每次处理一部分，可以随时中断和继续。**

```bash
# 第一批：处理前 1000 张
python build_gallery.py --num-images 1000

# 第二批：处理 1000-2000 张（会自动跳过已处理的）
python build_gallery.py --num-images 2000

# 第三批：处理 2000-3000 张
python build_gallery.py --num-images 3000
```

**优点**：
- 可以随时中断
- 可以分多次完成
- 已处理的图片会自动跳过

---

### 方案 4：使用旧特征（临时方案）⭐⭐

**如果不想重建，可以暂时使用旧特征，但搜索效果不会提升。**

**注意**：这不是推荐方案，因为：
- 旧特征使用 `cls` 模式，新代码使用 `fused` 模式
- 特征不匹配会导致搜索效果变差

**如果必须使用**：
1. 暂时回退 `server.py` 和 `search_gallery.py` 中的 `feature_mode="fused"` 改为 `feature_mode="cls"`
2. 但这样改进效果就没了

---

## 🎯 推荐流程

### 第一步：快速测试（5-10分钟）

```bash
# 只处理 200 张图片
python build_gallery.py --num-images 200 --quick-test 200

# 测试搜索效果
uvicorn server:app --reload
# 在网页上测试搜索，看看效果是否提升
```

### 第二步：如果效果好，全量重建

```bash
# 删除旧特征
Remove-Item gallery\features.npy -ErrorAction SilentlyContinue
Remove-Item gallery\paths.json -ErrorAction SilentlyContinue

# 全量重建（如果图片已下载，会跳过下载，只提取特征）
python build_gallery.py --num-images 3000
```

### 第三步：如果图片未下载，分批处理

```bash
# 第一批
python build_gallery.py --num-images 1000

# 第二批（会自动跳过已处理的）
python build_gallery.py --num-images 2000

# 第三批
python build_gallery.py --num-images 3000
```

---

## ⚡ 速度优化建议

### 1. 如果图片已下载
- 删除特征文件，保留图片文件
- 重新运行会自动跳过下载，只提取特征
- **速度提升：10-20倍**（下载是最慢的）

### 2. 使用快速测试模式
- 只处理部分图片
- **速度提升：15-20倍**（处理 200 张 vs 3000 张）

### 3. 分批处理
- 可以随时中断和继续
- 已处理的会自动跳过

---

## 📊 时间估算

假设：
- 下载速度：2-5 张/秒
- 特征提取速度：1-2 张/秒（单进程）

### 全量重建（3000 张）：
- 下载：15-25 分钟
- 特征提取：25-50 分钟
- **总计：40-75 分钟**

### 快速测试（200 张）：
- 下载：1-2 分钟
- 特征提取：2-3 分钟
- **总计：3-5 分钟**

### 只提取特征（图片已下载，3000 张）：
- 特征提取：25-50 分钟
- **总计：25-50 分钟**

---

## ✅ 推荐方案总结

**最佳实践**：
1. 先用快速测试模式验证效果（5分钟）
2. 如果效果好，删除特征文件，保留图片
3. 重新运行，只提取特征（30-50分钟）

**最快方案**：
- 快速测试模式：只处理 200 张（5分钟）

**最省事方案**：
- 分批处理：每次处理一部分，可以随时中断
