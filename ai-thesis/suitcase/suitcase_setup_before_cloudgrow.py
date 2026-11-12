# 在 TD 的 Textport 里运行：盖子上"卧室 <-> 万花筒"切换（第 2 步）。只新建 sc_ 开头的节点，并把"盖子形状"的纹理改成 sc_lid（可用 suitcase_undo.py 还原）
# 先在下面确认盖子形状的名字（上一步 shape_probe 里那个万花筒长方形，现在是 item5）
LID = 'item5'
RIGHT = 'item19'    # 右边一直变化的脸（右边盒子上的椭圆）
LEFTM = 'item18'    # 左边挂着的面具
CALM_MIN, CALM_MAX = 40.0, 70.0       # 平静持续多久（秒）
INV_MIN, INV_MAX = 15.0, 25.0         # 入侵持续多久（秒）
ROOM_SEC, ROOM_FADE = 25.0, 4.0       # 每个卧室停留多久 / 换房间淡入淡出多久（秒）
import os
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
p = op('/project1')
lid = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name == LID and c.op('parameters') is not None:
        lid = c
if lid is None:
    print('找不到形状', LID, '：请重新运行 shape_probe.py，看盖子现在叫什么，再改本脚本第一行')
else:
    pr = lid.op('parameters')
    sc = lid.op('script1')
    pts = [(q.x, q.y) for q in sc.points]
    x0, x1 = 960.0 + min(q[0] for q in pts), 960.0 + max(q[0] for q in pts)
    y0, y1 = 540.0 - max(q[1] for q in pts), 540.0 - min(q[1] for q in pts)
    prev = pr.par.Texture.eval()
    prev = str(getattr(prev, 'path', prev))
    if prev != '/project1/sc_lid':
        p.store('sc_prev_tex', prev)
    bedA = p.op('sc_bedA') or p.create(moviefileinTOP, 'sc_bedA')
    bedB = p.op('sc_bedB') or p.create(moviefileinTOP, 'sc_bedB')
    bedA.par.file = BASE + '/bedroom_v4_1.png'
    bedB.par.file = BASE + '/bedroom_v4_2.png'
    bx = p.op('sc_bed_x') or p.create(crossTOP, 'sc_bed_x')
    bx.inputConnectors[0].connect(bedA)
    bx.inputConnectors[1].connect(bedB)
    bx.par.cross = 0.0
    sl = p.op('sc_lid') or p.create(glslTOP, 'sc_lid')
    sl.inputConnectors[0].connect(bx)
    sl.inputConnectors[1].connect(p.op('castle_xf'))
    sl.par.outputresolution = 'custom'
    sl.par.resolutionw = 1920
    sl.par.resolutionh = 1080
    sl.par.vec0name = 'uR'
    sl.par.vec0valuex = 0.0       # Kantan 会把整张纹理拉伸进形状里，所以卧室要占满整张画面
    sl.par.vec0valuey = 0.0
    sl.par.vec0valuez = 1.0
    sl.par.vec0valuew = 1.0
    sl.par.vec1name = 'uS'
    sl.par.vec1valuex = 0.0
    px = p.op('sc_lid_pixel')
    if px is not None:
        px.text = open(BASE + '/lid_shader.glsl', encoding='utf-8').read()
    for i, n in enumerate((bedA, bedB, bx, sl)):
        n.nodeX, n.nodeY = 1500 + i * 200, -2000
    ex = p.op('sc_exec') or p.create(executeDAT, 'sc_exec')
    ex.text = '''
import time, random
CALM = (%f, %f)
INV = (%f, %f)
ROOM_SEC, ROOM_FADE = %f, %f
BASE = %r
ANG_CALM = 0.0      # 平时天使有多亮（0~1，0 = 平时完全看不见，只在报警那一句出现；想要一直淡淡地在就改成 0.5）
ANG_SIZE = 0.95     # 红色天使占形状高度的多少
ANG_WHITE = 0.8     # 白色天使出现时有多亮（0~1）

def onFrameEnd(frame):
    now = time.time()
    p = op('/project1')
    s = me.fetch('s', None)
    if s is None:
        s = {'phase': 'calm', 'next': now + random.uniform(*CALM), 'inv': 0.0, 'last': now, 'room': 0, 'room_next': now + ROOM_SEC, 'fade_t0': None, 'front': 'A'}
    dt = min(0.2, now - s['last'])
    s['last'] = now
    for k_ in ('inv', 'snd', 'wl', 'wbl'):      # 数字衰减到接近 0 时直接归零（太小的数写进参数会变成 1.8e308，把左面具冲白、拉扯条变绿）
        if abs(s.get(k_, 0.0)) < 0.0005:
            s[k_] = 0.0
    force = me.fetch('force', None)
    if force:
        me.store('force', None)
        s['phase'] = 'invade' if force == 'invade' else 'calm'
        s['next'] = now + (random.uniform(*INV) if force == 'invade' else random.uniform(*CALM))
    if now >= s['next'] and me.fetch('auto', False):          # 默认不再随机切换：由字幕按故事顺序决定什么时候入侵；想恢复随机就 store('auto', True)
        if s['phase'] == 'calm':
            s['phase'] = 'invade'
            s['next'] = now + random.uniform(*INV)
        else:
            s['phase'] = 'calm'
            s['next'] = now + random.uniform(*CALM)
    target = 1.0 if s['phase'] == 'invade' else 0.0
    s['inv'] += (target - s['inv']) * min(1.0, dt / 1.5)
    lid = p.op('sc_lid')
    if lid is not None:
        gt_ = me.fetch('gl_target', None)                     # 房间故障由字幕直接控制（{glitch1}/{glitch2}/{glitchoff}）；字幕没在管时才跟着入侵走
        if gt_ is None:
            gt_ = s['inv']
        s['gl'] = s.get('gl', 0.0) + (gt_ - s.get('gl', 0.0)) * min(1.0, dt / 0.35)
        lid.par.vec1valuex = s['gl']
        lid.par.vec1valuey = now %% 1000.0
    snd = 0.0
    try:
        a_ = (op('/project1/gz_exec').fetch('st', {}) or {}).get('sing_amp') or {}
        snd = max(float(a_.get('L', 0.0)), float(a_.get('R', 0.0)))
    except Exception:
        snd = 0.0
    s['snd'] = s.get('snd', 0.0) + (snd - s.get('snd', 0.0)) * min(1.0, dt / 0.12)
    try:                                                      # 弹钢琴（或用手演奏）时自动打开 TD 的声音，停了 10 秒后自动关；打击垫 3 仍然可以手动开关
        gst_ = op('/project1/gz_exec').fetch('st', None)
        if gst_ is not None:
            act_ = any(v_ > 0 for k_, v_ in (gst_.get('midi') or {}).items() if k_.startswith('ch1n'))
            if act_:
                s['key_t'] = now
                if not gst_.get('snd_on', False):
                    gst_['snd_on'] = True
                    s['auto_snd'] = True
            elif s.get('auto_snd') and now - s.get('key_t', 0.0) > 10.0:
                gst_['snd_on'] = False
                s['auto_snd'] = False
    except Exception:
        pass
    bl = p.op('sc_blob')
    if bl is not None:
        bl.par.vec0valuex = s['snd']
        bl.par.vec0valuey = now %% 1000.0
        bl.par.vec0valuew = s['inv']
    cl = p.op('sc_cloud')
    if cl is not None:
        cl.par.opacity = min(1.0, 0.15 + 0.85 * s['inv'] + 0.25 * s['snd'])
    fxc = p.op('sc_fx')
    if fxc is not None:
        g_ = 1.0
        if s['inv'] > 0.08:
            h_ = (((int(now * 14.0) * 2654435761) >> 8) & 255) / 255.0
            if h_ < 0.5 * s['inv']:
                g_ = 0.0
            elif h_ > 1.0 - 0.25 * s['inv']:
                g_ = 1.7
        fxc.par.gain = g_
    pl = p.op('sc_pull')
    if pl is not None:
        try:                                                  # 每帧重新读右脸 item19 和左面具 item18 当前的位置，所以你移动它们，拉扯跟着走
            bq_ = {}
            for c_ in op('/project1/kantanMapper/project/allShapes').children:
                if c_.name in ('item19', 'item18'):
                    pts_ = [(q_.x, q_.y) for q_ in c_.op('script1').points]
                    x0_, x1_ = 960.0 + min(q_[0] for q_ in pts_), 960.0 + max(q_[0] for q_ in pts_)
                    y0_, y1_ = 540.0 - max(q_[1] for q_ in pts_), 540.0 - min(q_[1] for q_ in pts_)
                    bq_[c_.name] = ((x0_ + x1_) / 2.0 / 1920.0, 1.0 - (y0_ + y1_) / 2.0 / 1080.0, (y1_ - y0_) / 2.0 / 1080.0)
            if len(bq_) == 2:
                pl.par.vec0valuex, pl.par.vec0valuey = bq_['item19'][0], bq_['item19'][1]
                pl.par.vec0valuez, pl.par.vec0valuew = bq_['item18'][0], bq_['item18'][1]
                pl.par.vec1valuex, pl.par.vec1valuey = bq_['item19'][2], bq_['item18'][2]
        except Exception:
            pass
        pl.par.vec1valuez = s['inv'] * (0.7 + 0.3 * s['snd'])
        pl.par.vec1valuew = now %% 1000.0
    ag = p.op('sc_angel')
    if ag is not None:
        al_ = me.fetch('alarm', None)                         # 字幕那一句带 {alarm} 时，字幕引擎会写入 (开始时间, 结束时间)
        tg_ = 1.0 if (al_ and al_[0] <= now <= al_[1]) else 0.0
        a0_ = s.get('alarm', 0.0)
        a0_ += (tg_ - a0_) * min(1.0, dt / (0.10 if tg_ > a0_ else 2.5))     # 上升很快（突然），回落很慢
        s['alarm'] = a0_
        try:                                                  # 每帧读 item4（天使所在）和 item5（行李箱盖子）的位置，让瞳孔盯着盖子
            bq2_ = {}
            for c_ in op('/project1/kantanMapper/project/allShapes').children:
                if c_.name in ('item4', 'item5'):
                    pts_ = [(q_.x, q_.y) for q_ in c_.op('script1').points]
                    bq2_[c_.name] = (min(q_[0] for q_ in pts_), max(q_[0] for q_ in pts_), min(q_[1] for q_ in pts_), max(q_[1] for q_ in pts_))
            if len(bq2_) == 2:
                ax0_, ax1_, ay0_, ay1_ = bq2_['item4']
                lx0_, lx1_, ly0_, ly1_ = bq2_['item5']
                ag.par.vec0valuex = (ax1_ - ax0_) / max(1.0, ay1_ - ay0_)
                ag.par.vec1valuex = ((lx0_ + lx1_) / 2.0 - ax0_) / max(1.0, ax1_ - ax0_)
                ag.par.vec1valuey = ((ly0_ + ly1_) / 2.0 - ay0_) / max(1.0, ay1_ - ay0_)
        except Exception:
            pass
        ag.par.vec0valuey = now %% 1000.0
        wt_, wbt_ = me.fetch('wa', 0.0), me.fetch('wb', 0.0)          # 白色天使：出现 / 放大（由字幕的 {white} {whitebig} {whiteoff} 控制）
        s['wl'] = s.get('wl', 0.0) + (wt_ - s.get('wl', 0.0)) * min(1.0, dt / (0.6 if wt_ > s.get('wl', 0.0) else 1.2))
        s['wbl'] = s.get('wbl', 0.0) + (wbt_ - s.get('wbl', 0.0)) * min(1.0, dt / 0.5)
        ag.par.vec0valuez = a0_
        ag.par.vec0valuew = max(ANG_CALM, ANG_WHITE * s['wl'], a0_)
        ag.par.vec1valuew = s['wl'] * (0.28 + 0.30 * s['wbl'])      # 白色天使的眼睛睁开一点（放大时再多一点），不变红
        sw_ = 0.55 + 0.35 * s['wbl']
        ag.par.vec1valuez = sw_ * (1.0 - a0_) + ANG_SIZE * (1.0 + 0.2 * a0_) * a0_
    ml = p.op('sc_maskL')
    if ml is not None:
        ml.par.opacity = s['inv']
    mr = p.op('sc_maskR')
    if mr is not None:
        mr.par.opacity = 1.0
    if s['fade_t0'] is None and now >= s['room_next'] and s['phase'] == 'calm':
        s['room'] = (s['room'] + 1) %% 5
        hidden = p.op('sc_bedB') if s['front'] == 'A' else p.op('sc_bedA')
        hidden.par.file = BASE + '/bedroom_v4_%%d.png' %% (s['room'] + 1)
        s['fade_t0'] = now
    bx = p.op('sc_bed_x')
    if s['fade_t0'] is not None and bx is not None:
        f = min(1.0, (now - s['fade_t0']) / ROOM_FADE)
        bx.par.cross = f if s['front'] == 'A' else 1.0 - f
        if f >= 1.0:
            s['front'] = 'B' if s['front'] == 'A' else 'A'
            s['fade_t0'] = None
            s['room_next'] = now + ROOM_SEC
    me.store('s', s)
''' % (CALM_MIN, CALM_MAX, INV_MIN, INV_MAX, ROOM_SEC, ROOM_FADE, BASE)
    ex.par.frameend = True
    ex.par.active = True
    ex.nodeX, ex.nodeY = 1500, -2200
    pr.par.Texture = '/project1/sc_lid'
    pr.par.Showtexture = True
    gate = p.op('sc_maskL') or p.create(levelTOP, 'sc_maskL')      # 左面具：平时空白，入侵时才出现右边那张脸
    gate.inputConnectors[0].connect(p.op('mask_R'))
    gate.par.opacity = 0.0
    gate.nodeX, gate.nodeY = 1500, -2600
    sv_, so_ = p.op('snd_vol'), p.op('snd_out')              # 声音故障：在 snd_vol 和 snd_out 之间插一个 sc_fx，入侵时让声音断断续续、偶尔爆响
    if sv_ is not None and so_ is not None:
        fxc = p.op('sc_fx') or p.create(mathCHOP, 'sc_fx')
        fxc.inputConnectors[0].connect(sv_)
        so_.inputConnectors[0].connect(fxc)
        fxc.par.gain = 1.0
        fxc.nodeX, fxc.nodeY = 1900, -2600
    gateR = p.op('sc_maskR') or p.create(levelTOP, 'sc_maskR')    # 右边的脸：入侵时淡出（因为它"搬"到了左边）
    gateR.inputConnectors[0].connect(p.op('mask_R'))
    gateR.par.opacity = 1.0
    gateR.nodeX, gateR.nodeY = 1700, -2600
    prev2 = p.fetch('sc_prev_tex2', {})
    for c2 in op('/project1/kantanMapper/project/allShapes').children:
        for nm_, tex_ in ((RIGHT, '/project1/sc_maskR'), (LEFTM, '/project1/sc_maskL')):
            if c2.name == nm_ and c2.op('parameters') is not None:
                q_ = c2.op('parameters').par
                cur_ = q_.Texture.eval()
                cur_ = str(getattr(cur_, 'path', cur_))
                if cur_ != tex_:
                    prev2[nm_] = cur_
                q_.Texture = tex_
                q_.Showtexture = True
                print(nm_, ':', cur_, '->', tex_)
    p.store('sc_prev_tex2', prev2)
    print('OK: 盖子', LID, '范围 x', int(x0), '-', int(x1), ' y', int(y0), '-', int(y1), '已改成 sc_lid（卧室 <-> 万花筒）')
    print('马上看一下：盖子上应该是简笔画卧室。想立刻看入侵：')
    print("  op('/project1/sc_exec').store('force','invade')    # 变万花筒")
    print("  op('/project1/sc_exec').store('force','calm')      # 变回卧室")
