"""
GAN 核心：加载 PGAN(celebAHQ-256) 并提供"画一张脸、可以在某一级的某个通道上调大"的函数。
被 gan_playground.py 使用。每张约 0.3 秒（CPU）。
"""
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

ZOO = "/Users/shanzeyang/Desktop/I can Here You/ai-thesis/models/pytorch_GAN_zoo"
STAGES = ["4x4", "8x8", "16x16", "32x32", "64x64", "128x128", "256x256"]
_S = {}


def load(model_name="celebAHQ-256", device="cpu"):
    """device="mps" 时用 Mac 的显卡（约 21 毫秒/张，CPU 约 200 毫秒/张；结果一样）。"""
    if "G" in _S:
        return
    torch.set_grad_enabled(False)
    m = torch.hub.load(ZOO, "PGAN", source="local", model_name=model_name, pretrained=True, useGPU=False)
    _S["m"] = m
    _S["G"] = m.avgG.eval()          # 平滑版生成器（官方推荐）
    if device != "cpu":
        _S["G"].to(device)


def n_channels(stage):
    G = _S["G"]
    return int(G.groupScale0[0].module.weight.shape[0] if stage == 0 else G.scaleLayers[stage - 1][1].module.weight.shape[0])


def _mask(h, w, region):
    mk = torch.zeros(h, w)
    if region == "full":
        mk[:] = 1
    elif region == "center":
        mk[h // 4: 3 * h // 4, w // 4: 3 * w // 4] = 1
    elif region == "top":
        mk[: h // 2] = 1
    elif region == "bottom":
        mk[h // 2:] = 1
    elif region == "left":
        mk[:, : w // 2] = 1
    elif region == "right":
        mk[:, w // 2:] = 1
    elif region == "eyes":                # 脸的大致眼睛位置（横带，偏上）
        mk[int(h * 0.30): int(h * 0.50), int(w * 0.15): int(w * 0.85)] = 1
    elif region == "mouth":               # 嘴巴大致位置
        mk[int(h * 0.62): int(h * 0.85), int(w * 0.28): int(w * 0.72)] = 1
    return mk


def _edit(x, e, gen):
    """e 可以是一个改动(dict)，也可以是一串改动(list)——同一级里同时改好几个通道（和弦）。"""
    if not e:
        return x
    for ee in (e if isinstance(e, list) else [e]):
        if ee["factor"] == 0:
            continue
        x = x.clone()
        v = x[:, ee["channel"]]
        s = v.flatten(1).std(dim=1).clamp_min(1e-6)[:, None, None]
        if ee.get("mask") is not None:      # 任意遮罩（比如"目光累积图"），0-1，会缩放到这一级的大小
            mk = F.interpolate(torch.as_tensor(ee["mask"])[None, None].float(), size=(v.shape[-2], v.shape[-1]),
                               mode="bilinear", align_corners=False)[0, 0].to(x.device, x.dtype)[None]
        else:
            mk = _mask(v.shape[-2], v.shape[-1], ee.get("region", "full")).to(x.device, x.dtype)[None]
        if ee.get("mode", "even") == "even":
            add = ee["factor"] * s * mk
        else:
            add = ee["factor"] * s * torch.randn(v.shape, generator=gen).abs().to(x.device, x.dtype) * mk
        x[:, ee["channel"]] = v + add
    return x


def _forward(z, edits):
    """edits: {stage: {channel, factor, mode, region}}；可以同时改好几级。"""
    G = _S["G"]
    z = z.to(next(G.parameters()).device)
    gen = torch.Generator().manual_seed(1234)
    x = G.normalizationLayer(z)
    x = x.view(-1, x.size(1))
    x = G.leakyRelu(G.formatLayer(x))
    x = x.view(x.size(0), -1, 4, 4)
    x = G.normalizationLayer(x)
    for conv in G.groupScale0:
        x = G.normalizationLayer(G.leakyRelu(conv(x)))
    x = _edit(x, edits.get(0), gen)
    for i, group in enumerate(G.scaleLayers, 1):
        x = F.interpolate(x, scale_factor=2, mode="nearest")
        for conv in group:
            x = G.normalizationLayer(G.leakyRelu(conv(x)))
        x = _edit(x, edits.get(i), gen)
    return G.toRGBLayers[-1](x)


def latent(seed):
    return torch.randn(1, 512, generator=torch.Generator().manual_seed(int(seed)))


def slerp(z1, z2, t):
    """两串随机数之间的"球面插值"：比直接平均更自然，脸不会变灰。"""
    a, b = z1 / z1.norm(), z2 / z2.norm()
    om = torch.acos((a * b).sum().clamp(-1, 1))
    if om.abs() < 1e-4:
        return z1
    return (torch.sin((1 - t) * om) * z1 + torch.sin(t * om) * z2) / torch.sin(om)


def render_z(z, edits=None, size=256):
    load()
    t = _forward(z, edits or {}).clamp(-1, 1).cpu()
    a = ((t[0].permute(1, 2, 0).numpy() + 1) * 127.5).astype(np.uint8)
    im = Image.fromarray(a)
    return im if size == 256 else im.resize((size, size), Image.BICUBIC)


def render(seed, edits=None, size=256):
    load()
    z = latent(seed)
    t = _forward(z, edits or {}).clamp(-1, 1).cpu()
    a = ((t[0].permute(1, 2, 0).numpy() + 1) * 127.5).astype(np.uint8)
    im = Image.fromarray(a)
    return im if size == 256 else im.resize((size, size), Image.BICUBIC)
