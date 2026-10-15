"""童核风格滤镜（只改颜色，不改脸的内容）。
stylize(im, preset)  对 脸 / AI 叠图 用；stylize_bw(im, preset) 对 黑白注意力图用。
preset: 'off' 不处理 | 'candy' 糖果粉彩 | 'crayon' 蜡笔纸感 | 'dream' 奶油梦幻
"""
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def _arr(im):
    return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def _img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB")


def _lerp(a, b, t):
    return a * (1 - t) + b * t


def stylize(im, preset="candy"):
    if preset in (None, "", "off"):
        return im
    if preset == "candy":
        im = ImageEnhance.Color(im.convert("RGB")).enhance(1.35)
        a = _arr(im)
        a = _lerp(a, np.array([1.0, 0.86, 0.92]), 0.18)               # 整体罩一层粉
        a = a * 0.80 + np.array([0.20, 0.17, 0.26])                    # 黑色抬成淡紫，亮度更高，没有"死黑"
        return _img(a)
    if preset == "crayon":
        im = im.convert("RGB").filter(ImageFilter.ModeFilter(3)) if False else im.convert("RGB")
        a = _arr(ImageEnhance.Color(im).enhance(1.2))
        a = np.floor(a * 5.0) / 5.0 + 0.08                             # 色阶变少，像蜡笔色块
        rng = np.random.RandomState(7)
        grain = rng.rand(*a.shape[:2]).astype(np.float32)[..., None]
        a = a * (0.92 + 0.12 * grain)                                  # 纸的颗粒
        a = _lerp(a, np.array([1.0, 0.96, 0.84]), 0.25)                # 暖黄纸色
        return _img(a)
    if preset == "dream":
        a = _arr(ImageEnhance.Color(im.convert("RGB")).enhance(0.9))
        a = _lerp(a, np.array([1.0, 0.95, 0.88]), 0.30)                # 奶油色
        a = a * 0.70 + np.array([0.26, 0.24, 0.30])
        a = a ** 0.9
        return _img(a)
    return im


_BW = {                                                                   # 黑 -> 色A，白 -> 色B（线性渐变）
    "candy": ((0.30, 0.25, 0.55), (1.00, 0.86, 0.90)),                   # 深蓝紫 -> 粉白
    "crayon": ((0.18, 0.20, 0.45), (1.00, 0.95, 0.70)),                  # 墨蓝 -> 黄纸
    "dream": ((0.35, 0.30, 0.50), (1.00, 0.96, 0.90)),                   # 暗淡紫 -> 奶油
}


def stylize_bw(im, preset="candy"):
    if preset in (None, "", "off") or preset not in _BW:
        return im
    lo, hi = (np.array(c, dtype=np.float32) for c in _BW[preset])
    g = np.asarray(im.convert("L"), dtype=np.float32)[..., None] / 255.0
    a = lo * (1 - g) + hi * g
    if preset == "crayon":
        rng = np.random.RandomState(7)
        a = a * (0.93 + 0.10 * rng.rand(*g.shape[:2], 1).astype(np.float32))
    return _img(a)
