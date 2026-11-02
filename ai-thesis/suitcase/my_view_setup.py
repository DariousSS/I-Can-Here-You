# 在 TD 的 Textport 里运行：把"我的视角"的话放进 Kantan 里名字叫「我的视角」的形状，一句一句淡入淡出、循环。
# 句子写在 my_perspective.txt（一行一句，改了保存就行，下一轮自动读新的，不用重跑）。
# 新建 sc_my_txt（Text TOP）、sc_my（Level TOP）、sc_my_exec（Execute DAT）；把形状「我的视角」的纹理换成 sc_my（旧纹理记下来，my_view_undo.py 可还原）。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
SHAPE_NAME = '我的视角'
p = op('/project1')
hit = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    sp = c.op('parameters')
    if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() == SHAPE_NAME:
        hit = c
if hit is None:
    print('找不到名字叫', SHAPE_NAME, '的形状，没有改动')
else:
    pts = [(q.x, q.y) for q in hit.op('script1').points]
    asp = 1.3
    if pts:
        bw = max(q[0] for q in pts) - min(q[0] for q in pts)
        bh = max(q[1] for q in pts) - min(q[1] for q in pts)
        if bw > 1 and bh > 1:
            asp = bw / bh
    H = 480
    W = int(round(H * asp))
    t = p.op('sc_my_txt') or p.create(textTOP, 'sc_my_txt')
    t.par.outputresolution = 'custom'
    t.par.resolutionw, t.par.resolutionh = W, H
    t.par.text = ' '
    for k, v in (('fontsizex', 40), ('fontcolorr', 1.0), ('fontcolorg', 0.92), ('fontcolorb', 0.8), ('alignx', 'center'), ('aligny', 'center'), ('font', 'Georgia')):
        try:
            setattr(t.par, k, v)
        except Exception as e:
            print('设置', k, '失败（不影响）', repr(e)[:50])
    t.nodeX, t.nodeY = 2000, -4500
    lv = p.op('sc_my') or p.create(levelTOP, 'sc_my')
    lv.inputConnectors[0].connect(t)
    lv.par.opacity = 0.0
    lv.nodeX, lv.nodeY = 2200, -4500
    ex = p.op('sc_my_exec') or p.create(executeDAT, 'sc_my_exec')
    ex.nodeX, ex.nodeY = 2400, -4500
    ex.text = '''import textwrap, time

FILE = '__BASE__/my_perspective.txt'
FADE = 0.9               # 淡入淡出各多少秒
BASE_HOLD, CPS = 1.6, 14.0   # 每句停留 = BASE_HOLD + 字数 / CPS 秒
CHARS = 24               # 每行最多多少字符（字号变大就改小）

def _load():
    try:
        with open(FILE, encoding='utf-8') as f:
            L = [x.strip() for x in f if x.strip()]
        if L:
            return L
    except Exception:
        pass
    return ['(my_perspective.txt is empty)']

def onFrameEnd(frame):
    t, lv = op('/project1/sc_my_txt'), op('/project1/sc_my')
    if t is None or lv is None:
        return
    now = time.time()
    st = me.fetch('st', None)
    if st is None:
        st = {'i': -1, 't0': -99.0, 'dur': 0.0, 'L': _load()}
        me.store('st', st)
    if now - st['t0'] >= st['dur']:
        st['i'] += 1
        if st['i'] >= len(st['L']):
            st['L'] = _load()
            st['i'] = 0
        s = st['L'][st['i']]
        st['t0'] = now
        st['dur'] = FADE * 2 + BASE_HOLD + len(s) / CPS
        t.par.text = chr(10).join(textwrap.wrap(s, int(me.fetch('chars', CHARS))))
    e = now - st['t0']
    a = min(1.0, e / FADE, max(0.0, (st['dur'] - e) / FADE))
    lv.par.opacity = max(0.0, a)
'''.replace('__BASE__', BASE)
    ex.par.framestart = False
    ex.par.frameend = True
    ex.par.active = True
    ex.store('st', None)
    sp = hit.op('parameters')
    cur = sp.par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if cur != '/project1/sc_my':
        p.store('sc_prev_my', (hit.name, cur))
    sp.par.Texture = '/project1/sc_my'
    sp.par.Showtexture = True
    hit.par.render = True
    print('OK: 「我的视角」已放进形状', hit.name, '，宽高比', round(asp, 2), '，文字画布', W, 'x', H, '| 句子在 my_perspective.txt')
