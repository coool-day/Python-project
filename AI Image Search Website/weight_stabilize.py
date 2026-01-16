import numpy as np


def clip_row_norms(w, max_norm):
    w = np.asarray(w).astype(np.float32, copy=True)
    row_norm = np.linalg.norm(w, axis=1)
    scale = np.ones_like(row_norm, dtype=np.float32)
    mask = row_norm > max_norm
    scale[mask] = (max_norm / (row_norm[mask] + 1e-12)).astype(np.float32)
    w *= scale[:, None]
    return w


def stabilize_weights(weights, layer_idx=8, max_norm=1.0):
    out = {k: v for k, v in weights.items()}
    key = f"encoder.layer.{layer_idx}.mlp.fc1.weight"
    out[key] = clip_row_norms(out[key], max_norm=max_norm)
    return out
