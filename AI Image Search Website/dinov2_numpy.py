import numpy as np

from scipy.ndimage import zoom


def gelu(x):
    """GELU 激活函数（Transformer 中常用）。

    参数:
        x: np.ndarray

    返回:
        与 x 同形状的 np.ndarray
    """
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))))


class Embeddings:
    """DINOv2 的 Embeddings 部分（纯 NumPy 推理）。

    主要职责：
    - 将输入图片 `pixel_values` 切成 patch 并线性投影到 hidden_size 维
    - 在序列首部拼接 `cls_token`
    - 加上可学习的位置编码（支持输入分辨率变化时的插值）

    约定:
    - 输入 `pixel_values` shape: (B, C, H, W)
    - patch_size = 14，因此要求 H、W 都是 14 的倍数
    - 输出 embeddings shape: (B, 1 + h*w, D)
      其中 h=H/14, w=W/14, D=768
    """

    def __init__(self, weights):
        """从 npz 权重中初始化 Embeddings 所需参数。"""
        self.hidden_size = 768  # D
        self.patch_size = 14  # ps

        self.cls_token = weights["embeddings.cls_token"]  # (1, 1, D)
        self.position_embeddings = weights["embeddings.position_embeddings"]  # (1, N+1, D)
        self.patch_embed_w = weights["embeddings.patch_embeddings.projection.weight"].reshape(768, -1).T
        self.patch_embed_b = weights["embeddings.patch_embeddings.projection.bias"].reshape(768, 1).T

    def pixel2patches(self, pixel_values): 
        """将图片像素按 patch_size 切分并展平。

        参数:
            pixel_values: (B, C, H, W)

        返回:
            patches: (B, h*w, C*patch_size*patch_size)
        """
        B, C, H, W = pixel_values.shape
        assert H % self.patch_size == 0 and W % self.patch_size == 0

        patches = []
        for i in range(0, H, self.patch_size):
            for j in range(0, W, self.patch_size):
                patch = pixel_values[:, :, i : i + self.patch_size, j : j + self.patch_size].reshape(B, -1)
                patches.append(patch)

        patches = np.stack(patches, axis=1)
        return patches

    def interpolate_pos_encoding(self, embeddings, height, width):
        """对位置编码做 2D 插值，以支持可变分辨率输入。

        DINOv2 的 position embedding 预训练时通常对应固定网格（例如 16x16）。
        当输入图片分辨率变化时，patch 网格 (h0, w0) 也会变化，需要将
        `position_embeddings` 的 patch 部分插值到新的网格尺寸。

        参数:
            embeddings: (B, 1 + h0*w0, D) —— 仅用于提供目标序列长度语义（此处不直接用它插值）
            height/width: 输入图片 H/W（像素），要求为 patch_size 的倍数

        返回:
            pos_embed: (1, 1 + h0*w0, D)，包含 cls 位置编码 + 插值后的 patch 位置编码
        """
        patch_size = self.patch_size
        h0 = height // patch_size
        w0 = width // patch_size

        pos_embed = self.position_embeddings
        cls_pos = pos_embed[:, :1, :]
        patch_pos = pos_embed[:, 1:, :]

        N = patch_pos.shape[1]
        D = patch_pos.shape[2]
        s = int(np.sqrt(N))
        if s * s != N:
            raise ValueError(f"Unexpected number of position embeddings: {N}")

        if h0 == s and w0 == s:
            return pos_embed

        patch_pos_2d = patch_pos.reshape(1, s, s, D).transpose(0, 3, 1, 2)
        zoom_factors = (1, 1, h0 / s, w0 / s)
        patch_pos_2d = zoom(patch_pos_2d, zoom_factors, order=1)
        patch_pos_new = patch_pos_2d.transpose(0, 2, 3, 1).reshape(1, h0 * w0, D)

        return np.concatenate([cls_pos, patch_pos_new], axis=1)

    def __call__(self, pixel_values):
        B, _, H, W = pixel_values.shape

        patch_values = self.pixel2patches(pixel_values)
        
        embeddings = patch_values @ self.patch_embed_w + self.patch_embed_b
        
        cls_token = np.tile(self.cls_token, (B, 1, 1))
        embeddings = np.concatenate([cls_token, embeddings], axis=1)

        pos_embed = self.interpolate_pos_encoding(embeddings, H, W)
        
        embeddings = embeddings + pos_embed
        return embeddings


