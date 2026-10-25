"""脸和"标准脸"（outputs_standard/standard_face.png，即平均脸）的偏离度。
做法：把脸缩到 128x128，只比较"脸的椭圆"（头发、背景不算），算和平均脸的均方根差；
再按参考标尺（deviation_ref.json：随机一批脸里最近的 5% 记 0，最远的 5% 记 1）线性缩放到 0-1。
0 = 在一批随机脸里属于最接近标准脸的那一档，1 = 属于最远的那一档（是相对尺度，不是绝对的"像不像"）。没有任何种族、性别之类的标签，只是像素上离平均脸有多远。
"""
import json
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
STD = os.path.join(HERE, "..", "outputs_standard", "standard_face.png")
REF = os.path.join(HERE, "..", "outputs_standard", "deviation_ref.json")
_C = {}


def _load():
    if "m" in _C:
        return
    m = np.asarray(Image.open(STD).convert("RGB").resize((128, 128), Image.LANCZOS)).astype(np.float64)
    yy, xx = np.mgrid[0:128, 0:128]
    ell = (((xx + 0.5) / 128 - 0.5) / 0.28) ** 2 + (((yy + 0.5) / 128 - 0.52) / 0.365) ** 2 <= 1.0     # 和面具用的脸椭圆同样大小（宽 0.56、高 0.73）
    p05, p95 = 30.0, 75.0
    try:
        with open(REF, encoding="utf-8") as f:
            r_ = json.load(f)
        p05, p95 = float(r_.get("p05", p05)), float(r_.get("p95", p95))
    except Exception:
        pass
    _C.update(m=m, ell=ell, p05=p05, p95=max(p95, p05 + 1e-3))


def raw(im):
    """原始距离（0-255 的像素尺度）。"""
    _load()
    a = np.asarray(im.convert("RGB").resize((128, 128), Image.LANCZOS)).astype(np.float64)
    d = (a - _C["m"]) ** 2
    return float(np.sqrt(d[_C["ell"]].mean()))


def deviation(im):
    _load()
    return float(min(1.0, max(0.0, (raw(im) - _C["p05"]) / (_C["p95"] - _C["p05"]))))
