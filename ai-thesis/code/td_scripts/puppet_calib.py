# 在 TD 的 Textport 里运行：自动量一下"手"和"线"实际画在哪里（几秒钟，会临时摆一下，结束后自动藏起来）
# 结果写进 td_live/puppet_calib.txt
import numpy as np
p = op('/project1')
lines = []
Wc, Hc = 1920.0, 1080.0
meta = {'w': 1536.0, 'h': 1024.0}
Wp = 0.38 * Wc
Hp = Wp * meta['h'] / meta['w']


def opaque(o, thr=0.5):
    a = o.numpyArray()
    a = np.flipud(a)                      # TD 的数组第 0 行是图的底部，翻成"第 0 行在上"
    m = a[:, :, 3] > thr
    ys, xs = np.nonzero(m)
    return a, m, xs, ys


# 1) 原图（hand_img）：不透明区域的外框、指尖
src = p.op('hand_img')
a, m, xs, ys = opaque(src)
sx0, sy0, sx1, sy1 = xs.min(), ys.min(), xs.max(), ys.max()
d = np.hypot(xs - sx0, ys - sy0)
i = int(np.argmax(d))
lines.append('src size=' + str(src.width) + 'x' + str(src.height) + ' opaque bbox=' + str((int(sx0), int(sy0), int(sx1), int(sy1))) + ' tip=' + str((int(xs[i]), int(ys[i]))))
tip_src = (float(xs[i]), float(ys[i]))

# 2) 摆一次 pL_tf：中心放在画布正中
tf = p.op('pL_tf')
tf.par.sx = Wp / Wc
tf.par.sy = Hp / Hc
tf.par.tx = 0.0
tf.par.ty = 0.0
tf.par.rotate = 0.0
a2, m2, xs2, ys2 = opaque(tf)
ox0, oy0, ox1, oy1 = xs2.min(), ys2.min(), xs2.max(), ys2.max()
d2 = np.hypot(xs2 - ox0, ys2 - oy0)
j = int(np.argmax(d2))
lines.append('out size=' + str(tf.width) + 'x' + str(tf.height) + ' opaque bbox=' + str((int(ox0), int(oy0), int(ox1), int(oy1))) + ' tip=' + str((int(xs2[j]), int(ys2[j]))))
# 期望：整张图 Wp x Hp，居中；指尖 = 左上角 + (tip/源图尺寸) * 绘制尺寸
left, top = Wc / 2 - Wp / 2, Hc / 2 - Hp / 2
exp_tip = (left + tip_src[0] / meta['w'] * Wp, top + tip_src[1] / meta['h'] * Hp)
lines.append('expected tip=' + str((round(exp_tip[0]), round(exp_tip[1]))) + '  measured tip=' + str((int(xs2[j]), int(ys2[j]))) + '  diff(measured-expected)=' + str((round(xs2[j] - exp_tip[0]), round(ys2[j] - exp_tip[1]))))
lines.append('drawn opaque width ratio (out/src*1536/Wp)=' + str(round(((ox1 - ox0) / max(1.0, (sx1 - sx0))) * meta['w'] / Wp, 3)) + ' height ratio=' + str(round(((oy1 - oy0) / max(1.0, (sy1 - sy0))) * meta['h'] / Hp, 3)))

# 3) 一根线：从 A=(300,300) 到 B=(900,700)，宽 4
s1 = p.op('pstr1')
A_, B_ = (300.0, 300.0), (900.0, 700.0)
dx, dy = B_[0] - A_[0], B_[1] - A_[1]
import math
ln = (dx * dx + dy * dy) ** 0.5
s1.par.sx = 4.0 / Wc
s1.par.sy = ln / Hc
s1.par.tx = ((A_[0] + B_[0]) / 2 - Wc / 2) / Wc
s1.par.ty = (Hc / 2 - (A_[1] + B_[1]) / 2) / Hc
s1.par.rotate = math.degrees(math.atan2(-dx, -dy))
a3, m3, xs3, ys3 = opaque(s1)
lines.append('string expected ends A=(300,300) B=(900,700); measured opaque bbox=' + str((int(xs3.min()), int(ys3.min()), int(xs3.max()), int(ys3.max()))) + ' (如果线方向反了，bbox 会是 x 300..900, y 300..700 的镜像)')
# 线朝向：看左上角和右下角哪个更靠近线
tl = ((xs3 - 300) ** 2 + (ys3 - 300) ** 2).min() ** 0.5
tr = ((xs3 - 900) ** 2 + (ys3 - 300) ** 2).min() ** 0.5
lines.append('distance from measured string to (300,300)=' + str(round(float(tl), 1)) + ' ; to (900,300)=' + str(round(float(tr), 1)) + '  (前者应该接近 0，后者应该很大)')

# 4) 收回
for nm in ('pL_tf', 'pstr1'):
    o = p.op(nm)
    o.par.sx = 0.0001
    o.par.sy = 0.0001
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/puppet_calib.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('puppet calib written')
