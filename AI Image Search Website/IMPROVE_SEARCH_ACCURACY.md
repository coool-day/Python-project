# 搜索准确率改进方案

## 问题诊断

根据诊断脚本的结果，发现以下问题：
- **随机样本间相似度均值只有 0.02**：说明大部分图片之间的相似度偏低
- **权重稳定化参数可能过严**：`max_norm=1.0` 可能裁剪得太厉害，导致特征质量下降

## 已实施的改进

### 1. 调整权重稳定化参数 ✅

**修改内容**：
- 将 `max_norm` 从 `1.0` 增加到 `2.0`
- 减少权重裁剪强度，保留更多原始特征信息

**修改的文件**：
- `build_gallery.py`: 更新 `STABILIZE_MAX_NORM = 2.0`
- `server.py`: 更新 `STABILIZE_MAX_NORM = 2.0`
- `search_gallery.py`: 更新 `STABILIZE_MAX_NORM = 2.0`
- `diagnose_features.py`: 更新 `STABILIZE_MAX_NORM = 2.0`

**特征版本更新**：
- 从 `v1-dinov2-base-resize224-stabilize-l8-max1.0` 
- 更新到 `v2-dinov2-base-resize224-stabilize-l8-max2.0`

## 重要：需要重新构建图库 ⚠️

**由于权重稳定化参数已改变，必须重新构建图库特征！**

### 重新构建步骤：

1. **备份现有图库**（可选，但推荐）：
   ```bash
   cd assignments
   cp -r gallery gallery_backup_v1
   ```

2. **删除旧的特征文件**：
   ```bash
   # Windows PowerShell
   Remove-Item gallery\features.npy
   Remove-Item gallery\paths.json
   ```

3. **重新构建图库**：
   ```bash
   python build_gallery.py --num-images 3000
   ```

4. **验证新特征**：
   ```bash
   python diagnose_features.py
   ```

5. **重启服务器**：
   ```bash
   uvicorn server:app --reload
   ```

## 预期改进效果

- **相似度分数提升**：相同类别的图片（如都是狗）的相似度应该从 0.2-0.3 提升到 0.4-0.6 或更高
- **Top-K 检索更准确**：查询图片本身应该能在 Top-3 中找到
- **特征质量改善**：特征向量保留更多原始信息，区分度更好

## 其他可能的改进方向

如果调整 `max_norm=2.0` 后效果仍不理想，可以尝试：

### 方案 A：进一步增大 max_norm
- 尝试 `max_norm=3.0` 或 `max_norm=5.0`
- 风险：可能导致数值不稳定（但概率较低）

### 方案 B：使用不同的权重稳定化策略
- 只裁剪异常大的行（例如只裁剪超过 3.0 的行）
- 使用更平滑的裁剪函数（如 soft clipping）

### 方案 C：特征后处理
- 对特征进行额外的归一化或标准化
- 使用特征选择或降维（但可能降低区分度）

### 方案 D：改进相似度计算
- 尝试其他相似度度量（如欧氏距离、曼哈顿距离）
- 使用加权余弦相似度

## 测试建议

1. **运行诊断脚本**：
   ```bash
   python diagnose_features.py
   ```
   检查：
   - 随机样本间相似度是否提升
   - 查询图片本身是否在 Top-3

2. **实际搜索测试**：
   - 上传一张狗的图片
   - 检查 Top-10 结果中是否大部分都是狗
   - 检查相似度分数是否提升（期望 >0.4）

3. **对比测试**：
   - 如果可能，对比使用 `max_norm=1.0` 和 `max_norm=2.0` 的搜索结果

## 注意事项

- **特征版本不兼容**：新构建的特征与旧特征不兼容，必须全部重新构建
- **构建时间**：重新构建 3000 张图片可能需要一些时间（取决于 CPU 性能）
- **存储空间**：确保有足够的磁盘空间存储新的特征文件
