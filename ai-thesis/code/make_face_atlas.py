"""把脸拼成一张图集 assets/atlas/faces_atlas.png（4x4，每格 256 像素）：
0~11 = 12 张爆开脸；12 = 留空（TD 里会把"此刻的实时脸"叠到这一格）；13 = Lucy/CelebA 标准脸；14 = FairFace 平均脸；15 = 留空（TD 里会把"此刻实时脸的 AI 注意力叠图"叠到这一格）。
棋盘和巨大拼脸的着色器只读这一张图，用编号找格子（不用一次接很多输入口）。运行：python make_face_atlas.py
"""
import os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
A = Image.new('RGB', (1024, 1024), (0, 0, 0))
def put(k, im):
    A.paste(im.convert('RGB').resize((256, 256), Image.LANCZOS), ((k % 4) * 256, (k // 4) * 256))
for i in range(12):
    put(i, Image.open(os.path.join(HERE, '..', 'td_live', 'burst', 'face_%02d.jpg' % i)))
put(13, Image.open(os.path.join(HERE, '..', 'outputs_standard', 'standard_face.png')))
put(14, Image.open(os.path.join(HERE, '..', 'outputs_standard', 'fairface', 'avg_all.png')))
out = os.path.join(HERE, '..', 'assets', 'atlas', 'faces_atlas.png')
A.save(out); print(os.path.abspath(out))
