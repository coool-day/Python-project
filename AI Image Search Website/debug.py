import os

import numpy as np

from dinov2_numpy import Dinov2Numpy
from preprocess_image import center_crop
from weight_stabilize import stabilize_weights

# 最小验证脚本（扩展版）：
# - 加载作业提供的 vit-dinov2-base.npz，并用 NumPy 实现做前向
# - 与 demo_data/cat_dog_feature.npy 对比（这是作业提供的参考输出）
# - 额外：打印逐层统计（embeddings / block_i / norm / cls），用于定位误差从哪一层开始出现
# - 额外：对指定 block（默认 7/8）打印 attention/mlp 分支级统计，用于定位“爆炸”来自哪条分支
# - 额外：打印 block_7/8 的 LayerScale 参数（lambda1）的统计，验证是否为 scale2 异常导致 MLP 分支爆炸
# - 额外：打印 block_7/8 的 MLP 权重/偏置 shape，验证是否存在 weight 转置/加载不一致
# - 额外：打印 block_7/8 的 fc1 权重/偏置统计（min/max/mean/std），判断 fc1_out 放大是否来自权重本身异常
# - 额外：打印 block_8 的 fc1_out 极值点，并对该通道做 dot/bias 分解（fc1_out = norm2 @ w_row + b）
# - 额外：打印 fc1.weight 的行范数 Top-K（layer7/layer8），确认是否存在少数“异常大行”
# - 额外：打印 fc1.weight 行范数分布与异常行计数（辅助向老师反馈：是否权重文件损坏/处理异常）
# - 可选：若本地已安装 torch/transformers 且已缓存/可访问 HF，则加载官方实现做逐层对照
#   用于定位从哪一层开始偏（不影响主逻辑、也不影响作业参考对齐）

# 控制是否启用权重稳定化（推荐开启，用于抑制 encoder.layer.8.mlp.fc1.weight 的离群行导致的数值爆炸）
ENABLE_WEIGHT_STABILIZE = True
WEIGHT_STABILIZE_LAYER_IDX = 8
WEIGHT_STABILIZE_MAX_NORM = 1.0

# 可选：在同一次运行中，对比「原始权重 vs 稳定化权重」在每一层的差异（仅 NumPy 内部对比，不依赖 transformers）
COMPARE_RAW_VS_STABILIZED = True

# 可选：扫描多组 max_norm 配置，观察 cat/dog 特征与参考输出的误差随 max_norm 变化的情况
RUN_MAX_NORM_SCAN = False
MAX_NORM_CANDIDATES = [1.0, 0.75, 0.5]

# 控制是否启用 transformers 对照：默认关闭，避免无网络环境下卡住
ENABLE_TRANSFORMERS_COMPARE = False

# 当 ENABLE_TRANSFORMERS_COMPARE=True 时：
# - 优先离线模式（只使用本地缓存），避免访问 huggingface.co 超时
# - 若你确认网络可用并希望自动下载，再把 OFFLINE_ONLY 改成 False
OFFLINE_ONLY = True

# 控制是否打印逐层统计（不依赖网络）
PRINT_LAYER_STATS = True

# 控制是否打印分支级统计（attention/mlp/残差）
PRINT_BLOCK_DETAIL_STATS = True

# 控制是否打印 LayerScale 的 lambda1 参数统计
PRINT_LAYERSCALE_STATS = True

# 控制是否打印 MLP 权重/偏置的 shape
PRINT_MLP_WEIGHT_SHAPES = True

# 控制是否打印 fc1.weight / fc1.bias 的统计
PRINT_FC1_WEIGHT_STATS = True

# 控制是否打印 block_8 的 mlp.fc1_out 极值位置（token_idx/channel_idx）
PRINT_FC1_OUT_EXTREME_LOC = True

# 控制是否打印 block_8 极值点的 dot/bias 分解（fc1_out = norm2 @ w_row + b_row）
PRINT_FC1_OUT_DOT_BIAS_BREAKDOWN = True

# 控制是否打印 fc1.weight 的行范数 Top-K
PRINT_FC1_ROW_NORM_TOPK = True
FC1_ROW_NORM_TOPK = 10

