# 这是"找光点 + 按琴键讲秘密"的游戏逻辑，会被 game_td_setup.py 放进 TD 里的 sc_game_exec（Execute DAT）。__BASE__ / __ASPECT__ 由安装脚本替换。
import time, math, random, textwrap, subprocess, re
BASE = '__BASE__'
VOICE = BASE + '/voice/'
LID_ASPECT = __ASPECT__
SFX_VOL = 0.3
FLASH_R = 0.26                  # 手电筒半径（盖子高度的比例）
GLITCH = 0.9                    # 房间有多乱
HAND_X = (0.15, 0.85)           # 摄像头里手的移动范围对应整个盖子（越小越灵敏）
HAND_Y = (0.15, 0.85)
FLIP_X = False                  # 左右反了改 True
FLIP_Y = False                  # 上下反了改 True
# 不用改文件，也可以在 Textport 里运行时调：op('/project1/sc_game_exec').store('cfg', {'flip_x': True, 'flip_y': True, 'flash_r': 0.3, 'glitch': 0.8, 'hand_x': (0.2, 0.8), 'hand_y': (0.2, 0.8)})
def _c(k, d):
    c = me.fetch('cfg', None) or {}
    return c.get(k, d)
HINT_AFTER, REVEAL_AFTER = 28.0, 55.0
TELL_MAX, TELL_IDLE, TELL_FIRST = 4, 4.5, 10.0
TYPE_CPS, HOLD_SEC, TYPE_GAP = 18.0, 7.0, 0.8     # 一句一句打出来：每秒几个字、全部打完后留多久、两句之间停多久
INTRO = [
    "You live in this house with your family. To pay the bills, you rent out a room.",
    "A girl has just moved in. She keeps her door closed. She keeps a secret.",
    "Find the lights hidden in the house.",
    "Wave your hand to look around. Make a fist to catch a light. Press a key to listen.",
    "Press any key to begin.",
]
FONT_PX = 44
WRAP = 24
CLAP_MIN, CLAP_RATIO = 0.1, 6.0
NOTE_OFFSET = 1
WHITE_PC = (0, 2, 4, 5, 7, 9, 11)
BLACK_PC = (1, 3, 6, 8, 10)
D2 = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
SENT = [
    "We need to rent out a room.", "Someone is moving in!", "The stairs creak every night at ten.", "Why did she just drag her large suitcase up the stairs?",
    "What did she put in the fridge? I'm so curious.", "\u2026you won't believe it, there's a girl upstairs\u2026", "\u2026she doesn't talk much, does she?\u2026", "\u2026what is she doing up there all day?\u2026",
    "\u2026cultural background\u2026 completely different\u2026", "She says she's moved so many times.", "She put a little bell on her door.", "She told us: please don't go into her room.",
    "The bell is off when she's home. It's on when she's out.", "The bell was taped above the door. Not very firmly.", "She has gone out!", "The door is open. Just a little.",
    "The bell rang.", "It kept ringing. It wouldn't stop.", "Then the bell stopped.", "The door was shut again. Nobody said a word.",
    "Don't go into her room again.", "What do I do? I already told the child not to go into her room.", "She's so smart. I didn't even know opening a door could be recorded.", "I can't lose this income.",
    "I'm so busy at work. I really don't want to deal with this.", "I didn't think she'd actually tell Mom.", "She looked easy to push around.", "Why don't you go play at your friend's house today?",
    "Listen up. We're a family. We stick together.", "You must be mistaken.", "Going into her room? That never happened.", "It's just talking. It's not a big deal.",
    "She said: \"I'm in my own room.\"", "She has moved out at last.", "Another guest will come.", "The door is closed. The room is clean."
]
# 25 个黑键，从最低的黑键到最高的黑键："她"（那个女孩）的声音
BSENT = [
    "Mom says someone is moving in.", "She put a bell on her door? What?", "Why would anyone put a bell on a door?", "She told me not to go into her room.",
    "But she's out. How could she possibly know?", "I don't believe it.", "I watched her door when she was home.", "She opened it. She closed it. No bell.",
    "It must be broken. Or switched off.", "I stood at her door. I didn't open it.", "\u2026I wonder what's in there\u2026", "Mom said no. So I walked away.",
    "The bell never rang.", "She's out. Just a quick look.", "I only looked. I didn't touch anything.", "The bell is ringing!",
    "Why won't it stop?", "The door won't close.", "Please. Help me close it.", "Then it stopped. I couldn't breathe.",
    "She'll know. She always knows.", "She turned it off when she was home. She turned it on when she left.", "She came home. She looked at me.", "I'm scared.",
    "I just wanted to see."
]

