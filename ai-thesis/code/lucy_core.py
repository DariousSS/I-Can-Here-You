"""
Lucy（128x128 人脸 DDPM）的隐藏层改法。

和 GAN 的区别：GAN 画一张只走一遍；扩散模型要"擦雾"很多步（这里默认 DDIM 20 步，约 1.7 秒/张；50 步约 4 秒/张），
每一步都会经过所有层。所以除了"改哪一层、哪个通道、多大声"，还多一个旋钮：
**"在擦雾的哪一段时间里改"**（刚开始 = 决定大形状；快结束 = 只改细节）。

可改的层（每个"块"的最后一个残差块的输出）：
  D0..D4 : 编码器（128→8），MID : 最中间，U0..U4 : 解码器（8→128）
"""
import numpy as np
import torch
import torch.nn.functional as F
from diffusers import DDIMScheduler, DDPMPipeline
from PIL import Image

MODEL = "/Users/shanzeyang/Desktop/I can Here You/ai-thesis/models/Lucy"
_S = {"edits": {}, "frac": 0.0}
LAYER_NAMES = ["D0", "D1", "D2", "D3", "D4", "MID", "U0", "U1", "U2", "U3", "U4"]


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
    elif region == "eyes":
        mk[int(h * 0.30): int(h * 0.50), int(w * 0.15): int(w * 0.85)] = 1
    elif region == "mouth":
        mk[int(h * 0.62): int(h * 0.85), int(w * 0.28): int(w * 0.72)] = 1
    return mk


def _make_hook(name):
    def hook(module, inp, out):
        e = _S["edits"].get(name)
        if not e or e["factor"] == 0:
            return out
        f = _S["frac"]
        if not (e.get("t0", 0.0) <= f <= e.get("t1", 1.0)):
            return out
        out = out.clone()
        ch = e["channel"]
        v = out[:, ch]
        s = v.flatten(1).std(dim=1).clamp_min(1e-6)[:, None, None]
        if e.get("mask") is not None:      # 任意遮罩（比如"目光累积图"），0-1，会缩放到这一层的大小
            mk = F.interpolate(torch.as_tensor(e["mask"])[None, None].float(), size=(v.shape[-2], v.shape[-1]),
                               mode="bilinear", align_corners=False)[0, 0].to(v.device, v.dtype)[None]
        else:
            mk = _mask(v.shape[-2], v.shape[-1], e.get("region", "full")).to(v.device, v.dtype)[None]
        if e.get("mode", "even") == "even":
            add = e["factor"] * s * mk
        else:
            g = torch.Generator().manual_seed(1234)
            add = e["factor"] * s * torch.randn(v.shape, generator=g).abs().to(v.device, v.dtype) * mk
        out[:, ch] = v + add
        return out
    return hook


def load():
    if "pipe" in _S:
        return
    torch.set_grad_enabled(False)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    pipe = DDPMPipeline.from_pretrained(MODEL)
    pipe.unet.to(dev).eval()
    u = pipe.unet
    mods = {f"D{i}": u.down_blocks[i].resnets[-1] for i in range(len(u.down_blocks))}
    mods["MID"] = u.mid_block.resnets[-1]
    mods.update({f"U{i}": u.up_blocks[i].resnets[-1] for i in range(len(u.up_blocks))})
    info = {}
    for n, m in mods.items():
        m.register_forward_hook(_make_hook(n))
        def rec(mod, i, o, n=n):
            info.setdefault(n, tuple(o.shape[1:]))      # 只记录形状，不返回任何东西（返回值会替换输出！）
        m.register_forward_hook(rec)
    _S.update(pipe=pipe, dev=dev, sched=DDIMScheduler.from_config(pipe.scheduler.config), mods=mods)
    sample(1, steps=2)                      # 预热，同时记下每层形状 (通道, 高, 宽)
    _S["info"] = info


def layer_info(name):
    c, h, w = _S["info"][name]
    return {"channels": int(c), "res": int(h)}


def sample(seed, edits=None, steps=20, size=128):
    """返回 PIL 图。edits = {层名: {channel, factor, mode, region, t0, t1}}，t0/t1 是 0-1，表示擦雾的哪一段。"""
    if "pipe" not in _S:
        load()
    pipe, sched, dev = _S["pipe"], _S["sched"], _S["dev"]
    _S["edits"] = edits or {}
    sched.set_timesteps(steps)
    g = torch.Generator("cpu").manual_seed(int(seed))
    x = torch.randn(1, 3, 128, 128, generator=g).to(dev)
    n = len(sched.timesteps)
    for k, t in enumerate(sched.timesteps):
        _S["frac"] = k / max(1, n - 1)
        eps = pipe.unet(x, t).sample
        x = sched.step(eps, t, x, eta=0.0).prev_sample
    _S["edits"] = {}
    a = ((x / 2 + 0.5).clamp(0, 1)[0].permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
    im = Image.fromarray(a)
    return im if size == 128 else im.resize((size, size), Image.BICUBIC)
