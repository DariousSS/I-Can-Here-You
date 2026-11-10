# 在 TD 的 Textport 里运行：参考你的画（紫/蓝/橙的细线 + 灰蓝/品红泼墨斑点），做"手划过留下锋利的线，停下来溅一个泼墨，然后慢慢淡掉"。
# 新建（都在 /project1）：sk_init、sk_draw（GLSL，带反馈）、sk_fb（Feedback）、sk_bg、sk_out（最终画面）、sk_exec（读手、画线）
# 看画面：  op('/project1/sk_out').openViewer()
# 没有手也能试：  sk_demo(True)  假装有一根手指在画；  sk_demo(False) 关掉
# 映射到 Kantan：在被子的 Kantan 里新画一个形状，名字叫「线条区域」，再运行本脚本（或 sk_bind()），线条就只出现在这个形状里。
# 可调（Textport 里）：
#   op('/project1').store('sk_half', 2.5)     线条淡掉的半衰期（秒），越大留得越久
#   op('/project1').store('sk_width', 0.0022) 线宽（占画面高度的比例）
#   op('/project1').store('sk_flipy', True)   手上下反了就设 True；左右反了设 sk_flipx
#   op('/project1').store('sk_on', False)     关掉
# 撤销：运行 scribble_undo.py
p = op('/project1')
W, H = 1920, 1200
KANTAN = '/project1/sc_bedkantan'
SHAPE = '线条区域'

def mk(t, name, x, y):
    n = p.op(name) or p.create(t, name)
    n.nodeX, n.nodeY = x, y
    return n

SHADER = '''uniform vec4 uSeg0;
uniform vec4 uSeg1;
uniform vec4 uCol0;
uniform vec4 uCol1;
uniform vec4 uBlob;
uniform vec4 uBlobCol;
uniform vec4 uParam;
out vec4 fragColor;
float h11(float n) { return fract(sin(n * 127.1) * 43758.5453); }
float vn(float x) { float i = floor(x); float f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h11(i), h11(i + 1.0), f); }
float segd(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a; vec2 ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-8), 0.0, 1.0);
    return length(pa - ba * h);
}
void main() {
    vec2 uv = vUV.st;
    float Wd = uTDOutputInfo.res.z;
    float Ht = uTDOutputInfo.res.w;
    vec2 asp = vec2(Wd / Ht, 1.0);
    vec2 p = uv * asp;
    vec4 res = texture(sTD2DInputs[0], uv) * uParam.x;
    res = max(res - vec4(0.0015), vec4(0.0));
    if (uCol0.w > 0.0) {
        float d = segd(p, uSeg0.xy * asp, uSeg0.zw * asp);
        float a = 1.0 - smoothstep(uCol0.w, uCol0.w + 1.3 / Ht, d);
        res = res * (1.0 - a) + vec4(uCol0.rgb * a, a);
    }
    if (uCol1.w > 0.0) {
        float d = segd(p, uSeg1.xy * asp, uSeg1.zw * asp);
        float a = 1.0 - smoothstep(uCol1.w, uCol1.w + 1.3 / Ht, d);
        res = res * (1.0 - a) + vec4(uCol1.rgb * a, a);
    }
    if (uBlob.z > 0.0) {
        vec2 c = uBlob.xy * asp;
        float r = uBlob.z;
        float sd = uBlob.w;
        vec2 dd = p - c;
        float l = length(dd);
        float ang = atan(dd.y, dd.x);
        float rr = r * (0.80 + 0.40 * vn(ang * 2.2 + sd) + 0.20 * vn(ang * 7.0 + sd * 3.0));
        float a = 1.0 - smoothstep(rr * 0.96, rr, l);
        for (int i = 0; i < 16; i++) {
            float t = float(i) + sd;
            float an = h11(t * 1.31) * 6.2832;
            float dist = r * (1.35 + 2.4 * h11(t * 2.17));
            float rad = r * (0.04 + 0.13 * h11(t * 3.71));
            vec2 q = c + vec2(cos(an), sin(an)) * dist;
            a = max(a, 1.0 - smoothstep(rad * 0.9, rad, length(p - q)));
        }
        a *= uBlobCol.a;
        res = res * (1.0 - a) + vec4(uBlobCol.rgb * a, a);
    }
    fragColor = TDOutputSwizzle(res);
}
'''

