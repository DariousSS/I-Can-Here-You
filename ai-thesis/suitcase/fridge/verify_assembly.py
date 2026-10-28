"""把每块板"拼"起来检查：逐个体素看有没有 重叠 / 缺口。用法: python3 verify_assembly.py --w 560 --d 400 --h 950 --t 4 --finger 20 --tiers --split 0.42"""
import sys, runpy, os, io, contextlib
import numpy as np
argv = sys.argv[1:] + ['--name', '_verify_tmp']
sys.argv = ['fridge_laser.py'] + argv
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(HERE, 'fridge_laser.py'))
W, D, H, T = G['W'], G['D'], G['H'], G['T']
parts = {p[0]: p for p in G['parts']}
shelf_vs = G['shelf_vs']
vs = T / 2.0

def inside(poly, px, py):
    m = np.zeros(px.shape, dtype=bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if y1 == y2:
            continue
        cond = ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1)
        m ^= cond
    return m

def raster(p, A, B):
    nu, nv = int(round(A / vs)), int(round(B / vs))
    u = (np.arange(nu) + 0.5) * vs
    v = (np.arange(nv) + 0.5) * vs
    PU, PV = np.meshgrid(u, v, indexing='ij')
    cuts = p[3]
    m = inside(cuts[0], PU, PV)
    for hole in cuts[1:]:
        m &= ~inside(hole, PU, PV)
    return m

nx, ny, nz = int(round(W / vs)), int(round(D / vs)), int(round(H / vs))
cnt = np.zeros((nx, ny, nz), dtype=np.int8)
t = int(round(T / vs))
def put(sel, mask2d, axes):
    """axes: 板的 (u, v) 分别对应 3D 的哪个轴；sel: 第三个轴上的范围"""
    pass
# 底、顶：u=x, v=y
m = raster(parts['bottom'], W, D)
cnt[:, :, 0:t] += m[:, :, None].astype(np.int8)
m = raster(parts['top'], W, D)
cnt[:, :, nz - t:nz] += m[:, :, None].astype(np.int8)
# 左、右：u=y, v=z
m = raster(parts['left'], D, H)
cnt[0:t, :, :] += m[None, :, :].astype(np.int8)
m = raster(parts['right'], D, H)
cnt[nx - t:nx, :, :] += m[None, :, :].astype(np.int8)
# 后：u=x, v=z
m = raster(parts['back'], W, H)
cnt[:, ny - t:ny, :] += m[:, None, :].astype(np.int8)
# 搁板：u=x, v=y，厚 T，z 从 shelf_vs
for k, z0 in enumerate(shelf_vs):
    p = parts['shelf%d' % (k + 1)]
    m = raster(p, p[1], p[2])
    k0 = int(round(z0 / vs))
    cnt[0:m.shape[0], 0:m.shape[1], k0:k0 + t] += m[:, :, None].astype(np.int8)
E = np.zeros((nx, ny, nz), dtype=bool)
E[:, :, 0:t] = True; E[:, :, nz - t:] = True; E[0:t, :, :] = True; E[nx - t:, :, :] = True; E[:, ny - t:, :] = True
bp = parts['back']                                  # 后板上的出线孔是故意开的，不算缺口
nu_, nv_ = int(round(W / vs)), int(round(H / vs))
uu = (np.arange(nu_) + 0.5) * vs; vv = (np.arange(nv_) + 0.5) * vs
PU, PV = np.meshgrid(uu, vv, indexing='ij')
holes = np.zeros((nu_, nv_), dtype=bool)
for hole in bp[3][1:]:
    holes |= inside(hole, PU, PV)
E[:, ny - t:, :] &= ~holes[:, None, :]
over = int((cnt > 1).sum())
gaps = int((E & (cnt == 0)).sum())
extra = int((~E & (cnt > 0)).sum())
shelf_vol = sum(int(round(parts['shelf%d' % (k + 1)][1] / vs)) * int(round(parts['shelf%d' % (k + 1)][2] / vs)) * t for k in range(len(shelf_vs)))
print('尺寸 %.0f x %.0f x %.0f mm，板厚 %.0f，体素 %.1f mm' % (W, D, H, T, vs))
print('重叠体素:', over, '| 缺口体素（外壳里没有材料的地方）:', gaps, '| 外壳之外的体素:', extra, '（搁板体积约', shelf_vol, '，应该接近）')
ok = over == 0 and gaps == 0
print('结论:', '榫头互相咬合，没有重叠也没有缺口' if ok else '有问题，需要检查')
if over:
    idx = np.argwhere(cnt > 1)[:5]; print('重叠位置示例(体素):', idx.tolist())
if gaps:
    idx = np.argwhere(E & (cnt == 0))[:5]; print('缺口位置示例(体素):', idx.tolist())
