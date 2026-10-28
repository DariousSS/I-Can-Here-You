# 在 TD 的 Textport 里运行：把万花筒放进你在隔音棉上新画的那个形状里，变成会随声音呼吸的云朵/史莱姆
# BLOB 留空 = 自动找（纹理是 sc_black、而且不在旧形状名单里的那一个）；如果提示找不到或找到多个，把形状名填在这里，例如 BLOB = 'item23'
BLOB = 'item4'
OLD = ['item4', 'item10', 'item11', 'item14', 'item15', 'item16', 'item17', 'item20', 'item21', 'item22']
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
p = op('/project1')
cand = []
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.op('parameters') is None or not hasattr(c.op('parameters').par, 'Texture'):
        continue
    cur = c.op('parameters').par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if (BLOB and c.name == BLOB) or (not BLOB and cur == '/project1/sc_black' and c.name not in OLD):
        cand.append((c, cur))
if len(cand) > 1:
    def _num(t):
        d = ''.join(ch for ch in t[0].name if ch.isdigit())
        return int(d) if d else -1
    cand.sort(key=_num)
    print('找到', len(cand), '个候选形状：', [c.name for c, t in cand], '-> 自动选最新画的一个：', cand[-1][0].name, '（选错了就把 BLOB = 填成想要的名字再运行）')
    cand = [cand[-1]]
if len(cand) != 1:
    print('没有找到候选形状（纹理是 sc_black、不在旧形状名单里）。请先在 Kantan 里画一个长方形，或在本脚本里填 BLOB = 形状名')
else:
    c, cur = cand[0]
    sc = c.op('script1')
    pts = [(q.x, q.y) for q in sc.points]
    w = max(q[0] for q in pts) - min(q[0] for q in pts)
    h = max(q[1] for q in pts) - min(q[1] for q in pts)
    asp = w / h if h > 0 else 1.78
    fresh = p.op('sc_blob') is None
    bl = p.op('sc_blob') or p.create(glslTOP, 'sc_blob')
    bl.inputConnectors[0].connect(p.op('castle_xf'))
    bl.par.outputresolution = 'custom'
    bl.par.resolutionw = 1920
    bl.par.resolutionh = 1080
    bl.par.vec0name = 'uB'
    bl.par.vec0valuex = 0.0
    bl.par.vec0valuey = 0.0
    bl.par.vec0valuez = asp
    bl.par.vec0valuew = 0.0
    bl.par.vec1name = 'uC'
    if fresh:                       # 重新运行时不覆盖你调好的圆心和大小
        bl.par.vec1valuex = 0.4     # 圆心（形状自己的 0~1 坐标，y 0 是下边）：0.4, 0.4 = 贴着盖子左上角；半圆就把圆心放在边上
        bl.par.vec1valuey = 0.4
        bl.par.vec1valuez = 1.6     # 大小倍数
    px = p.op('sc_blob_pixel')
    if px is not None:
        px.text = open(BASE + '/blob_shader.glsl', encoding='utf-8').read()
    bl.nodeX, bl.nodeY = 1500, -2800
    if cur != '/project1/sc_blob':
        p.store('sc_prev_blob', (c.name, cur))
    c.op('parameters').par.Texture = '/project1/sc_blob'
    c.op('parameters').par.Showtexture = True
    print('OK: 形状', c.name, '宽高比', round(asp, 2), '已接上 sc_blob（万花筒云朵）')
    print('接下来再运行一次 suitcase_setup.py，让它让云朵随声音和入侵变大变小')
