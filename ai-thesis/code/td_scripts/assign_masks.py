# 在 TD 的 Textport 里运行：给"两个面具"和"两个小三角形"填上纹理
#  - 面具：你在 Kantan 里新画的、还没有城堡纹理的两个形状（自动认），x 更靠左的是 左面具(mask_L=标准脸)，靠右的是 右面具(mask_R=此刻的脸)
#  - 小三角形：名字在 audio_fx.json 的 tri_names 里（默认 Freeform16、Freeform17）-> castle_tri（可淡出的城堡纹理）
import json
KNOWN = ('/project1/castle_xf', '/project1/castle_tri', '/project1/castle_ball_tf', '/project1/scene_all', '/project1/scene_out', '/project1/hand_out', '/project1/mask_L', '/project1/mask_R')
CANVAS_AREA = 1920 * 1080
try:
    tri_names = json.load(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/audio_fx.json', encoding='utf-8')).get('tri_names', ['Freeform16', 'Freeform17'])
except Exception:
    tri_names = ['Freeform16', 'Freeform17']
shapes = []
for c in op('/project1/kantanMapper/project/allShapes').children:
    p = c.op('parameters')
    if p is None or not hasattr(p.par, 'Texture'):
        continue
    nm = str(p.par.Name.eval()) if hasattr(p.par, 'Name') else ''
    cur = p.par.Texture.eval()
    path = str(getattr(cur, 'path', cur))
    sc = c.op('script1')
    area, cx = 0.0, 0.0
    if sc is not None:
        pts = [(q.x, q.y) for q in sc.points]
        if pts:
            area = (max(q[0] for q in pts) - min(q[0] for q in pts)) * (max(q[1] for q in pts) - min(q[1] for q in pts))
            cx = (max(q[0] for q in pts) + min(q[0] for q in pts)) / 2.0
    shapes.append((nm, path, area, cx, p))
# 1) 小三角形 -> castle_tri
if op('/project1/castle_tri') is None or op('/project1/mask_L') is None:
    print('找不到 castle_tri / mask_L，请先重新运行 gaze_setup.py 安装')
else:
    did_tri = []
    for nm, path, area, cx, p in shapes:
        if nm in tri_names:
            p.par.Texture = '/project1/castle_tri'
            p.par.Showtexture = True
            did_tri.append(nm)
    print('小三角形（会在面具出现时淡出）:', did_tri if did_tri else '没有找到名字在 tri_names 里的形状 ' + str(tri_names))
    # 2) 面具：新画的、纹理还不是已知纹理、面积不大不小、也不是零的形状
    cand = [t for t in shapes if t[1] not in KNOWN and 200 < t[2] < 0.3 * CANVAS_AREA and t[0] not in tri_names]
    print('面具候选:', [(t[0], int(t[2])) for t in cand])
    if len(cand) < 2:
        print('找到的新形状不足 2 个。请先在 Kantan 里用 Freeform 工具沿两个面具的轮廓各画一个（别在里面点一下就完），再运行本脚本。')
    else:
        cand = sorted(cand, key=lambda t: -t[2])[:2]
        cand.sort(key=lambda t: t[3])
        left, right = cand[0], cand[1]
        left[4].par.Texture = '/project1/mask_L'
        left[4].par.Showtexture = True
        right[4].par.Texture = '/project1/mask_R'
        right[4].par.Showtexture = True
        print('左面具（标准脸）:', left[0], '| 右面具（此刻的脸）:', right[0])
