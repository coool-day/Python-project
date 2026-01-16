# 快速开始：提高搜索准确率

## 方法概览

我已经为你实现了多种提高搜索准确率的方法。以下是**推荐的使用顺序**：

## 🚀 方法 1：特征池化策略改进（最简单，推荐先试）

### 说明
当前使用 CLS token，可以改为：
- **patch_mean**：使用所有 patch tokens 的平均（可能保留更多细节）
- **fused**：融合 CLS 和 patch mean（平衡全局和局部信息）

### 使用方法

1. **修改 `build_gallery.py`**（第 386 行附近）：
   ```python
   # 原来：
   feat = vit(pixel_values)[0].astype(np.float32)
   
   # 改为（推荐 fused）：
   feat = vit(pixel_values, feature_mode="fused")[0].astype(np.float32)
   ```

2. **修改 `server.py` 和 `search_gallery.py`**（特征提取的地方）：
   ```python
   # 原来：
   feat = VIT(pixel_values)[0].astype(np.float32)
   
   # 改为：
   feat = VIT(pixel_values, feature_mode="fused")[0].astype(np.float32)
   ```

3. **重新构建图库**：
   ```bash
   python build_gallery.py --num-images 3000
   ```

4. **测试效果**：
   ```bash
   python test_feature_modes.py
   ```

### 预期效果
- **patch_mean**：可能提升 3-7% 准确率
- **fused**：可能提升 5-10% 准确率（推荐）

---

## 🔄 方法 2：混合相似度（无需重建图库）

### 说明
使用余弦相似度 + 欧氏距离的混合，可能更鲁棒。

### 使用方法

1. **修改 `search_gallery.py`**：
   ```python
   from feature_enhance import hybrid_similarity
   
   def cosine_topk(query, feats, k=10):
       # ... 原有代码 ...
       
       # 在回退路径中，可以尝试混合相似度：
       # 原来：
       # sims = F @ q
       
       # 改为：
       sims = hybrid_similarity(q, F, cosine_weight=0.7)
   ```

2. **重启服务器测试**（无需重建图库）

### 预期效果
可能提升 2-5% 准确率

---

## 🎯 方法 3：重排序（Re-ranking）

### 说明
两阶段检索：先用快速方法找 Top-100，再用精细方法重排序。

### 使用方法

1. **修改 `search_gallery.py`**：
   ```python
   from feature_enhance import rerank_topk
   
   def cosine_topk(query, feats, k=10):
       # 使用重排序
       idx, sims = rerank_topk(
           query, feats,
           topk_coarse=100,
           topk_final=k
       )
       return idx, sims
   ```

2. **重启服务器测试**（无需重建图库）

### 预期效果
可能提升 5-15% 准确率（特别是 Top-10）

---

## 📊 测试和对比

运行测试脚本对比不同方法的效果：

```bash
python test_feature_modes.py
```

这会测试 `cls`、`patch_mean`、`fused` 三种模式，并显示：
- Top-1 相似度分数
- Top-5 平均相似度
- 查询图片本身的排名

---

## ⚠️ 注意事项

1. **特征版本管理**：
   - 修改特征提取方式（方法1）后，**必须重新构建图库**
   - 修改相似度计算（方法2、3）后，**无需重建图库**

2. **计算开销**：
   - `patch_mean` 和 `fused` 几乎无额外开销
   - `rerank_topk` 会增加一些计算时间（但通常可接受）

3. **效果验证**：
   - 建议先用测试脚本验证效果
   - 在实际搜索中测试用户体验

---

## 🎯 推荐配置

**最佳实践组合**：
1. 使用 `feature_mode="fused"`（方法1）
2. 使用 `hybrid_similarity`（方法2）
3. 可选：使用 `rerank_topk`（方法3）

**快速尝试**：
- 如果不想重建图库：先试方法2和方法3
- 如果愿意重建图库：直接试方法1（fused）+ 方法2

---

## 📚 更多方法

查看 `IMPROVE_SEARCH_ACCURACY_ADVANCED.md` 了解其他进阶方法：
- 查询增强（Query Augmentation）
- 多尺度特征提取
- PCA 降维
- 等等
