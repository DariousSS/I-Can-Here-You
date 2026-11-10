# 在 TD 的 Textport 里运行：让"心跳"控制万花筒的扭曲（先运行 pulse_setup.py 接上耳夹/手指传感器，没有硬件也可以先用 pk_test 试）。
# 想法：心跳每跳一下，脸轻轻一抖；心率比"基准"快，脸越扭曲（带一点颜色分离）；心率慢下来，脸慢慢恢复。
#       基准 = 刚戴上后前 20 秒的平均心率，所以每个人起点一样，不看绝对数字。不给观众的情绪下判断，只是把身体的紧张变成画面。
# 新建节点（都在 /project1）：arr_pk（CHOP）、pk_warp_full（全屏万花筒 gz_tile 后面）、pk_warp_castle（城堡/纸箱万花筒 castle_tile 后面）、pk_exec
# 不改 gz_exec 等已有节点；只是把"吃 gz_tile / castle_tile 的节点"改成吃 pk_warp。撤销：运行 pulse_kaleido_undo.py
# Textport 里可用：
#   pk_test(75)    不接硬件，假装心率 75（再试 90、110 看扭曲变化；基准固定 70）
#   pk_real()      回到真实传感器
#   pk_base()      重新记基准（换一个观众时用，前 20 秒不扭曲）
#   pk_off() / pk_on()   关闭 / 打开效果
#   pk_status()    看心率、基准、扭曲程度
#   op('/project1').store('pk_gain', 12.0)   心率比基准快多少 bpm 就扭曲到最大（默认 12，越小越敏感）
p = op('/project1')

def mk(t, name, x, y):
    n = p.op(name) or p.create(t, name)
    n.nodeX, n.nodeY = x, y
    return n

k = mk(constantCHOP, 'arr_pk', -400, -1800)
for i, nm in enumerate(('tension', 'beat', 'base', 'bpm', 'present')):
    setattr(k.par, 'const%dname' % i, nm)
    setattr(k.par, 'const%dvalue' % i, 0.0)

SHADER = '''uniform vec2 uP;      // x = 紧张程度 0~1，y = 心跳一抖 0~1
uniform float uT;      // 时间
out vec4 fragColor;
vec2 mir(vec2 u) { return 1.0 - abs(1.0 - mod(u, 2.0)); }
void main() {
    vec2 uv = vUV.st;
    vec2 c = uv - 0.5;
    float T = clamp(uP.x, 0.0, 1.0);
    float B = clamp(uP.y, 0.0, 1.0);
    float a = 0.004 + 0.040 * T;                         // 扭曲幅度：平静时几乎看不出
    vec2 w = uv;
    w.x += a * sin(uv.y * 17.0 + uT * (0.9 + 1.6 * T));
    w.y += a * sin(uv.x * 13.0 - uT * (0.7 + 1.2 * T));
    w += c * (B * (0.012 + 0.020 * T));                  // 每次心跳：画面从中心轻轻鼓一下
    vec2 ca = c * (0.002 + 0.016 * T);                   // 越紧张，红蓝越分离
    float r = texture(sTD2DInputs[0], mir(w + ca)).r;
    vec4 g = texture(sTD2DInputs[0], mir(w));
    float bl = texture(sTD2DInputs[0], mir(w - ca)).b;
    float lift = 1.0 + 0.10 * B;
    fragColor = TDOutputSwizzle(vec4(r * lift, g.g * lift, bl * lift, g.a));
}
'''

def make_warp(name, src_name, x, y):
    src = p.op(src_name)
    if src is None:
        print('找不到', src_name, '，跳过', name)
        return None
    w = mk(glslTOP, name, x, y)
    w.inputConnectors[0].connect(src)
    pix = p.op(name + '_pixel')
    if pix is None:
        raise Exception('没找到 ' + name + '_pixel（GLSL 的像素着色器 DAT）')
    pix.text = SHADER
    w.par.vec0name = 'uP'
    w.par.vec0valuex.expr = "op('/project1/arr_pk')['tension'].eval()"
    w.par.vec0valuey.expr = "op('/project1/arr_pk')['beat'].eval()"
    w.par.vec1name = 'uT'
    w.par.vec1valuex.expr = "absTime.seconds % 600"
    done = p.fetch('pk_rewired', [])
    for n in p.children:                                   # 所有原本吃 src 的 TOP，改成吃 warp
        if n is w or n.family != 'TOP':
            continue
        for i, inp in enumerate(n.inputs):
            if inp is src:
                n.inputConnectors[i].connect(w)
                done.append((n.path, i, src.path))
    p.store('pk_rewired', done)
    return w