def _play(name):
    try:
        subprocess.Popen(['afplay', '-v', str(SFX_VOL), VOICE + name + '.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def _new_day(G, now):
    G['dot'] = (random.uniform(0.08, 0.92), random.uniform(0.2, 0.8))
    G['day_start'] = now
    G['state'] = 'search'
    G['tell'] = None
    r = op('/project1/sc_room')
    if r is not None:
        r.par.file = BASE + '/game/room_day' + str(G['day'] + 1) + '.png'

def _hand(G, now):
    real = _real_hand(G)
    if real is not None:
        return real
    mh = me.fetch('hand', None)              # 假的手（测试用）：只有摄像头看不到真的手时才用
    if mh:
        return float(mh[0]), float(mh[1])
    return None

def _real_hand(G):
    for path in ('/project1/hand_tracking2/null2', '/project1/hand_tracking/null2', '/project1/hand_tracking2/null3'):
        n = op(path)
        if n is None:
            continue
        try:
            pts = list(n.points)
        except Exception:
            continue
        if len(pts) > 9:
            x, y = pts[9].x, pts[9].y
            if (x, y) == G.get('last_raw'):
                G['same'] = G.get('same', 0) + 1
            else:
                G['same'] = 0
                G['last_raw'] = (x, y)
                G['chg'] = G.get('chg', 0) + 1
            if G['same'] > 60:
                continue
            hx_, hy_ = _c('hand_x', HAND_X), _c('hand_y', HAND_Y)
            u = (x - hx_[0]) / (hx_[1] - hx_[0])
            v = (y - hy_[0]) / (hy_[1] - hy_[0])
            if _c('flip_x', FLIP_X):
                u = 1.0 - u
            if _c('flip_y', FLIP_Y):
                v = 1.0 - v
            return max(0.0, min(1.0, u)), max(0.0, min(1.0, v))
    return None

def _clap(G):
    if me.fetch('clap', False):
        me.store('clap', False)
        return True
    o = op('/project1/clap_in')
    if o is None:
        return False
    try:
        peak = float(abs(o.numpyArray()).max())
    except Exception:
        return False
    base = G['clap_base']
    G['clap_since'] += 1
    is_clap = peak > CLAP_MIN and peak > CLAP_RATIO * max(base, 0.003) and G['clap_since'] > 20
    if is_clap:
        G['clap_since'] = 0
        return True
    if peak < 3.0 * max(base, 0.003):
        G['clap_base'] = base * 0.98 + peak * 0.02
    return False

def _fist_now(G):
    # 握拳返回 True，张开返回 False，没有手的数据返回 None。四根手指里至少三根"指尖离手腕比指节根离手腕近得多"就算握拳
    if G.get('same', 0) > 60:
        return None
    try:
        gs_ = str(op('/project1/MediaPipe1').par.Gestures.eval()).lower()
    except Exception:
        gs_ = ''
    G['gest'] = gs_
    if _c('fist_gesture', True) and 'fist' in gs_:      # MediaPipe 自己的手势识别说是握拳（Closed_Fist）
        return True
    for path in ('/project1/hand_tracking2/null2', '/project1/hand_tracking/null2', '/project1/hand_tracking2/null3'):
        n = op(path)
        if n is None:
            continue
        try:
            pts = list(n.points)
        except Exception:
            continue
        if len(pts) < 21:
            continue
        w = pts[0]
        curled = 0
        rs = []
        for tip, mcp in ((8, 5), (12, 9), (16, 13), (20, 17)):
            dt = math.hypot(pts[tip].x - w.x, pts[tip].y - w.y)
            dm = math.hypot(pts[mcp].x - w.x, pts[mcp].y - w.y)
            r = dt / max(dm, 1e-6)
            rs.append(round(r, 2))
            if r < _c('fist_ratio', 1.35):
                curled += 1
        G['fist_dbg'] = rs
        return curled >= 3
    return None

def _grab(G):
    # 收集光点的动作：握拳（从张开变成握紧）。store('clap',True) 仍可假装触发；想继续用拍手：store('cfg',{'use_clap':True})
    if me.fetch('clap', False):
        me.store('clap', False)
        return True
    if _c('use_clap', False) and _clap(G):
        return True
    f = _fist_now(G)
    if f is None:
        G['fist_n'] = 0
        return False
    if f:
        G['fist_n'] = G.get('fist_n', 0) + 1
    else:
        G['fist_n'] = 0
        G['open_n'] = G.get('open_n', 10) + 1
    if f and G['fist_n'] == 2 and G.get('open_n', 10) >= 4:
        G['open_n'] = 0
        return True
    return False

def _note_index(n):
    # 返回 ('w', 白键序号 0~35) 或 ('b', 黑键序号 0~24)，范围外返回 None
    s = n - NOTE_OFFSET
    pc = s % 12
    oc = s // 12 - 3
    if pc in WHITE_PC:
        idx = oc * 7 + WHITE_PC.index(pc)
        return ('w', idx) if 0 <= idx <= 35 else None
    idx = oc * 5 + BLACK_PC.index(pc)
    return ('b', idx) if 0 <= idx <= 24 else None

def _keys(G):
    out = []
    k = me.fetch('key', None)
    if k is not None:
        me.store('key', None)
        ks = str(k)
        out.append(('b', int(ks[1:])) if ks.startswith('b') else ('w', int(ks)))
    gz = op('/project1/gz_exec')
    st = (gz.fetch('st', None) if gz is not None else None) or {}
    midi = st.get('midi') or {}
    prev = G['prev_notes']
    for name, v in midi.items():
        m = re.match(r'ch1n(\d+)$', name)
        if not m:
            continue
        if v > 0 and prev.get(name, 0) == 0:
            i = _note_index(int(m.group(1)))
            if i is not None:
                out.append(i)
    G['prev_notes'] = dict(midi)
    return out

def _add_told(G, text, now):
    T = G['tell']
    T['n'] += 1
    T['last'] = now
    start = now
    if T['told']:
        ptext, pt0 = T['told'][-1]
        start = max(now, pt0 + len(ptext) / _c('type_cps', TYPE_CPS) + TYPE_GAP)      # 排队：上一句打完、停一下，才打这一句
    T['told'].append((text, start))
    G['lit'][G['day']] = True
    sfx = T.setdefault('sfx', [])
    if 'kept ringing' in text or 'is ringing' in text:
        sfx.append((start, 'bell_stuck'))
    elif 'bell rang' in text:
        sfx.append((start, 'bell'))

def _press(G, key, now):
    T = G['tell']
    kind, idx = key
    if G['state'] == 'intro':
        _new_day(G, now)          # 观众按了一下琴键：封面消失，游戏开始
        return
    if G['state'] == 'tell' and T is not None and now >= T['t0'] and T['n'] < TELL_MAX:
        if kind == 'b' and 0 <= idx < len(BSENT):
            _add_told(G, BSENT[idx], now)
        elif kind == 'w' and 0 <= idx < len(SENT):
            _add_told(G, SENT[idx], now)
    elif G['state'] == 'search':
        G['hint_t'] = now

def _intro_text(wrap):
    out = []
    for s_ in INTRO:
        out.extend(textwrap.wrap(s_, wrap))
        out.append('')
    return chr(10).join(out).strip(chr(10))

def _show_cards(G):
    # 封面期间：把「日历」「光点数」两块牌子整个关掉（它们的黑色底会挡住封面）；游戏开始后再打开，同时关掉封面
    want = G['state'] != 'intro'
    if G.get('cards_on') == want:
        return
    G['cards_on'] = want
    try:
        for c in op('/project1/kantanMapper/project/allShapes').children:
            if c.op('parameters') is None or not hasattr(c.op('parameters').par, 'Name'):
                continue
            nm = str(c.op('parameters').par.Name.eval()).strip()
            if nm in ('日历', '光点数'):
                c.par.render = want
            elif nm == '封面':
                c.par.render = not want
    except Exception as e_:
        print('开关牌子失败：', repr(e_)[:80])

def _text(G, now):
    cal = []
    for i in range(7):
        if G['lit'][i]:
            cal.append(D2[i])
        elif i == G['day'] and G['state'] != 'end':
            cal.append('[' + D2[i] + ']')
        else:
            cal.append('..')
    lines = []
    T = G['tell']
    if G['state'] == 'intro':
        return '' if op('/project1/sc_intro') is not None else _intro_text(WRAP)
    if G['state'] == 'end':
        return ''
    if T is not None:
        body = []
        for text, t0 in T['told']:
            if now < t0:
                continue
            nshow = min(len(text), int((now - t0) * _c('type_cps', TYPE_CPS)))
            shown = text[:max(0, nshow)]
            if shown:
                body.append(textwrap.wrap(shown, WRAP))
        maxl = 11
        flat = []
        for b in body:
            flat.extend(b)
        flat = flat[-maxl:]
        lines.extend(flat)
        if T['n'] == 0 and now > T['t0']:
            lines.append('(press a key)' if int(now * 2) % 2 == 0 else '')
    elif G['state'] == 'search':
        seen_ = now - G['seen_t'] < 3.0
        near_ = seen_ and math.hypot((G['dot'][0] - G['hx']) * LID_ASPECT, G['dot'][1] - G['hy']) < _c('flash_r', FLASH_R) * 0.95
        if near_:
            lines.append(_c('fist_hint', 'Make a fist' + chr(10) + 'to catch the light.'))
        elif seen_:
            lines.append(_c('move_hint', 'Move your hand' + chr(10) + 'to find a light.'))
        else:
            lines.append(_c('search_hint', 'Hold your hand up to the camera' + chr(10) + 'to find a light.'))
    return chr(10).join(lines)

def _frame():
    now = time.time()
    p = op('/project1')
    G = me.fetch('G', None)
    if G is None:
        G = {'day': 0, 'week': 1, 'state': 'search', 'count': 0, 'lit': [False] * 7, 'tell': None, 'dot': (0.5, 0.5), 'day_start': now,
             'flash_t0': -9.0, 'hit': False, 'center': None, 'hx': 0.5, 'hy': 0.5, 'seen_t': -99.0, 'prev_notes': {}, 'clap_base': 0.01, 'clap_since': 999,
             'hint_t': -9.0, 'last_txt': None, 'state_t': now}
        _new_day(G, now)
        if _c('intro', True):
            G['state'] = 'intro'
            G['intro_t0'] = now
    dt_ = max(0.001, min(0.2, now - G.get('t_prev', now - 0.016)))
    G['t_prev'] = now
    G['fps'] = G.get('fps', 60.0) * 0.95 + (1.0 / dt_) * 0.05
    if now - G.get('hz_t0', now) >= 1.0:
        G['hand_hz'] = G.get('chg', 0) / (now - G['hz_t0'])
        G['chg'] = 0
        G['hz_t0'] = now
    G.setdefault('hz_t0', now)
    h = _hand(G, now)
    if h is not None:
        dist_ = math.hypot((h[0] - G['hx']) * LID_ASPECT, h[1] - G['hy'])
        tau_ = 0.006 + (_c('hand_tau', 0.02) - 0.006) * math.exp(-dist_ * 14.0)      # 手移得远（快）就几乎直接跟上；停着或微抖时才平滑
        k_ = 1.0 - math.exp(-dt_ / tau_)
        ox_, oy_ = G['hx'], G['hy']
        G['hx'] += (h[0] - G['hx']) * k_
        G['hy'] += (h[1] - G['hy']) * k_
        G['vx'] = G.get('vx', 0.0) * 0.8 + ((G['hx'] - ox_) / dt_) * 0.2
        G['vy'] = G.get('vy', 0.0) * 0.8 + ((G['hy'] - oy_) / dt_) * 0.2
        G['seen_t'] = now
    seen = now - G['seen_t'] < 3.0
    state = G['state']
    # --- 拍手（手电筒收紧） ---
    if _grab(G) and state == 'search' and now - G['flash_t0'] > 0.9:
        G['flash_t0'] = now
        dx, dy = (G['dot'][0] - G['hx']) * LID_ASPECT, G['dot'][1] - G['hy']
        G['hit'] = bool(seen and math.hypot(dx, dy) < _c('flash_r', FLASH_R) * 1.05)
        G['center'] = G['dot'] if G['hit'] else None
    if me.fetch('find', False) and state == 'search':
        me.store('find', False)
        G['hx'], G['hy'] = G['dot']
        G['seen_t'] = now
        G['flash_t0'] = now
        G['hit'] = True
        G['center'] = G['dot']
        seen = True
    # --- 手电筒动画 ---
    u = (now - G['flash_t0']) / 1.1
    sc = 1.0
    fx, fy = G['hx'], G['hy']
    lead_ = _c('hand_lead', 0.0)
    if lead_ > 0.0 and seen:       # 预判：按手的速度把圈往前多画一点，补偿摄像头数据更新慢的延迟
        fx = max(0.0, min(1.0, fx + G.get('vx', 0.0) * lead_))
        fy = max(0.0, min(1.0, fy + G.get('vy', 0.0) * lead_))
    if 0.0 <= u < 1.0:
        e = u / 0.35 if u < 0.35 else 1.0
        back = (u - 0.6) / 0.4 if u > 0.6 else 0.0
        sc = 1.0 - 0.78 * (1.0 - (1.0 - e) ** 3) + 0.78 * back * back
        if G['hit'] and G['center'] is not None and u > 0.18:
            k = min(1.0, (u - 0.18) / 0.2)
            fx = G['hx'] + (G['center'][0] - G['hx']) * k
            fy = G['hy'] + (G['center'][1] - G['hy']) * k
        if G['hit'] and state == 'search' and u > 0.38:
            G['state'] = state = 'tell'
            G['count'] = min(7, G['count'] + 1)
            G['tell'] = {'t0': now + 1.0, 'last': 0.0, 'n': 0, 'told': []}
            _play('found')
            G['hit'] = False
    R = _c('flash_r', FLASH_R) * sc
    # --- 琴键 ---
    for key in _keys(G):
        _press(G, key, now)
    # --- 开场介绍 ---
    if state == 'intro' and me.fetch('skip_intro', False):
        me.store('skip_intro', False)
        _new_day(G, now)
        state = G['state']
    # --- 讲述 ---
    T = G['tell']
    if T is not None:
        due = [x for x in T.get('sfx', []) if x[0] <= now]
        if due:
            T['sfx'] = [x for x in T['sfx'] if x[0] > now]
            for x in due:
                _play(x[1])
    if state == 'tell' and T is not None:
        if T['n'] == 0 and now - T['t0'] > TELL_FIRST:
            _add_told(G, random.choice(SENT), now)
        if T['told']:
            ltext, lt0 = T['told'][-1]
            over = now > lt0 + len(ltext) / _c('type_cps', TYPE_CPS) + _c('hold', HOLD_SEC)
            if over:
                if G['day'] >= 6:
                    G['state'] = state = 'end'
                    G['state_t'] = now
                else:
                    G['day'] += 1
                    _new_day(G, now)
                    state = G['state']
    if state == 'end' and now - G['state_t'] > 3.6:
        G['day'] = 0
        G['week'] += 1
        G['count'] = 0
        G['lit'] = [False] * 7
        _new_day(G, now)
        state = G['state']
    # --- 光点：只在手电筒里看得见 ---
    a = 0.0
    if state == 'search':
        d = math.hypot((G['dot'][0] - G['hx']) * LID_ASPECT, G['dot'][1] - G['hy'])
        el = now - G['day_start']
        if seen and d < _c('flash_r', FLASH_R) * 0.95:
            a = 0.55 + 0.45 * math.sin(now * 5.0)
        elif _c('hints', False) and el > REVEAL_AFTER:
            a = 0.5 + 0.4 * math.sin(now * 4.0)
        elif _c('hints', False) and el > HINT_AFTER:
            a = 0.10 + 0.10 * max(0.0, math.sin(now * 2.2))
        if me.fetch('show_dot', False):
            a = max(a, 0.5)
    # --- 写给盖子 ---
    lid = p.op('sc_gamelid')
    if lid is not None:
        lid.par.vec0valuex = _c('glitch', GLITCH)
        lid.par.vec0valuey = now % 1000.0
        lid.par.vec0valuez = LID_ASPECT
        lid.par.vec1valuex = fx
        lid.par.vec1valuey = fy
        lid.par.vec1valuez = R
        lid.par.vec1valuew = 1.0 if seen else 0.0
        lid.par.vec2valuex = G['dot'][0]
        lid.par.vec2valuey = G['dot'][1]
        lid.par.vec2valuez = a
    # --- 写给床上的第二台投影仪（sc_bedscene）：房间放大地图 + 木头手（跟着手电筒圈）+ 找到的光点（物品）亮起 ---
    bed = p.op('sc_bedscene')
    if bed is not None:
        blank = _c('bed_blank', False)
        found = state in ('tell', 'end')
        if found and G.get('bed_found_t') is None:
            G['bed_found_t'] = now % 1000.0
        elif not found:
            G['bed_found_t'] = None
        G['bed_da'] = G.get('bed_da', 0.0) + ((1.0 if found else 0.0) - G.get('bed_da', 0.0)) * min(1.0, dt_ * 3.0)
        G['bed_ha'] = G.get('bed_ha', 0.0) + ((1.0 if seen else 0.0) - G.get('bed_ha', 0.0)) * min(1.0, dt_ * 6.0)
        hide = 0.0 if blank else 1.0
        bed.par.vec0valuex = now % 1000.0
        bed.par.vec0valuey = 1.0 if _c('bed_flip', True) else 0.0
        bed.par.vec0valuez = 1920.0 / 1200.0
        bed.par.vec0valuew = _c('bed_angel', 0.0) * hide
        bed.par.vec1valuex, bed.par.vec1valuey = _c('bed_angel_pos', (0.5, 0.7))
        bed.par.vec1valuez = _c('bed_angel_size', 0.5)
        bed.par.vec1valuew = 1920.0 / 1080.0
        bed.par.vec2valuex, bed.par.vec2valuey = G['dot']
        bed.par.vec2valuez = G['bed_da'] * hide
        bed.par.vec2valuew = G['bed_found_t'] if G.get('bed_found_t') is not None else 0.0
        bed.par.vec3valuex, bed.par.vec3valuey = fx, fy
        bed.par.vec3valuez = G['bed_ha'] * hide
        bed.par.vec3valuew = max(0.0, min(1.0, 1.0 - sc))
        bed.par.vec4valuex = LID_ASPECT
        bed.par.vec4valuey = _c('bed_room_scale', 1.0)
        bed.par.vec4valuez = _c('bed_room_dim', 0.30) * hide
        bed.par.vec4valuew = R
        bed.par.vec5valuex = _c('bed_hand_size', 0.55)
        bed.par.vec5valuey = _c('bed_hand_bob', 0.012)
        bed.par.vec5valuez = 1.0 if _c('bed_room', False) else 0.0       # 默认不画房间（背景黑，之后用 Kantan 把光投到被子和杂物上）
    # --- 写给右墙 ---
    txt = p.op('sc_sub_txt')
    lv = p.op('sc_sub')
    if txt is not None and lv is not None:
        s = _text(G, now)
        if s != G.get('last_txt'):
            G['last_txt'] = s
            txt.par.text = s
            txt.par.fontsizex = FONT_PX
        lv.par.opacity = 1.0
    _show_cards(G)
    # --- 写给封面牌子（Kantan 里叫 封面 的形状） ---
    cov = p.op('sc_intro')
    if cov is not None:
        cv = _intro_text(30) if G['state'] == 'intro' else ' '
        if cv != G.get('last_cover'):
            G['last_cover'] = cv
            cov.par.text = cv
    # --- 写给日历牌子（Kantan 里叫 日历 的形状，和字幕分开） ---
    cal_t = p.op('sc_cal')
    if cal_t is not None:
        rows = []
        for i in range(7):
            if G['lit'][i]:
                rows.append(D2[i])
            elif i == G['day'] and G['state'] != 'end':
                rows.append('[' + D2[i] + ']')
            else:
                rows.append('..')
        cs2 = ' ' if G['state'] == 'intro' else chr(10).join(rows)
        if cs2 != G.get('last_cal'):
            G['last_cal'] = cs2
            cal_t.par.text = cs2
    # --- 写给光点数牌子 ---
    ctx = p.op('sc_count')
    if ctx is not None:
        cs_ = ' ' if G['state'] == 'intro' else str(G['count']) + ' / 7' + chr(10) + ' '.join(['*' if i < G['count'] else '.' for i in range(7)])
        if cs_ != G.get('last_count'):
            G['last_count'] = cs_
            ctx.par.text = cs_
    wu_ = me.fetch('watch', 0.0)
    if wu_ and wu_ < 1000000.0:
        wu_ = now + wu_          # store('watch', 6) = 从现在起监视 6 秒
        me.store('watch', wu_)
    if wu_ and now < wu_ and now - G.get('watch_t', 0) > 0.5:
        G['watch_t'] = now
        print('  [监视] 握拳?', _fist_now(G), '| 四指弯曲比', G.get('fist_dbg'), '| 手势识别', repr(G.get('gest')), '| 连续握拳帧', G.get('fist_n'), '张开帧', G.get('open_n'), '| 离光点', round(math.hypot((G['dot'][0] - G['hx']) * LID_ASPECT, G['dot'][1] - G['hy']), 2), '(要小于', round(_c('flash_r', FLASH_R) * 1.05, 2), ')', '| 状态', G['state'])
    if me.fetch('status', False):
        me.store('status', False)
        for pth in ('/project1/hand_tracking2/null2', '/project1/hand_tracking/null2', '/project1/hand_tracking2/null3'):
            nn = op(pth)
            try:
                print('  手的节点', pth, '|', '没有这个节点' if nn is None else ('点数 ' + str(len(list(nn.points)))))
            except Exception as e_:
                print('  手的节点', pth, '| 读取失败', repr(e_)[:60])
        print('状态', G['state'], '| 第', G['week'], '周 第', G['day'] + 1, '天 | 收集', G['count'], '/ 7 | 手(盖子坐标)', round(G['hx'], 2), round(G['hy'], 2), '看得到手' if seen else '没看到手', '| 光点', round(G['dot'][0], 2), round(G['dot'][1], 2), '| 原始手', G.get('last_raw'), '| 四指弯曲比', G.get('fist_dbg'), '(小于1.25算弯)', '| 游戏帧率', round(G.get('fps', 0)), '| 手数据每秒更新', round(G.get('hand_hz', 0), 1), '次', '| 游戏代码每帧耗时', round(G.get('ms', 0.0), 1), '毫秒')
    me.store('G', G)

def onFrameEnd(frame):
    try:
        t0_ = time.perf_counter()
        _frame()
        g_ = me.fetch('G', None)
        if g_ is not None:
            g_['ms'] = g_.get('ms', 0.0) * 0.9 + (time.perf_counter() - t0_) * 1000.0 * 0.1
    except Exception as e:
        msg = repr(e)[:200]
        if me.fetch('last_err', '') != msg:
            me.store('last_err', msg)
            print('sc_game_exec 出错：', msg)

def onStart():
    # 每次 TD 打开工程：把用不到的 MediaPipe 检测关掉（否则手数据每秒只有 8 次，光圈会卡），并回到封面
    try:
        mp = op('/project1/MediaPipe1')
        if mp is not None:
            for n in _c('mp_off', ('Detectobjects', 'Detectimages', 'Detectimageembeddings', 'Detectposes')):
                if hasattr(mp.par, n):
                    setattr(mp.par, n, False)
        me.store('G', None)
        print('sc_game_exec 启动：已关掉用不到的 MediaPipe 检测，游戏回到封面')
    except Exception as e:
        print('sc_game_exec 启动设置失败：', repr(e)[:100])
