# 在 TD 的 Textport 里运行（一次）：把「云朵」形状接回万花筒云朵（sc_blob），贴在卧室边上，
# 随着第几天（被窥探的隐私变多）慢慢变大，空气钢琴弹得越多它再鼓得越大、越抖。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
SHAPE_NAME = '云朵'            # Kantan 里这个形状的名字
CX, CY, SIZE = 0.5, 1.0, 1.4
SIZE_START = 0.45              # 第 1 天的大小倍数（越小越小）；第 7 天长到上面的 SIZE   # 云朵圆心（形状自己的 0~1 坐标）：1,0.5 = 平边在右边，贴着右边的卧室；0,0.5 = 平边在左；大小倍数 1.0、大小倍数
AUTO_CORNER = True            # True = 自动把云朵圆心放在房间的左下角（贴着房间左边和下边）；想手动指定就改成 False 并改上面的 CX, CY
p = op('/project1')
sh = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    q = c.op('parameters')
    if q is not None and hasattr(q.par, 'Name') and str(q.par.Name.eval()).strip() == SHAPE_NAME:
        sh = c
if sh is None:
    print('没找到名字叫', SHAPE_NAME, '的形状')
else:
    pts = [(q.x, q.y) for q in sh.op('script1').points]
    w = max(a[0] for a in pts) - min(a[0] for a in pts)
    h = max(a[1] for a in pts) - min(a[1] for a in pts)
    bl = p.op('sc_blob') or p.create(glslTOP, 'sc_blob')
    bl.inputConnectors[0].connect(p.op('castle_xf'))
    bl.par.outputresolution = 'custom'
    bl.par.resolutionw, bl.par.resolutionh = 1920, 1080
    bl.par.vec0name, bl.par.vec1name = 'uB', 'uC'
    bl.par.vec0valuez = w / h if h > 0 else 1.0
    def _box(s_):                                              # 形状在 1920x1080 画布上的范围（y 向下）
        q_ = [(a.x, a.y) for a in s_.op('script1').points]
        return 960.0 + min(a[0] for a in q_), 960.0 + max(a[0] for a in q_), 540.0 - max(a[1] for a in q_), 540.0 - min(a[1] for a in q_)
    rx0, rx1, ry0, ry1 = _box(sh)
    room = None
    for c_ in op('/project1/kantanMapper/project/allShapes').children:
        if c_.name == 'item5':
            room = c_
    if room is not None and AUTO_CORNER:                       # 云朵圆心 = 房间（盖子）的左下角，换算成云朵形状自己的 0~1 坐标（y 0 在下）
        ax0, ax1, ay0, ay1 = _box(room)
        CX = min(1.0, max(0.0, ((ax0 + ax1) / 2.0 - rx0) / max(1.0, rx1 - rx0)))      # 圆心 = 房间最下面那条边的正中间
        CY = min(1.0, max(0.0, (ry1 - ay1) / max(1.0, ry1 - ry0)))
        print('云朵圆心自动放在房间下边正中：', round(CX, 2), round(CY, 2), '（云朵形状范围 x', int(rx0), '-', int(rx1), ' y', int(ry0), '-', int(ry1), '；房间 x', int(ax0), '-', int(ax1), ' y', int(ay0), '-', int(ay1), '）')
    p.store('cloud_sz', (SIZE_START, SIZE))
    bl.par.vec1valuex, bl.par.vec1valuey, bl.par.vec1valuez, bl.par.vec1valuew = CX, CY, SIZE_START, 1.0     # 最后的 1.0 = 半圆，平边朝上，贴在房间下边，向下长
    px = p.op('sc_blob_pixel')
    if px is not None:
        px.text = open(BASE + '/blob_shader.glsl', encoding='utf-8').read()
    sh.op('parameters').par.Texture = '/project1/sc_blob'
    sh.op('parameters').par.Showtexture = True
    sh.par.render = True
    ex = p.op('sc_cloud_exec') or p.create(executeDAT, 'sc_cloud_exec')
    ex.text = '''
import time
def onFrameEnd(frame):
    p = op('/project1')
    ge = op('/project1/sc_game_exec')
    G = ge.fetch('G', None) if ge is not None else None
    if not G:
        return
    st = p.fetch('cloud_st', None) or {'extra': 0.0, 'g': 0.0, 't': time.time()}
    now = time.time()
    dt = min(0.2, now - st['t'])
    st['t'] = now
    base = 0.20 + 0.70 * G['day'] / 6.0                      # 第 1 天很小，第 7 天最大（向下长，把下面的字遮住）
    if G['state'] == 'intro':
        base = 0.0
    try:
        gst = op('/project1/gz_exec').fetch('st', None) or {}
        act = any(v > 0 for k, v in (gst.get('midi') or {}).items() if k.startswith('ch1n'))
    except Exception:
        act = False
    st['extra'] = min(0.25, st['extra'] + 0.08 * dt) if act else max(0.0, st['extra'] - 0.01 * dt)     # 弹琴时多鼓一点，停了慢慢缩回
    tgt = min(1.0, base + st['extra'])
    st['g'] += (tgt - st['g']) * min(1.0, dt / 1.5)
    p.store('cloud_st', st)
    sz = p.fetch('cloud_sz', None)
    b_ = p.op('sc_blob')
    if sz and b_ is not None:
        b_.par.vec1valuez = sz[0] + (sz[1] - sz[0]) * (G['day'] / 6.0)      # 第几天越往后，云朵的大小倍数越大
    p.store('cloud_grow', st['g'])
    return
'''
    ex.par.active = True
    ex.par.framestart = False
    ex.par.frameend = True
    print('OK：形状', sh.name, '（', SHAPE_NAME, '）已接上云朵。接着请再运行一次 suitcase_setup.py（让它用新的变大规则）')
