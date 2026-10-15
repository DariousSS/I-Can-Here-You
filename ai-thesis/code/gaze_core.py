"""
目光累积 -> 隐藏层（核心）。

  你看哪里，哪里就"累积"（dwell map）；看得越久越大；移开就慢慢退。
  累积图当作"遮罩"，去调大某一层某个通道的数字：看得越久的地方，隐藏层变化越大。

模型可选：lucy（128 脸，扩散，慢但画质好）/ gan（PGAN 256 脸，快）。
"""
import math
import os
import sys

import numpy as np
import torch
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from render_heatmaps import colorize           # noqa: E402


class GazeFace:
    def __init__(self, model="lucy", layer="U3", channel=102, fmax=140.0, steps=10,
                 rise=3.0, decay=10.0, sigma=0.12, grid=24, size=512, mode="even", t0=0.0, t1=1.0):
        self.model, self.layer, self.channel, self.fmax = model, layer, int(channel), float(fmax)
        self.steps, self.rise, self.decay, self.sigma, self.G = steps, rise, decay, sigma, grid
        self.size, self.mode, self.t0, self.t1 = size, mode, t0, t1
        self.D = torch.zeros(grid, grid)
        c = (torch.arange(grid).float() + 0.5) / grid
        self.cx, self.cy = c[None, :], c[:, None]
        if model == "lucy":
            import lucy_core as M
            M.load()
        else:
            import gan_core as M
            M.load(device="mps")
        self.M = M

    def update(self, gaze, dt):
        """gaze: (x, y) 范围 0-1，或 None（没在看）。dt：距离上次更新过了几秒。"""
        self.D = self.D * math.exp(-dt / self.decay)
        if gaze is not None:
            gx, gy = float(gaze[0]), float(gaze[1])
            w = torch.exp(-((self.cx - gx) ** 2 + (self.cy - gy) ** 2) / (2 * self.sigma ** 2))
            self.D = self.D + w * (dt / self.rise)
        self.D = self.D.clamp(0, 1)

    def reset(self):
        self.D = torch.zeros_like(self.D)

    def face(self, seed, extra=None):
        """extra：额外的改动 {层名: {channel, factor, mode, t0, t1}}（比如琴键）。只有 Lucy 支持；和目光用同一层时以目光为准。"""
        e = {"channel": self.channel, "factor": self.fmax, "mode": self.mode, "mask": self.D.clone()}
        if self.model == "lucy":
            e.update(t0=self.t0, t1=self.t1)
            edits = dict(extra or {})
            edits[self.layer] = e
            return self.M.sample(seed, edits, self.steps, self.size)
        return self.M.render(seed, {int(self.layer.lstrip("U")) if isinstance(self.layer, str) else self.layer: e}, self.size)

    def heat(self, size=256):
        a = self.D.numpy()
        return Image.fromarray(colorize(a)).resize((size, size), Image.BICUBIC)
