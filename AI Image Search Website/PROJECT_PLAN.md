# 以图搜图网站（DINOv2 NumPy版）项目梳理与计划

> 本文档由 Cursor 辅助生成，用于期末大作业项目的结构梳理、现状评估、待完善清单与推荐实现顺序。

## 1. 项目结构（当前）

项目根目录：`以图搜图网站/`

- `assignments/`
  - `dinov2_numpy.py`
    - **作用**：用 NumPy 实现 DINOv2 ViT 推理（patch embedding + transformer blocks + cls token 输出特征）。
    - **现状**：主体框架已搭好，但存在关键 ToDo：
      - `Embeddings.interpolate_pos_encoding` 未实现（输入尺寸变化时的位置编码插值）。
      - `MultiHeadAttention.__call__` 未实现（多头注意力）。
      - 另外：`SingleHeadAttention` 中引用了 `self.hidden_size` 但类里未定义（潜在 bug，不过目前代码未使用该类）。
  - `preprocess_image.py`
    - **作用**：图片预处理。
    - **现状**：
      - `center_crop` 已实现（用于 debug，固定裁剪到 224x224 并标准化）。
      - `resize_short_side` ToDo（用于真实检索场景：短边缩放到 224，并保证宽高为 patch_size=14 的倍数）。
  - `debug.py`
    - **作用**：加载权重 `vit-dinov2-base.npz`，对 demo 图片提取特征（cat/dog），用于验证实现正确性。
  - `data.csv`
    - **作用**：预计为爬取/下载图像的 URL 列表或元数据（用于构建图库 gallery）。
  - `demo_data/`
    - `cat.jpg`, `dog.jpg`
    - `cat_dog_feature.npy`（参考特征，用于数值对齐验证）
  - `vit-dinov2-base.npz`
    - **作用**：DINOv2 ViT 权重（NumPy 加载）。
  - `__MACOSX/`
    - **作用**：macOS 解压缩遗留目录，可忽略。

## 2. 项目现状（你现在拥有什么）

- **模型权重与推理框架已就绪**：`Dinov2Numpy` 结构完整。
- **具备可验证的最小闭环**：
  - `debug.py` + `demo_data/cat_dog_feature.npy` 提供了“对齐参考输出”的方式。
- **但还不是“网站/系统”**：目前只有离线脚本级别能力，缺少：
  - 图库构建（批量特征抽取与保存）
  - 检索（相似度计算、Top-K）
  - Web 后端 API
  - 前端上传与结果展示

## 3. 待完善部分（Todo List，按优先级）

### P0（必须先做：决定模型能否跑对）

- [x] `dinov2_numpy.py`: 实现 `MultiHeadAttention.__call__`
  - [x] 完成 Q/K/V 投影与 reshape 成多头
  - [x] 完成 attention 计算（缩放 + `softmax`）
  - [x] 完成多头合并与 `out_proj`

- [x] `dinov2_numpy.py`: 实现 `Embeddings.interpolate_pos_encoding`
  - [x] 根据输入 H/W 计算 patch 网格 `(h=H/14, w=W/14)`
  - [x] 对 `position_embeddings` 做 2D 插值以匹配 `(h, w)`
  - [x] 拼回 `cls_token` 的位置编码，使输出形状为 `(1, h*w+1, D)`

- [x] `preprocess_image.py`: 实现 `resize_short_side`
  - [x] 短边缩放到 `target_size`（默认 224）
  - [x] 输出宽高都对齐到 `patch_size=14` 的倍数

- [ ] Debug 验证
  - [ ] 运行 `python debug.py` 生成 `cat_feat/dog_feat`
  - [ ] 与 `demo_data/cat_dog_feature.npy` 对比，误差在小容忍范围内

### P1（完成“以图搜图”的核心功能）

- 图库构建（gallery）
  - 读取 `data.csv`，下载 1w+ 图片（建议并发+断点续传+失败重试）
  - 对每张图做 `resize_short_side` -> `Dinov2Numpy` -> 得到特征向量
  - 保存：
    - `features.npy`（N, D）
    - `paths.json` 或 `paths.txt`（图片路径/URL 与特征行号对齐）

- 检索（query）
  - 对用户上传图片提取特征 `q`
  - 与 gallery 特征矩阵 `F` 计算相似度：
    - cosine：`sim = (F @ q) / (||F|| * ||q||)`
    - 或 L2
  - 取 Top-10 返回对应图片

### P2（网站化：后端 API + 前端）

- 后端（推荐 FastAPI）
  - `POST /search`：上传图片 -> 返回 TopK 结果（图片 URL/路径 + 分数）
  - 静态文件服务：用于展示 gallery 图片

- 前端
  - 上传图片、展示检索结果（Top-10）

### P3（加分项/工程化）

- 特征抽取加速（批处理、向量化、可选 FAISS）
- 缓存与持久化（sqlite / lmdb）
- 更好的图片下载与清洗（去重、坏图过滤）
- UI 美化与交互（分页、预览、相似度条）

## 4. 推荐实现顺序（强烈建议按此推进）

1. **完成 `dinov2_numpy.py` 的两个 ToDo**（注意力 + 位置编码插值）
2. **完成 `resize_short_side`**
3. **跑通 debug 对齐**（与 `cat_dog_feature.npy` 对比）
4. **实现离线检索脚本**（先在本地 demo_data 或少量图片上跑通 TopK）
5. **实现 gallery 构建（批量下载+抽特征+保存）**
6. **接入 FastAPI 做成服务**
7. **做一个简单前端**（或先用后端模板页）