init = mk(constantTOP, 'sk_init', -400, -2300)
init.par.outputresolution = 'custom'
init.par.resolutionw, init.par.resolutionh = W, H
init.par.colorr = init.par.colorg = init.par.colorb = 0.0
init.par.alpha = 0.0

dr = mk(glslTOP, 'sk_draw', -200, -2300)
dr.par.outputresolution = 'custom'
dr.par.resolutionw, dr.par.resolutionh = W, H
try:
    dr.par.format = 'rgba16float'
except Exception as e:
    print('sk_draw 16 位格式没设成功（线会有一点残影）：', repr(e)[:60])
fb = mk(feedbackTOP, 'sk_fb', -400, -2450)
fb.inputConnectors[0].connect(init)
fb.par.top = 'sk_draw'
dr.inputConnectors[0].connect(fb)
try:
    dr.seq.vec.numBlocks = 7
except Exception as e:
    print('sk_draw 的 vec 序列设置失败：', repr(e)[:80])
for i, nm in enumerate(('uSeg0', 'uSeg1', 'uCol0', 'uCol1', 'uBlob', 'uBlobCol', 'uParam')):
    setattr(dr.par, 'vec%dname' % i, nm)
px = p.op('sk_draw_pixel')
if px is None:
    raise Exception('没找到 sk_draw_pixel（GLSL 的像素着色器 DAT）')
px.text = SHADER

bg = mk(constantTOP, 'sk_bg', 0, -2450)
bg.par.outputresolution = 'custom'
bg.par.resolutionw, bg.par.resolutionh = W, H
bg.par.colorr, bg.par.colorg, bg.par.colorb, bg.par.alpha = 0.03, 0.0, 0.07, 1.0
out = mk(overTOP, 'sk_out', 0, -2300)
out.inputConnectors[0].connect(dr)
out.inputConnectors[1].connect(bg)

EXEC = r"""import math, random
HAND_LISTS = [['/project1/hand_tracking2/null2', '/project1/hand_tracking/null2'], ['/project1/hand_tracking2/null3']]
PAL = [(0.55, 0.22, 0.95), (0.45, 0.20, 0.90), (0.65, 0.30, 0.95), (0.40, 0.18, 0.85), (0.60, 0.28, 0.92)]      # 线条只用紫色（深浅不同）
BLOB = [((0.55, 0.65, 0.85), 0.78), ((0.80, 0.30, 0.80), 0.70), ((0.50, 0.30, 0.90), 0.65)]
def _tip(lst):
    n = None
    for pth in lst:
        n = op(pth)
        if n is not None:
            break
    if n is None:
        return None
    pts = list(n.points)
    if len(pts) <= 20:
        return None
    return (pts[8].x, pts[8].y)
def onFrameEnd(frame):
    host = parent()
    g = op('/project1/sk_draw')
    if g is None:
        return
    now = absTime.seconds
    S = host.fetch('sk_st', None) or {}
    if S.get('t', -1.0) > now + 0.5:
        S = {}
    dt = min(0.2, max(1e-3, now - S.get('t', now)))
    S['t'] = now
    on = host.fetch('sk_on', True)
    half = max(0.3, float(host.fetch('sk_half', 2.5)))
    wd = float(host.fetch('sk_width', 0.0022))
    fx, fy = host.fetch('sk_flipx', False), host.fetch('sk_flipy', False)
    demo = host.fetch('sk_demo', False)
    segs, cols = [(0, 0, 0, 0), (0, 0, 0, 0)], [(0, 0, 0, 0), (0, 0, 0, 0)]
    blob, bcol = (0, 0, 0, 0), (0, 0, 0, 0)
    for hi in range(2):
        H = S.setdefault('h%d' % hi, {})
        tip = None
        if on:
            if demo and hi == 0:
                tt = (now // 7.0) * 5.8 + min(now % 7.0, 5.8)
                tip = (0.5 + 0.38 * math.sin(tt * 0.9), 0.5 + 0.30 * math.sin(tt * 1.7 + 1.0))
            elif not demo:
                tip = _tip(HAND_LISTS[hi])
        if tip is not None:
            x, y = tip
            if fx: x = 1.0 - x
            if fy: y = 1.0 - y
            if H.get('last') is None or now - H.get('lt', -9.0) > 0.45:
                H['last'] = (x, y)
                H['lt'] = now
                H['col'] = random.choice(PAL)
                H['len'] = 0.0
                H['still'] = now
            elif now - H['lt'] >= 0.09:
                lx, ly = H['last']
                d = math.hypot(x - lx, y - ly)
                if d > 0.012:
                    segs[hi] = (lx, ly, x, y)
                    cols[hi] = H['col'] + (wd,)
                    H['len'] = H.get('len', 0.0) + d
                    H['last'] = (x, y)
                    H['still'] = now
                H['lt'] = now
            H['seen'] = now
            if H.get('len', 0.0) > 0.15 and now - H['still'] > 0.5 and now - S.get('stamp', -9.0) > 1.2:
                bc, ba = random.choice(BLOB)
                blob = (H['last'][0], H['last'][1], random.uniform(0.035, 0.075), random.random() * 50.0)
                bcol = bc + (ba,)
                S['stamp'] = now
                H['len'] = 0.0
        elif H.get('last') is not None and now - H.get('seen', -9.0) > 0.35:
            if H.get('len', 0.0) > 0.15 and now - S.get('stamp', -9.0) > 1.2:
                bc, ba = random.choice(BLOB)
                blob = (H['last'][0], H['last'][1], random.uniform(0.035, 0.075), random.random() * 50.0)
                bcol = bc + (ba,)
                S['stamp'] = now
            H['last'] = None
            H['len'] = 0.0
    host.store('sk_st', S)
    fade = 0.5 ** (dt / half)
    vals = [segs[0], segs[1], cols[0], cols[1], blob, bcol, (fade, 0, 0, 0)]
    for i, v in enumerate(vals):
        for j, ax in enumerate('xyzw'):
            setattr(g.par, 'vec%dvalue%s' % (i, ax), float(v[j]))
    return
"""
ex = mk(executeDAT, 'sk_exec', -200, -2450)
ex.par.framestart = False
ex.par.frameend = True
ex.par.active = True
ex.text = EXEC
for k, v in (('sk_on', True), ('sk_half', 2.5), ('sk_width', 0.0022), ('sk_flipx', False), ('sk_flipy', False), ('sk_demo', False)):
    if p.fetch(k, None) is None:
        p.store(k, v)

