"""
Lucy 的"AI 注意力"：在生成（降噪）的每一步，记录 6 个自注意力模块里
"每个位置被其他位置关注了多少"（注意力概率按列求和，再对 8 个头取平均）。

只读记录，不改变生成结果（同种子同设置，脸和平时完全一样）。
注意：Lucy 没有文字，这是"位置看位置"的注意力，没有语义（它不知道哪里是眼睛）。

运行（在 ai-thesis/code 目录）：
  python lucy_attention.py                 # 默认种子 11，10 步，出一张拼图
  python lucy_attention.py --seed 5 --steps 10
结果在 ../outputs_lucy/attention/ ：
  sheet_seed<种子>.png   每行一个模块，每列一个擦雾阶段（早→晚），热力叠在脸上
  mean_seed<种子>.png    16x16 模块、后半段平均的"AI 注意力"热力叠图（装置里要用的那张）
  face_seed<种子>.png    原脸
"""
import argparse
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M                     # noqa: E402
from diffusers.models.attention_processor import Attention, AttnProcessor   # noqa: E402
from render_heatmaps import colorize      # noqa: E402

OUT = "/Users/shanzeyang/Desktop/I can Here You/ai-thesis/outputs_lucy/attention"


class RecordingProcessor(AttnProcessor):
    """和默认处理器算法一样，只是多记一份"被关注总量"。"""

    def __init__(self, name, store):
        super().__init__()
        self.name, self.store = name, store

    def __call__(self, attn, hidden_states, encoder_hidden_states=None, attention_mask=None, temb=None, *args, **kwargs):
        residual = hidden_states
        if attn.spatial_norm is not None:
            hidden_states = attn.spatial_norm(hidden_states, temb)
        input_ndim = hidden_states.ndim
        if input_ndim == 4:
            b, c, h, w = hidden_states.shape
            hidden_states = hidden_states.view(b, c, h * w).transpose(1, 2)
        b, n, _ = hidden_states.shape if encoder_hidden_states is None else encoder_hidden_states.shape
        attention_mask = attn.prepare_attention_mask(attention_mask, n, b)
        if attn.group_norm is not None:
            hidden_states = attn.group_norm(hidden_states.transpose(1, 2)).transpose(1, 2)
        q = attn.to_q(hidden_states)
        if encoder_hidden_states is None:
            encoder_hidden_states = hidden_states
        elif attn.norm_cross:
            encoder_hidden_states = attn.norm_encoder_hidden_states(encoder_hidden_states)
        k = attn.to_k(encoder_hidden_states)
        v = attn.to_v(encoder_hidden_states)
        q, k, v = attn.head_to_batch_dim(q), attn.head_to_batch_dim(k), attn.head_to_batch_dim(v)
        probs = attn.get_attention_scores(q, k, attention_mask)        # (b*头数, N, N)
        col = probs.sum(dim=1)                                          # 每个位置被关注的总量 (b*头数, N)
        col = col.view(b, -1, col.shape[-1]).mean(dim=1)[0]             # 头平均，取第 1 张 -> (N)
        side = int(round(col.shape[0] ** 0.5))
        self.store.setdefault(self.name, []).append((M._S["frac"], col.reshape(side, side).float().cpu().numpy()))
        out = torch.bmm(probs, v)
        out = attn.batch_to_head_dim(out)
        out = attn.to_out[0](out)
        out = attn.to_out[1](out)
        if input_ndim == 4:
            out = out.transpose(-1, -2).reshape(b, c, h, w)
        if attn.residual_connection:
            out = out + residual
        return out / attn.rescale_output_factor


def overlay(face, amap, alpha=0.55, size=256):
    a = np.asarray(amap, dtype=np.float32)
    lo, hi = np.percentile(a, 2), np.percentile(a, 98)
    a = np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1)
    heat = Image.fromarray(colorize(a)).resize((size, size), Image.BICUBIC).convert("RGB")
    base = face.resize((size, size), Image.BICUBIC).convert("RGB")
    return Image.blend(base, heat, alpha), a