class LayerNorm:
    """LayerNorm（最后一维做归一化）。

    参数:
        weight, bias: 可学习参数，shape 通常为 (D,)
        eps: 数值稳定项

    输入/输出:
        x: (..., D)
        return: (..., D)
    """

    def __init__(self, weight, bias, eps=1e-6):
        self.weight = weight
        self.bias = bias
        self.eps = eps

    def __call__(self, x):
        mean = x.mean(-1, keepdims=True)
        var = x.var(-1, keepdims=True)
        norm = (x - mean) / np.sqrt(var + self.eps)
        return norm * self.weight + self.bias


class LayerScale: 
    """LayerScale：对残差分支输出做按通道缩放。

    DINOv2 中每个 block 的 attention/mlp 输出会乘以一个可学习向量 lambda1。

    输入/输出:
        x: (..., D)
        return: (..., D)
    """

    def __init__(self, lambda1): 
        self.lambda1 = lambda1

    def __call__(self, x): 
        return x * self.lambda1


class Linear:
    """线性层：y = x @ W^T + b（与 PyTorch Linear 对齐）。

    约定:
        - x 最后一维为输入特征维
        - weight shape: (out_features, in_features)
        - bias shape: (out_features,)

    输入/输出:
        x: (..., in_features)
        return: (..., out_features)
    """

    def __init__(self, weight, bias):
        self.weight = weight
        self.bias = bias

    def __call__(self, x):
        return x @ self.weight.T + self.bias


class SingleHeadAttention:
    """单头自注意力（当前项目未使用，保留用于对照/教学）。

    输入/输出:
        x: (B, N, D)
        return: (B, N, D)

    注意:
        - DINOv2 实际使用的是多头注意力（见 MultiHeadAttention）。
    """

    def __init__(self, config, prefix, weights):
        q_w = weights[f"{prefix}.attention.query.weight"]
        q_b = weights[f"{prefix}.attention.query.bias"]
        k_w = weights[f"{prefix}.attention.key.weight"]
        k_b = weights[f"{prefix}.attention.key.bias"]
        v_w = weights[f"{prefix}.attention.value.weight"]
        v_b = weights[f"{prefix}.attention.value.bias"]
        o_w = weights[f"{prefix}.output.dense.weight"]
        o_b = weights[f"{prefix}.output.dense.bias"]

        self.hidden_size = config["hidden_size"]

        self.q_proj = Linear(q_w, q_b)
        self.k_proj = Linear(k_w, k_b)
        self.v_proj = Linear(v_w, v_b)
        self.out_proj = Linear(o_w, o_b)

    def __call__(self, x):
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)

        att = np.matmul(q, k.transpose(0, 2, 1)) / np.sqrt(self.hidden_size)
        att = softmax(att, axis=-1)

        out = np.matmul(att, v)
        return self.out_proj(out)