# 控制是否打印 fc1.weight 行范数分布与异常行计数
PRINT_FC1_ROW_NORM_DIST = True

# 只打印这些 block 的分支级统计（根据你当前现象，block_8 开始爆炸）
DETAIL_BLOCKS = (7, 8)


def _max_abs(x):
    return float(np.max(np.abs(x)))


def _l2(x):
    return float(np.linalg.norm(x))


def _to_numpy(x):
    return x.detach().cpu().numpy()


def _stats(x):
    x = np.asarray(x)
    return {
        "shape": tuple(x.shape),
        "dtype": str(x.dtype),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "mean": float(np.mean(x)),
        "std": float(np.std(x)),
    }


def _print_stats(title, x):
    s = _stats(x)
    print(
        f"{title}: shape={s['shape']}, dtype={s['dtype']}, min={s['min']:.6e}, max={s['max']:.6e}, mean={s['mean']:.6e}, std={s['std']:.6e}"
    )


def _print_shape(title, x):
    x = np.asarray(x)
    print(f"{title}: shape={tuple(x.shape)}, dtype={x.dtype}")


def _row_norms(w):
    w = np.asarray(w).astype(np.float64)
    return np.linalg.norm(w, axis=1)


def _print_row_norm_topk(layer_idx, w_fc1, topk=10):
    w = np.asarray(w_fc1).astype(np.float64)
    row_norm = np.linalg.norm(w, axis=1)
    top_idx = np.argsort(-row_norm)[:topk]
    print(f"[FC1 row-norm Top-{topk}] encoder.layer.{layer_idx}.mlp.fc1.weight")
    for r in top_idx:
        wr = w[int(r)]
        print(
            f"row={int(r):4d} | l2={float(row_norm[int(r)]):.6e} | min={float(wr.min()):.6e} | max={float(wr.max()):.6e} | mean={float(wr.mean()):.6e} | std={float(wr.std()):.6e}"
        )
    print()


def _print_row_norm_dist(layer_idx, w_fc1):
    rn = _row_norms(w_fc1)
    qs = {
        "min": float(np.min(rn)),
        "p50": float(np.quantile(rn, 0.50)),
        "p90": float(np.quantile(rn, 0.90)),
        "p95": float(np.quantile(rn, 0.95)),
        "p99": float(np.quantile(rn, 0.99)),
        "max": float(np.max(rn)),
    }
    print(f"[FC1 row-norm distribution] encoder.layer.{layer_idx}.mlp.fc1.weight")
    print(
        f"min={qs['min']:.6e}, p50={qs['p50']:.6e}, p90={qs['p90']:.6e}, p95={qs['p95']:.6e}, p99={qs['p99']:.6e}, max={qs['max']:.6e}"
    )

    for thr in [1.0, 2.0, 3.0]:
        cnt = int(np.sum(rn > thr))
        print(f"count(row_norm>{thr:.1f})={cnt} / {rn.shape[0]}")
    print()