def sk_bind(shape=None, src='sk_draw'):
    """把 sk_out 贴到 Kantan 里指定名字的形状上（默认「线条区域」）。盒盖和被子两个 Kantan 都会找。例如：sk_bind('伤口')"""
    shape = shape or SHAPE
    roots = ['/project1/kantanMapper', '/project1/sc_bedkantan/kantanMapper']
    hits = []
    for r in roots:
        try:
            shapes = op(r + '/project/allShapes').findChildren(maxDepth=4)
        except Exception:
            continue
        for s in shapes:
            sp = s.op('parameters')
            if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() == shape:
                hits.append((r, sp))
    if not hits:
        print('两个 Kantan 里都没找到名字叫「' + shape + '」的形状：在 Kantan 里画一个并改好名字，再运行 sk_bind("名字")')
        return
    for r, sp in hits:
        sp.par.Texture = '/project1/' + src
        sp.par.Showtexture = True
        print('OK：' + r + ' 里形状「' + shape + '」的纹理 = /project1/' + src + ('（只有线条，透明底）' if src == 'sk_draw' else '（带深紫黑底）'))
def sk_res(w=960, h=1860):
    """改线条画面的分辨率，让它和形状的长宽比一致（线不会被压扁）。伤口是竖的：sk_res(960, 1860)；回到横的：sk_res(1920, 1200)"""
    for nm in ('sk_init', 'sk_draw', 'sk_bg'):
        o = p.op(nm)
        if o is not None:
            o.par.outputresolution = 'custom'
            o.par.resolutionw, o.par.resolutionh = int(w), int(h)
    print('线条画面分辨率 =', w, 'x', h)
def sk_demo(on=True):
    p.store('sk_demo', bool(on))
    print('假手指' + ('开' if on else '关'))
import builtins
for _f in (sk_bind, sk_res, sk_demo):
    setattr(builtins, _f.__name__, _f)
sk_bind()
print('OK：线条效果已建好。看画面：op("/project1/sk_out").openViewer()；没有手先试 sk_demo(True)')