class MultiHeadAttention:
    """多头自注意力（Multi-Head Self-Attention）。

    计算流程（与标准 Transformer 一致）:
    1) Q/K/V = Linear(x)
    2) reshape 为多头: (B, heads, N, head_dim)
    3) attention = softmax(QK^T / sqrt(head_dim))，softmax 的轴是最后一维（对每个 query 的所有 key 归一化）
    4) out = attention @ V
    5) 合并 heads 并做 out_proj

    输入/输出:
        x: (B, N, D)
        return: (B, N, D)

    易错点:
        - 缩放因子使用 sqrt(head_dim)，不是 sqrt(D)
        - softmax(axis=-1)
        - transpose 维度顺序要与 matmul 匹配
    """

    def __init__(self, config, prefix, weights):
        self.num_heads = config["num_heads"]
        self.head_dim = config["hidden_size"] // self.num_heads
        self.hidden_size = config["hidden_size"]

        q_w = weights[f"{prefix}.attention.query.weight"]
        q_b = weights[f"{prefix}.attention.query.bias"]
        k_w = weights[f"{prefix}.attention.key.weight"]
        k_b = weights[f"{prefix}.attention.key.bias"]
        v_w = weights[f"{prefix}.attention.value.weight"]
        v_b = weights[f"{prefix}.attention.value.bias"]
        o_w = weights[f"{prefix}.output.dense.weight"]
        o_b = weights[f"{prefix}.output.dense.bias"]

        self.q_proj = Linear(q_w, q_b)
        self.k_proj = Linear(k_w, k_b)
        self.v_proj = Linear(v_w, v_b)
        self.out_proj = Linear(o_w, o_b)

    def __call__(self, x):
        B, N, D = x.shape

        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)

        q = q.reshape(B, N, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        k = k.reshape(B, N, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        v = v.reshape(B, N, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)

        att = np.matmul(q, k.transpose(0, 1, 3, 2)) / np.sqrt(self.head_dim)
        att = softmax(att, axis=-1)

        out = np.matmul(att, v)
        out = out.transpose(0, 2, 1, 3).reshape(B, N, D)
        return self.out_proj(out)


class MLP:
    """Transformer block 中的前馈网络（两层 Linear + GELU）。

    输入/输出:
        x: (B, N, D)
        return: (B, N, D)
    """

    def __init__(self, prefix, weights):
        w1 = weights[f"{prefix}.mlp.fc1.weight"]
        b1 = weights[f"{prefix}.mlp.fc1.bias"]
        w2 = weights[f"{prefix}.mlp.fc2.weight"]
        b2 = weights[f"{prefix}.mlp.fc2.bias"]

        self.fc1 = Linear(w1, b1)
        self.fc2 = Linear(w2, b2)

    def __call__(self, x, debug=False):
        if debug:
            dumps = {}
            fc1_out = self.fc1(x)
            dumps["fc1_out"] = fc1_out

            gelu_out = gelu(fc1_out)
            dumps["gelu_out"] = gelu_out

            fc2_out = self.fc2(gelu_out)
            dumps["fc2_out"] = fc2_out
            return fc2_out, dumps

        return self.fc2(gelu(self.fc1(x)))


def softmax(x, axis=-1):
    """数值稳定的 softmax。

    参数:
        x: 任意形状 np.ndarray
        axis: 归一化维度

    返回:
        softmax(x) 与 x 同形状
    """
    x_max = np.max(x, axis=axis, keepdims=True)
    x_exp = np.exp(x - x_max)
    x_sum = np.sum(x_exp, axis=axis, keepdims=True)
    return x_exp / x_sum


class TransformerBlock:
    """DINOv2 的单个 Transformer 编码块。

    结构（Pre-LN 形式）:
        x = x + LayerScale(attn(LayerNorm(x)))
        x = x + LayerScale(mlp(LayerNorm(x)))

    输入/输出:
        x: (B, N, D)
        return: (B, N, D)
    """

    def __init__(self, config, idx, weights):
        prefix = f"encoder.layer.{idx}"
        
        self.norm1 = LayerNorm(weights[f"{prefix}.norm1.weight"], weights[f"{prefix}.norm1.bias"])
        self.scale1 = LayerScale(weights[f"{prefix}.layer_scale1.lambda1"])
        self.attn = MultiHeadAttention(config, f"{prefix}.attention", weights)

        self.norm2 = LayerNorm(weights[f"{prefix}.norm2.weight"], weights[f"{prefix}.norm2.bias"])
        self.scale2 = LayerScale(weights[f"{prefix}.layer_scale2.lambda1"])
        self.mlp = MLP(f"{prefix}", weights)

        self.idx = idx

    def forward_debug(self, x):
        dumps = {}
        dumps["input"] = x

        n1 = self.norm1(x)
        dumps["norm1"] = n1

        a = self.attn(n1)
        dumps["attn_out"] = a

        sa = self.scale1(a)
        dumps["attn_scaled"] = sa

        x1 = x + sa
        dumps["after_attn"] = x1

        n2 = self.norm2(x1)
        dumps["norm2"] = n2

        m, mlp_dump = self.mlp(n2, debug=True)
        dumps["mlp.fc1_out"] = mlp_dump["fc1_out"]
        dumps["mlp.gelu_out"] = mlp_dump["gelu_out"]
        dumps["mlp.fc2_out"] = mlp_dump["fc2_out"]

        dumps["mlp_out"] = m

        sm = self.scale2(m)
        dumps["mlp_scaled"] = sm

        x2 = x1 + sm
        dumps["output"] = x2
        return x2, dumps

    def __call__(self, x, debug=False):
        if debug:
            return self.forward_debug(x)

        x = x + self.scale1(self.attn(self.norm1(x)))
        x = x + self.scale2(self.mlp(self.norm2(x)))
        return x


class Dinov2Numpy:
    """DINOv2 ViT 推理主类（纯 NumPy）。

    使用方式:
        weights = np.load("vit-dinov2-base.npz")
        vit = Dinov2Numpy(weights)
        feat = vit(pixel_values)  # (B, D)

    输入/输出:
        pixel_values: (B, C, H, W)
        return: (B, D)  # 取 CLS token 作为图像全局特征
    """

    def __init__(self, weights, config=None):
        self.weights = weights
        self.config = config or {
            "hidden_size": 768,
            "num_heads": 12,
            "num_layers": 12,
            "patch_size": 14,
        }

        self.embeddings = Embeddings(weights)
        self.blocks = [TransformerBlock(self.config, i, weights) for i in range(self.config["num_layers"])]
        self.norm = LayerNorm(weights["layernorm.weight"], weights["layernorm.bias"])

    def forward_debug(self, pixel_values, debug_block_details=(7, 8)):
        """逐层输出中间结果，用于定位数值偏差从哪一层开始出现。

        返回一个 dict，键为层名，值为对应的 numpy 数组。
        当 block idx 在 debug_block_details 中时，额外输出该 block 的分支级中间量。
        """
        dumps = {}

        x = self.embeddings(pixel_values)
        dumps["embeddings"] = x

        for i, blk in enumerate(self.blocks):
            if i in debug_block_details:
                x, blk_dump = blk(x, debug=True)
                dumps[f"block_{i}"] = x
                dumps[f"block_{i}.detail"] = blk_dump
            else:
                x = blk(x)
                dumps[f"block_{i}"] = x

        x = self.norm(x)
        dumps["norm"] = x

        dumps["cls"] = x[:, 0]
        return dumps

    def __call__(self, pixel_values, debug=False, feature_mode="cls"):
        """提取图像特征。
        
        参数:
            pixel_values: (B, C, H, W) 输入图片
            debug: 是否返回逐层 dump 字典
            feature_mode: 特征提取模式
                - "cls": 使用 CLS token（默认，当前方式）
                - "patch_mean": 使用所有 patch tokens 的平均
                - "fused": 融合 CLS 和 patch mean（权重 0.5）
        
        返回:
            (B, D) 特征向量，或 debug=True 时的 dump 字典
        """
        if debug:
            return self.forward_debug(pixel_values)

        pos_embed = self.embeddings(pixel_values)
        for blk in self.blocks:
            pos_embed = blk(pos_embed)
        pos_embed = self.norm(pos_embed)
        
        if feature_mode == "cls":
            return pos_embed[:, 0]  # (B, D) CLS token
        elif feature_mode == "patch_mean":
            # 使用所有 patch tokens 的平均（排除 CLS）
            return pos_embed[:, 1:].mean(axis=1)  # (B, D)
        elif feature_mode == "fused":
            # 融合 CLS 和 patch mean
            cls_feat = pos_embed[:, 0]  # (B, D)
            patch_feat = pos_embed[:, 1:].mean(axis=1)  # (B, D)
            return 0.5 * cls_feat + 0.5 * patch_feat  # (B, D)
        else:
            raise ValueError(f"Unknown feature_mode: {feature_mode}, must be one of ['cls', 'patch_mean', 'fused']")