def main():
    base_dir = os.path.dirname(__file__)
    demo_dir = os.path.join(base_dir, "demo_data")

    # 原始权重 + 稳定化权重（若启用）
    raw_weights = np.load(os.path.join(base_dir, "vit-dinov2-base.npz"))
    if ENABLE_WEIGHT_STABILIZE:
        stab_weights = stabilize_weights(
            raw_weights,
            layer_idx=WEIGHT_STABILIZE_LAYER_IDX,
            max_norm=WEIGHT_STABILIZE_MAX_NORM,
        )
        print(
            f"[Weight stabilize] 已对 encoder.layer.{WEIGHT_STABILIZE_LAYER_IDX}.mlp.fc1.weight "
            f"执行 row_norm clipping，max_norm={WEIGHT_STABILIZE_MAX_NORM}"
        )
        weights = stab_weights
    else:
        stab_weights = None
        weights = raw_weights

    vit_np = Dinov2Numpy(weights)

    cat_pixel_values = center_crop(os.path.join(demo_dir, "cat.jpg"))
    dog_pixel_values = center_crop(os.path.join(demo_dir, "dog.jpg"))

    if PRINT_LAYER_STATS:
        print("[Input stats]")
        _print_stats("cat_pixel_values", cat_pixel_values)
        _print_stats("dog_pixel_values", dog_pixel_values)
        print()

    cat_dump = vit_np.forward_debug(cat_pixel_values, debug_block_details=DETAIL_BLOCKS)
    dog_dump = vit_np.forward_debug(dog_pixel_values, debug_block_details=DETAIL_BLOCKS)

    cat_feat = cat_dump["cls"]
    dog_feat = dog_dump["cls"]

    if PRINT_LAYER_STATS:
        print("[Layer stats (NumPy, cat, stabilized权重)]" if ENABLE_WEIGHT_STABILIZE else "[Layer stats (NumPy, cat, raw权重)]")
        _print_stats("embeddings", cat_dump["embeddings"])
        for i in range(vit_np.config["num_layers"]):
            _print_stats(f"block_{i}", cat_dump[f"block_{i}"])
        _print_stats("norm", cat_dump["norm"])
        _print_stats("cls", cat_dump["cls"])
        print()

    if PRINT_LAYERSCALE_STATS:
        print("[LayerScale lambda stats (NumPy model params)]")
        for bi in DETAIL_BLOCKS:
            blk = vit_np.blocks[bi]
            _print_stats(f"block_{bi}.scale1.lambda1", blk.scale1.lambda1)
            _print_stats(f"block_{bi}.scale2.lambda1", blk.scale2.lambda1)
        print()

    if PRINT_MLP_WEIGHT_SHAPES:
        print("[MLP weight/bias shapes (from当前使用的 weights)]")
        for bi in DETAIL_BLOCKS:
            prefix = f"encoder.layer.{bi}"
            _print_shape(f"{prefix}.mlp.fc1.weight", weights[f"{prefix}.mlp.fc1.weight"])
            _print_shape(f"{prefix}.mlp.fc1.bias", weights[f"{prefix}.mlp.fc1.bias"])
            _print_shape(f"{prefix}.mlp.fc2.weight", weights[f"{prefix}.mlp.fc2.weight"])
            _print_shape(f"{prefix}.mlp.fc2.bias", weights[f"{prefix}.mlp.fc2.bias"])
        print()

    if PRINT_FC1_WEIGHT_STATS:
        print("[MLP fc1 weight/bias stats (from当前使用的 weights)]")
        for bi in DETAIL_BLOCKS:
            prefix = f"encoder.layer.{bi}"
            _print_stats(f"{prefix}.mlp.fc1.weight", weights[f"{prefix}.mlp.fc1.weight"])
            _print_stats(f"{prefix}.mlp.fc1.bias", weights[f"{prefix}.mlp.fc1.bias"])
        print()

    if PRINT_FC1_ROW_NORM_TOPK:
        w7 = weights["encoder.layer.7.mlp.fc1.weight"]
        w8 = weights["encoder.layer.8.mlp.fc1.weight"]
        _print_row_norm_topk(7, w7, topk=FC1_ROW_NORM_TOPK)
        _print_row_norm_topk(8, w8, topk=FC1_ROW_NORM_TOPK)

    if PRINT_FC1_ROW_NORM_DIST:
        w7 = weights["encoder.layer.7.mlp.fc1.weight"]
        w8 = weights["encoder.layer.8.mlp.fc1.weight"]
        _print_row_norm_dist(7, w7)
        _print_row_norm_dist(8, w8)

    if PRINT_FC1_OUT_EXTREME_LOC:
        bi = 8
        k = f"block_{bi}.detail"
        if k in cat_dump and "mlp.fc1_out" in cat_dump[k] and "norm2" in cat_dump[k]:
            fc1_out = np.asarray(cat_dump[k]["mlp.fc1_out"])[0]
            norm2 = np.asarray(cat_dump[k]["norm2"])[0]

            max_idx = int(np.argmax(fc1_out))
            max_tok = int(max_idx // fc1_out.shape[1])
            max_ch = int(max_idx % fc1_out.shape[1])
            max_val = float(fc1_out[max_tok, max_ch])

            min_idx = int(np.argmin(fc1_out))
            min_tok = int(min_idx // fc1_out.shape[1])
            min_ch = int(min_idx % fc1_out.shape[1])
            min_val = float(fc1_out[min_tok, min_ch])

            print("[Block 8 fc1_out 极值定位 (NumPy, cat)]")
            print(f"max fc1_out={max_val:.6e} at token_idx={max_tok} (0=CLS), channel_idx={max_ch}")
            _print_stats(f"norm2[token={max_tok}]", norm2[max_tok])
            print(f"min fc1_out={min_val:.6e} at token_idx={min_tok} (0=CLS), channel_idx={min_ch}")
            _print_stats(f"norm2[token={min_tok}]", norm2[min_tok])
            print()

            if PRINT_FC1_OUT_DOT_BIAS_BREAKDOWN:
                prefix = f"encoder.layer.{bi}"
                w_fc1 = np.asarray(weights[f"{prefix}.mlp.fc1.weight"])  # (3072, 768)
                b_fc1 = np.asarray(weights[f"{prefix}.mlp.fc1.bias"])    # (3072,)

                w_row = w_fc1[max_ch]
                b_row = float(b_fc1[max_ch])

                dot_max = float(norm2[max_tok] @ w_row)
                dot_min = float(norm2[min_tok] @ w_row)

                print("[Block 8 fc1_out dot/bias 分解 (NumPy, cat)]")
                print(f"channel_idx={max_ch} 的 bias={b_row:.6e}")
                print(f"max_tok={max_tok}: dot={dot_max:.6e}, dot+bias={dot_max + b_row:.6e}, fc1_out={max_val:.6e}")
                print(f"min_tok={min_tok}: dot={dot_min:.6e}, dot+bias={dot_min + b_row:.6e}, fc1_out={min_val:.6e}")
                _print_stats(f"fc1.weight[row={max_ch}]", w_row)
                print()

    if PRINT_BLOCK_DETAIL_STATS:
        for bi in DETAIL_BLOCKS:
            k = f"block_{bi}.detail"
            if k not in cat_dump:
                continue
            bd = cat_dump[k]
            print(f"[Block {bi} detail stats (NumPy, cat)]")
            _print_stats("input", bd["input"])
            _print_stats("norm1", bd["norm1"])
            _print_stats("attn_out", bd["attn_out"])
            _print_stats("attn_scaled", bd["attn_scaled"])
            _print_stats("after_attn", bd["after_attn"])
            _print_stats("norm2", bd["norm2"])
            _print_stats("mlp_out", bd["mlp_out"])
            _print_stats("mlp.fc1_out", bd["mlp.fc1_out"])
            _print_stats("mlp.gelu_out", bd["mlp.gelu_out"])
            _print_stats("mlp.fc2_out", bd["mlp.fc2_out"])
            _print_stats("mlp_scaled", bd["mlp_scaled"])
            _print_stats("output", bd["output"])
            print()

    ref = np.load(os.path.join(demo_dir, "cat_dog_feature.npy"))
    cat_ref, dog_ref = ref[0], ref[1]

    print("[Compare with assignment reference cat_dog_feature.npy （当前 weights）]")
    print(f"cat max abs diff: {_max_abs(cat_feat - cat_ref):.6e}, l2 diff: {_l2(cat_feat - cat_ref):.6e}")
    print(f"dog max abs diff: {_max_abs(dog_feat - dog_ref):.6e}, l2 diff: {_l2(dog_feat - dog_ref):.6e}")
    print()

    # 可选：对比 raw vs stabilized 在每一层的差异，帮助你更精细地理解裁剪对数值的影响
    if COMPARE_RAW_VS_STABILIZED and ENABLE_WEIGHT_STABILIZE and stab_weights is not None:
        print("[Raw vs Stabilized 对比（逐层 NumPy 内部对照，不依赖 transformers）]")

        vit_raw = Dinov2Numpy(raw_weights)
        cat_dump_raw = vit_raw.forward_debug(cat_pixel_values, debug_block_details=[])

        keys = ["embeddings"] + [f"block_{i}" for i in range(vit_np.config["num_layers"])] + ["norm", "cls"]
        for k in keys:
            np_x = cat_dump.get(k)
            raw_x = cat_dump_raw.get(k)
            if np_x is None or raw_x is None:
                continue
            if np_x.shape != raw_x.shape:
                print(f"{k}: shape mismatch stabilized{np_x.shape} vs raw{raw_x.shape} (skip)")
                continue
            diff = np_x - raw_x
            print(f"{k}: max_abs={_max_abs(diff):.6e}, l2={_l2(diff):.6e}")
        print()

    # 可选：扫描多组 max_norm，看哪一组更接近作业参考特征
    if RUN_MAX_NORM_SCAN:
        print("[Max-norm 扫描：不同裁剪强度下与参考特征的误差]")
        print("  max_norm | cat_max_abs  cat_l2_diff  dog_max_abs  dog_l2_diff")
        for mn in MAX_NORM_CANDIDATES:
            ws = stabilize_weights(raw_weights, layer_idx=WEIGHT_STABILIZE_LAYER_IDX, max_norm=mn)
            vit_tmp = Dinov2Numpy(ws)
            cat_tmp = vit_tmp(center_crop(os.path.join(demo_dir, "cat.jpg")))[0]
            dog_tmp = vit_tmp(center_crop(os.path.join(demo_dir, "dog.jpg")))[0]
            print(
                f"{mn:9.3f} | "
                f"{_max_abs(cat_tmp - cat_ref):10.3e}  {_l2(cat_tmp - cat_ref):10.3e}  "
                f"{_max_abs(dog_tmp - dog_ref):10.3e}  {_l2(dog_tmp - dog_ref):10.3e}"
            )
        print()

    if not ENABLE_TRANSFORMERS_COMPARE:
        print("[Skip transformers compare] 当前未开启 ENABLE_TRANSFORMERS_COMPARE。")
        print("如需逐层对照：请将 debug.py 顶部的 ENABLE_TRANSFORMERS_COMPARE = True")
        if OFFLINE_ONLY:
            print("当前 OFFLINE_ONLY=True：只使用本地 HuggingFace 缓存，不会联网下载。")
        else:
            print("当前 OFFLINE_ONLY=False：可能会联网下载模型/配置文件。")
        return

    try:
        import torch
        from transformers import AutoImageProcessor, AutoModel

        if OFFLINE_ONLY:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_id = "facebook/dinov2-base"

        processor = AutoImageProcessor.from_pretrained(model_id, local_files_only=OFFLINE_ONLY)
        model = AutoModel.from_pretrained(model_id, local_files_only=OFFLINE_ONLY)
        model.eval().to(device)

        from PIL import Image

        cat_img = Image.open(os.path.join(demo_dir, "cat.jpg")).convert("RGB")
        inputs = processor(images=[cat_img], return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)

        hs = outputs.hidden_states
        torch_dump = {"embeddings": _to_numpy(hs[0])}
        for i in range(1, len(hs)):
            torch_dump[f"block_{i-1}"] = _to_numpy(hs[i])

        print(f"[Layerwise compare with transformers ({model_id}) on {device}]")
        keys = ["embeddings"] + [f"block_{i}" for i in range(vit_np.config["num_layers"])]
        for k in keys:
            np_x = cat_dump.get(k)
            th_x = torch_dump.get(k)
            if np_x is None or th_x is None:
                continue
            if np_x.shape != th_x.shape:
                print(f"{k}: shape mismatch numpy{np_x.shape} vs torch{th_x.shape} (skip)")
                continue

            diff = np_x - th_x
            print(f"{k}: max_abs={_max_abs(diff):.6e}, l2={_l2(diff):.6e}")

        print("\n提示：若这里从 embeddings 就差很多，通常是预处理或 patch 展平顺序不一致导致。")

    except Exception as e:
        print("[Skip transformers compare] torch/transformers 加载失败或处于离线且本地无缓存：")
        print(str(e))


if __name__ == "__main__":
    main()