if p.fetch('pk_rewired', None) is None:
    p.store('pk_rewired', [])
wf = make_warp('pk_warp_full', 'gz_tile', 250, -1000)
wc = make_warp('pk_warp_castle', 'castle_tile', 750, -1300)

EXEC = '''import math
def onFrameEnd(frame):
    host = parent()
    w = op('/project1/arr_pulse')
    k = op('/project1/arr_pk')
    if w is None or k is None:
        return
    now = absTime.seconds
    s = host.fetch('pk_st', None) or {}
    if s.get('t', -1.0) > now + 0.5:
        s = {}                                            # 重新打开工程后计时从 0 开始，清掉旧状态
    dt = min(0.2, max(1e-3, now - s.get('t', now)))
    s['t'] = now
    fake = float(host.fetch('pk_fake', 0))
    on = host.fetch('pk_on', True)
    gain = max(1.0, float(host.fetch('pk_gain', 12.0)))
    base_secs = float(host.fetch('pk_base_secs', 20.0))
    if fake > 0:
        bpm, present = fake, True
        beat_age = now % (60.0 / fake)
        if s.get('base') is None:
            s['base'] = 70.0
    else:
        bpm = w['bpm'].eval()
        present = w['present'].eval() > 0.5 and 40.0 < bpm < 150.0
        bt = w['beat_t'].eval()
        beat_age = (now - bt) if (bt <= now and bt > -50) else 99.0
    target = 0.0
    if present:
        if s.get('base') is None:                         # 还在记基准：前 20 秒不扭曲
            s['bsum'] = s.get('bsum', 0.0) + bpm * dt
            s['bt'] = s.get('bt', 0.0) + dt
            if s['bt'] >= base_secs:
                s['base'] = s['bsum'] / s['bt']
        else:
            target = max(0.0, min(1.0, (bpm - s['base']) / gain))
    ten = s.get('ten', 0.0)
    tau = 2.0 if target > ten else 6.0                     # 紧张起来约 2 秒，恢复约 6 秒
    ten += (target - ten) * min(1.0, dt / tau)
    s['ten'] = ten
    beat = math.exp(-beat_age / 0.25) if present else 0.0
    if not on:
        ten, beat = 0.0, 0.0
    host.store('pk_st', s)
    k.par.const0value = ten
    k.par.const1value = beat
    k.par.const2value = s.get('base') or 0.0
    k.par.const3value = bpm if present else 0.0
    k.par.const4value = 1.0 if present else 0.0
    return
'''
ex = mk(executeDAT, 'pk_exec', -200, -1800)
ex.par.framestart = False
ex.par.frameend = True
ex.par.active = True
ex.text = EXEC

def pk_test(bpm=75):
    p.store('pk_fake', float(bpm))
    print('假心率 =', bpm, '（基准 70）。回到真实传感器：pk_real()')
def pk_real():
    p.store('pk_fake', 0)
    print('已回到真实传感器')
def pk_base():
    s = p.fetch('pk_st', None) or {}
    for key in ('base', 'bsum', 'bt', 'ten'):
        s.pop(key, None)
    p.store('pk_st', s)
    print('重新记基准：接下来 20 秒保持放松')
def pk_off():
    p.store('pk_on', False)
    print('效果已关闭')
def pk_on():
    p.store('pk_on', True)
    print('效果已打开')
def pk_status():
    k = op('/project1/arr_pk')
    print('扭曲程度 %.2f | 心跳 %.2f | 基准 %.1f | 心率 %.0f | 有信号 %d' % (k['tension'].eval(), k['beat'].eval(), k['base'].eval(), k['bpm'].eval(), k['present'].eval()))
import builtins
for _f in (pk_test, pk_real, pk_base, pk_off, pk_on, pk_status):
    setattr(builtins, _f.__name__, _f)
print('OK：心跳 -> 万花筒扭曲 已接好。没有硬件先试：pk_test(75)，再 pk_test(95)；看数字：pk_status()')