## 5. 当前已发现的风险点/坑

- **输入尺寸与位置编码**：DINOv2 的 position embedding 必须与 patch 数匹配，否则维度会对不上。
- **patch_size=14 的倍数约束**：预处理不做对会导致 `pixel2patches` assert 失败。
- **性能**：1w+ 图片逐张 NumPy 推理会很慢；可接受的做法是先满足作业要求，后续再优化。



② 用 Cursor 辅助你把“以图搜图网站”做完：实战工作流（提示词工程 + 选模型策略）
你这个项目非常适合用 Cursor 做“拆解-实现-验证”的闭环。我建议你按 P0(模型对齐) → P1(检索闭环) → P2(网站化) 来推进（我已经把这套顺序写进 assignments/PROJECT_PLAN.md 了）。
1) Cursor 的正确打开方式（针对你这个项目）
1.1 三种常用模式怎么用
Ask（问答/解释）
适用：读代码、理解 DINOv2 结构、解释某段实现、让它给你推导形状（shape）。
优点：不改代码，适合先“搞懂再动手”。
Edit（单文件/小范围改动）
适用：实现 resize_short_side、补 interpolate_pos_encoding、补 MultiHeadAttention 这种“明确位置、明确目标”的任务。
优点：改动可控、容易 review。
Agent（多步骤/跨文件任务）
适用：从“离线检索脚本”扩展到“FastAPI 服务 + 特征缓存 + 静态文件服务”的整合型工作。
注意：Agent 很强，但也更容易“动太多”。你要给清晰边界（只允许改哪些文件、不要加注释/不要乱建文件等）。
2) 提示词工程：你要怎么提问，AI 才会稳定产出可用代码
2.1 你每次提需求，最好包含这 5 件事
[目标] 我希望实现什么功能（例如：实现多头注意力，输出 shape 必须一致）
[位置] 具体文件 + 函数名（例如：assignments/dinov2_numpy.py 的 MultiHeadAttention.__call__）
[约束] 不能引入新依赖/必须 NumPy 实现/不能改接口/patch_size=14 等
[验收] 用什么验证（例如：跑 debug.py 与 cat_dog_feature.npy 误差 < 某阈值）
[边界] 不要改其它文件/不要重构/不要加注释（如果你在意这些）
2.2 直接可复用的提示词模板（建议你收藏）
模板 A：实现某个 ToDo（最常用）
你是资深 Python/ML 工程师。请在不改变函数签名的前提下，实现：文件：assignments/dinov2_numpy.py函数：MultiHeadAttention.__call__(self, x)约束：- 仅使用 numpy- 输入 x shape: (B, N, D)，输出 shape 必须是 (B, N, D)- num_heads = self.num_heads, head_dim = self.head_dim- 注意 softmax 轴、缩放因子、transpose 的维度必须正确验收：- 代码能被 debug.py 调用- 不要修改其它函数，不要添加注释
模板 B：让 AI 先推导 shape，避免写错
请先只做“形状推导”，不要写代码。给定 x: (B, N, D)，num_heads=12，head_dim=D/12。请写出 Q/K/V reshape、attention 矩阵、输出合并各步的 shape，以及 softmax 的 axis。
模板 C：锁定改动范围（防止 Agent 发散）
只允许修改以下文件：assignments/dinov2_numpy.py只允许修改以下函数：Embeddings.interpolate_pos_encoding不要新建文件，不要改其它任何代码。实现位置编码插值以支持可变分辨率输入。
3) “选合适的编程 AI / 模式”的策略（什么时候用谁）
3.1 你的任务类型 → 推荐模式
[读代码/理解原理]
用：Ask
提问方式：让它解释、画数据流、列 shape、指出潜在 bug
[单点实现/补 ToDo]
用：Edit
原因：你要的是“精确落点”，不是大改
[跨文件做检索闭环/做网站]
用：Agent（但要强约束）
原因：涉及新 API、缓存、数据流串联，Agent 能自动串起来
3.2 你这个项目的关键阶段选择
P0（对齐参考特征）：强烈建议 Edit 为主
因为 MultiHeadAttention / pos_embed 一旦写错就会全盘错，改动必须可控。
P1（离线检索脚本）：Edit + 少量 Agent
P2（FastAPI 网站化）：Agent 更合适（但把范围钉死）
4) 最关键的 Cursor 使用习惯：让产出“可控 + 可验收”
4.1 每次改完立刻让 AI 给你“验收命令/验收点”
例如你实现 MultiHeadAttention 后，下一句就问：
[验收] 跑 python assignments/debug.py 预期看到什么？怎么和 cat_dog_feature.npy 对比？阈值建议多少？
4.2 用“逐步提交”的方式减少返工
先让 AI 只推导 shape（不写代码）
再让 AI 写代码
再让 AI 帮你检查数值稳定性（softmax 减 max、缩放因子等）

## 6. 可继续完善的功能清单（建议）
- 图库增量与断点续跑：支持跳过已下载/已提取的图片，避免重复计算。
- 下载健壮性：增加失败重试、超时/尺寸过滤、坏图自动清理与日志聚合。
- 检索性能：引入 FAISS 或分块加载特征，支持大规模图库的快速 Top-K。
- 特征管理：提供特征缓存/版本号与校验，支持不同模型或裁剪策略的多版本特征。
- 前端体验：结果分页、相似度条、悬停预览、批量上传与最近搜索列表。
- 调试对齐：完善逐层对比入口，尝试更精细的权重裁剪或数值稳定策略以逼近参考输出。
