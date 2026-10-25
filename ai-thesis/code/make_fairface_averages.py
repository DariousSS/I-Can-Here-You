"""FairFace（外部数据文件夹里的 parquet）-> 平均脸、万花筒预览、PCA"特征脸"生成器预览。
类别是数据集作者标注的 7 类（不是我们分的）；所有类别用同样的处理、并排放在一起。照片不保存、不展示，只留平均图和从 PCA 生成的新脸。
运行：nice -n 15 python make_fairface_averages.py   -> ../outputs_standard/fairface/
"""
import io, json, os, sys, time
import numpy as np
import pyarrow.parquet as pq
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/shanzeyang/Desktop/外部数据/FairFace_0.25"
OUT = os.path.join(HERE, "..", "outputs_standard", "fairface")
os.makedirs(OUT, exist_ok=True)
FILES = sorted(f for f in os.listdir(SRC) if f.endswith(".parquet"))
RACES = ['East Asian', 'Indian', 'Black', 'White', 'Middle Eastern', 'Latino_Hispanic', 'Southeast Asian']
CAP = 1500          # 每个类别最多用多少张
PCA_N = 64          # PCA 用的缩小尺寸
S = 224

sums = {r: np.zeros((S, S, 3)) for r in range(7)}
cnt = {r: 0 for r in range(7)}
small = {r: [] for r in range(7)}
t0 = time.time()
rng = np.random.default_rng(7)
done = False
for fn in FILES:
    pf = pq.ParquetFile(os.path.join(SRC, fn))
    for g in range(pf.num_row_groups):
        tb = pf.read_row_group(g, columns=['image', 'race']).to_pylist()
        order = rng.permutation(len(tb))
        for i in order:
            row = tb[i]
            r = int(row['race'])
            if cnt[r] >= CAP:
                continue
            im = Image.open(io.BytesIO(row['image']['bytes'])).convert('RGB').resize((S, S), Image.LANCZOS)
            sums[r] += np.asarray(im, dtype=np.float64)
            small[r].append(np.asarray(im.resize((PCA_N, PCA_N), Image.LANCZOS), dtype=np.uint8))
            cnt[r] += 1
        if all(cnt[r] >= CAP for r in range(7)):
            done = True
            break
    print(fn, '已用', cnt, '用时', round(time.time() - t0), '秒', flush=True)
    if done:
        break
tot = sum(cnt.values())
means = {r: (sums[r] / max(cnt[r], 1)) for r in range(7)}
means['all'] = sum(sums[r] for r in range(7)) / tot          # 各类别张数相同 -> 等权平均
for k, m in means.items():
    name = 'avg_all' if k == 'all' else 'avg_' + RACES[k].replace(' ', '_')
    Image.fromarray(m.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, name + '.png'))

# 对齐方式不同：FairFace 是 dlib 裁切；Lucy 是 CelebA 对齐。拿 Lucy 标准脸放在最前面做对照（只作对照，注意裁剪不同）
lucy = Image.open(os.path.join(HERE, '..', 'outputs_standard', 'standard_face.png')).convert('RGB').resize((S, S), Image.LANCZOS)
tiles = [('Lucy / CelebA', lucy), ('FairFace  all (balanced)', Image.fromarray(means['all'].clip(0, 255).astype(np.uint8)))] + [(RACES[r], Image.fromarray(means[r].clip(0, 255).astype(np.uint8))) for r in range(7)]
sheet = Image.new('RGB', (S * 3 + 40, (S + 30) * 3 + 20), (20, 16, 30))
d = ImageDraw.Draw(sheet)
for i, (nm, im) in enumerate(tiles):
    x, y = 10 + (i % 3) * (S + 10), 10 + (i // 3) * (S + 30)
    sheet.paste(im, (x, y + 22))
    d.text((x + 4, y + 4), nm, fill=(255, 255, 255))
sheet.save(os.path.join(OUT, 'averages_sheet.png'))


def kaleido(src, size=448, n=6, rot=0.0, zoom=1.0):
    """六重镜像万花筒：把源图的一个楔形镜像复制 n 次。"""
    a = np.asarray(src.resize((S, S)), dtype=np.float64)
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    cx = cy = (size - 1) / 2
    dx, dy = xx - cx, yy - cy
    r = np.hypot(dx, dy) / (size / 2)
    th = np.arctan2(dy, dx) + rot
    seg = np.pi / n
    th = np.abs(((th + seg) % (2 * seg)) - seg)
    sx = (0.5 + 0.5 * r * np.cos(th) * zoom) * (S - 1)
    sy = (0.5 + 0.5 * r * np.sin(th) * zoom) * (S - 1)
    sxi, syi = np.clip(sx.astype(int), 0, S - 1), np.clip(sy.astype(int), 0, S - 1)
    out = a[syi, sxi]
    out[r > 1] = 0
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


kt = [(nm, kaleido(im, rot=0.35)) for nm, im in tiles[:2] + [tiles[2], tiles[8]]]
ksheet = Image.new('RGB', (448 * 4 + 50, 448 + 30), (20, 16, 30))
d = ImageDraw.Draw(ksheet)
for i, (nm, im) in enumerate(kt):
    ksheet.paste(im, (10 + i * 458, 24))
    d.text((14 + i * 458, 6), nm, fill=(255, 255, 255))
ksheet.save(os.path.join(OUT, 'kaleidoscope_sheet.png'))


def pca_faces(arr, k=40, nsamp=8, seed=3):
    X = np.stack(arr).reshape(len(arr), -1).astype(np.float64)
    mu = X.mean(0)
    U, Sv, Vt = np.linalg.svd(X - mu, full_matrices=False)
    sd = Sv[:k] / np.sqrt(len(arr))
    rg = np.random.default_rng(seed)
    out = []
    for _ in range(nsamp):
        z = rg.standard_normal(k) * sd
        out.append((mu + z @ Vt[:k]).reshape(PCA_N, PCA_N, 3).clip(0, 255).astype(np.uint8))
    return out


groups = [('FairFace all', [a for r in range(7) for a in small[r]]), ('East Asian', small[0]), ('Southeast Asian', small[6]), ('White', small[3])]
psheet = Image.new('RGB', (8 * 130 + 20, len(groups) * 150 + 10), (20, 16, 30))
d = ImageDraw.Draw(psheet)
for gi, (nm, arr) in enumerate(groups):
    faces = pca_faces(arr)
    d.text((8, gi * 150 + 4), nm + '（PCA 生成的新脸，不是真人）', fill=(255, 255, 255))
    for j, f in enumerate(faces):
        psheet.paste(Image.fromarray(f).resize((120, 120), Image.LANCZOS), (10 + j * 128, gi * 150 + 22))
psheet.save(os.path.join(OUT, 'pca_samples_sheet.png'))
print('完成，用时', round(time.time() - t0), '秒 ->', os.path.abspath(OUT))