def record(seed, steps=10):
    M.load()
    store = {}
    unet = M._S["pipe"].unet
    old = {}
    for name, mod in unet.named_modules():
        if isinstance(mod, Attention):
            old[name] = mod.processor
            mod.set_processor(RecordingProcessor(name, store))
    try:
        face = M.sample(seed, None, steps, 256)
    finally:
        for name, mod in unet.named_modules():
            if name in old:
                mod.set_processor(old[name])
    return face, store


def mean_map(store, frac_from=0.5, res=16, size=64):
    """16x16（或指定分辨率）模块、擦雾后半段的平均注意力，统一缩放后再平均。"""
    acc, cnt = None, 0
    for name, lst in store.items():
        for f, a in lst:
            if f < frac_from or a.shape[0] != res:
                continue
            t = torch.from_numpy(a)[None, None]
            t = F.interpolate(t, size=(size, size), mode="bilinear", align_corners=False)[0, 0].numpy()
            t = (t - t.min()) / max(t.max() - t.min(), 1e-9)
            acc = t if acc is None else acc + t
            cnt += 1
    return acc / max(cnt, 1)


def install(store):
    """给 Lucy 的 6 个自注意力模块永久装上记录层（不改变生成结果）。store 是一个 dict，每次生成前请 store.clear()。"""
    M.load()
    for name, mod in M._S["pipe"].unet.named_modules():
        if isinstance(mod, Attention):
            mod.set_processor(RecordingProcessor(name, store))
    return store


def ai_overlay(store, face, size=512, alpha=0.55):
    """把后半段、16x16 模块的平均注意力叠在脸上，返回 PIL 图；没记录到就返回 None。"""
    mm = mean_map(store)
    if mm is None:
        return None
    im, _ = overlay(face, mm, alpha=alpha, size=size)
    return im


def ai_bw(store, size=512, gamma=1.6):
    """纯黑白的 AI 注意力图（没有脸）：越白 = AI 越关注。没记录到就返回 None。gamma>1 让亮的峰更突出、背景更黑。"""
    mm = mean_map(store)
    if mm is None:
        return None
    a = np.asarray(mm, dtype=np.float32)
    lo, hi = np.percentile(a, 2), np.percentile(a, 99)
    a = np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1) ** gamma
    im = Image.fromarray((a * 255).astype(np.uint8), mode="L").resize((size, size), Image.BICUBIC)
    return im.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--cols", type=int, default=5)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    face, store = record(args.seed, args.steps)
    face.save(os.path.join(OUT, f"face_seed{args.seed}.png"))
    names = sorted(store, key=lambda n: (n.split(".")[0] != "mid_block", n))
    print("记录到的模块：", {n: (len(store[n]), store[n][0][1].shape) for n in names})

    # 拼图：行=模块，列=擦雾阶段
    W = 160
    sheet = Image.new("RGB", (W * (args.cols + 1) + 140, (W + 18) * len(names)), "black")
    d = ImageDraw.Draw(sheet)
    for r, n in enumerate(names):
        lst = store[n]
        d.text((4, r * (W + 18) + 8), n.replace("_blocks", "").replace("attentions.", "a"), fill="white")
        idxs = np.linspace(0, len(lst) - 1, args.cols).round().astype(int)
        for c, i in enumerate(idxs):
            f, a = lst[i]
            im, _ = overlay(face, a, size=W)
            sheet.paste(im, (140 + c * W, r * (W + 18) + 18))
            d.text((140 + c * W + 4, r * (W + 18) + 2), f"t={f:.2f} {a.shape[0]}x{a.shape[1]}", fill="white")
    sheet.save(os.path.join(OUT, f"sheet_seed{args.seed}.png"))

    mm = mean_map(store)
    if mm is not None:
        im, a = overlay(face, mm, size=384)
        im.save(os.path.join(OUT, f"mean_seed{args.seed}.png"))
        np.save(os.path.join(OUT, f"mean_seed{args.seed}.npy"), mm)
    print("完成 ->", OUT)


if __name__ == "__main__":
    main()
