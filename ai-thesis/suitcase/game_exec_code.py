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
END_ANGEL = 9.0                                   # 结尾：巨大的天使 + 祝贺的话 出现多久（秒），之后一下子消失，开始红字结算
CONGRATS = 'Congratulations.' + chr(10) + 'You found her secret.'
SUM_CPS, SUM_HOLD = 45.0, 8.0                      # 结算：每秒打几个字、全部打完后停多久
TYPE_CPS, HOLD_SEC, TYPE_GAP = 18.0, 7.0, 0.8     # 一句一句打出来：每秒几个字、全部打完后留多久、两句之间停多久
INTRO = [
    "You live in this house with your family. To pay the bills, you rent out a room.",
    "A girl has just moved in. She keeps her door closed. She keeps a secret.",
    "Find the lights hidden in the house.",
    "Wave your hand to look around. Hold still on a light to catch it.",
    "Each page of this book holds a piece of the story. Catch a light, then wave your hand to turn the page.",
]
FONT_PX = 44
WRAP = 24
CLAP_MIN, CLAP_RATIO = 0.1, 6.0
NOTE_OFFSET = 1
WHITE_PC = (0, 2, 4, 5, 7, 9, 11)
BLACK_PC = (1, 3, 6, 8, 10)
D2 = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
SENT = [
    'We need to rent out a room.',
    'Someone is moving in!',
    "It kept ringing. It wouldn't stop.",
    'Why did she just drag her large suitcase up the stairs?',
    "What did she put in the fridge? I'm so curious.",
    "…you won't believe it, there's a girl upstairs…",
    "…she doesn't talk much, does she?…",
    '…what is she doing up there all day?…',
    '…cultural background… completely different…',
    'I opened her wardrobe. She hid it well, but I still found it.',
    'She put a little bell on her door.',
    "She told us: please don't go into her room.",
    "The bell is off when she's home. It's on when she's out.",
    'The bell was taped above the door. Not very firmly.',
    'She has gone out!',
    'The door is open. Just a little.',
    'The bell rang.',
    'I went through the trash in her room. She really does have a secret! Gotcha!',
    'Then the bell stopped.',
    'The door was shut again. Nobody said a word.',
    "Don't go into her room again.",
    'What do I do? I already told the child not to go into her room.',
    "She's so smart. I didn't even know opening a door could be recorded.",
    "I can't lose this income.",
    "I'm so busy at work. I really don't want to deal with this.",
    "I didn't think she'd actually tell Mom.",
    'She looked easy to push around.',
    "Why don't you go play at your friend's house today?",
    "Listen up. We're a family. We stick together.",
    'You must be mistaken.',
    'Going into her room? That never happened.',
    "It's just talking. It's not a big deal.",
    "She said: \"I'm in my own room.\"",
    'She has moved out at last.',
    'Another guest will come.',
    'The door is closed. The room is clean.',
]
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

MY_FILE = BASE + '/my_perspective.txt'
MY_MAP = [   # (他们那句话里的一小段, 对应「我的视角」第几句（my_perspective.txt 的第几行，从 1 开始）)
    ('large suitcase', 1), ('went through the trash', 2), ('opened her wardrobe', 2), ('little bell on her door', 3), ('please don', 4),
    ('The bell is off when', 5), ('taped above the door', 5), ('She has gone out', 6), ('door is open', 7), ('The bell rang', 8), ('kept ringing', 8),
    ('could be recorded', 9), ('girl upstairs', 10), ('talk much', 10), ('doing up there', 10), ('in my own room', 10), ('You must be mistaken', 11),
    ('never happened', 11), ('Then the bell stopped', 12), ('Nobody said a word', 12), ('just talking', 13), ('cultural background', 14),
    ('moved out at last', 15), ('room is clean', 15), ('Another guest', 16), ('lose this income', 17), ('deal with this', 17),
    ('told me not to go', 4), ('bell on her door? What', 3), ('Why would anyone put a bell', 3), ('switched off', 5), ('turned it off when', 5),
    ('Just a quick look', 6), ('only looked', 7), ('bell is ringing', 8), ("Why won't it stop", 8), ("ll know", 9),
]

def _my_line(sentence):
    # 找出和这句话对应的「我的视角」，没有对应就返回 None
    for key_, n_ in MY_MAP:
        if key_ in sentence:
            try:
                with open(MY_FILE, encoding='utf-8') as f_:
                    L_ = [x_.strip() for x_ in f_ if x_.strip()]
                return L_[n_ - 1] if 0 < n_ <= len(L_) else None
            except Exception:
                return None
    return None

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
    if _book_on():
        start = max(start, now + _c('book_flip_s', 1.3) * 0.8)       # 书翻到一半，新的字才开始出现
    T['told'].append((text, start))
    G.setdefault('week_told', []).append(text)
    G['lit'][G['day']] = True
    sfx = T.setdefault('sfx', [])
    if 'kept ringing' in text or 'is ringing' in text:
        sfx.append((start, 'bell_stuck'))
    elif 'bell rang' in text:
        sfx.append((start, 'bell'))

def _book_on():
    # 听故事时是否用"翻页动画"（线框书翻页）。默认关：书只当柜门上的封面用。想恢复翻页：cfg book_play=True
    return op('/project1/sc_book') is not None and _c('book_mode', True) and _c('book_play', True)

def _cover_on():
    # 柜门上的书本封面（sc_book 的封面模式）：游戏开始时先出现，等观众"开门"（或几秒后自动）才显示游戏规则
    return op('/project1/sc_book') is not None and _c('book_mode', True) and _c('cover_book', True)

def _bed_shape(G, key, name, now, kan='/project1/sc_bedkantan/kantanMapper'):
    # 在 Kantan 里按名字找形状（默认是被子的 sc_bedkantan，kan 换成 '/project1/kantanMapper' 就是盖子那份），找到后记住路径；没找到每 3 秒再试一次
    if G.get(key) is None and now - G.get(key + '_try', -9.0) > 3.0:
        G[key + '_try'] = now
        root_ = op(kan + '/project/allShapes')
        if root_ is not None:
            for c_ in root_.findChildren(maxDepth=4):
                sp_ = c_.op('parameters')
                if sp_ is not None and hasattr(sp_.par, 'Name') and str(sp_.par.Name.eval()).strip() == name:
                    G[key] = c_.path
    return op(G[key]) if G.get(key) else None

def _pages(day):
    # 这一天书里的页：故事按时间顺序切成 7 段，每天的白键（屋子里的声音）和黑键（她）交替排成页。想自己定：cfg day_pages = {天号 0~6: [('w', 编号 0~35) 或 ('b', 编号 0~24), ...]}
    dp_ = _c('day_pages', None)
    if dp_ and day in dp_:
        return list(dp_[day])
    w0_, w1_ = round(36 * day / 7.0), round(36 * (day + 1) / 7.0)
    b0_, b1_ = round(25 * day / 7.0), round(25 * (day + 1) / 7.0)
    W_ = [('w', i_) for i_ in range(w0_, w1_)]
    B_ = [('b', i_) for i_ in range(b0_, b1_)]
    out_ = []
    for i_ in range(max(len(W_), len(B_))):
        if i_ < len(W_):
            out_.append(W_[i_])
        if i_ < len(B_):
            out_.append(B_[i_])
    return out_

def _wave(G, now):
    # 挥手翻页：手在画面里、左右移动得够快（vx 是手每秒横向移动的盖子宽度），并且离上次翻页超过 1.2 秒
    if now - G.get('seen_t', -9.0) > 0.4 or now - G.get('wave_t', -9.0) < _c('wave_gap', 1.2):
        return False
    return abs(G.get('vx', 0.0)) > _c('wave_v', 1.6)

def _book_turn(G, kind, idx, sentence, now):
    # 按下琴键：书翻一页（线框动画，sc_book 画）。中间偏左的键 → 从左往右翻；偏右的键 → 从右往左翻。字不在书里，仍然显示在原来的两个长方形（右 = 她们的话，左 = 我的视角）
    if not _book_on():
        return
    left_half = idx < (18 if kind == 'w' else 13)
    d_ = -1.0 if left_half else 1.0
    if _c('book_fixed_dir', True):
        d_ = -1.0                                  # 衣柜像一本从左往右翻开的书：每一页都是从左往右翻
    if _c('book_dir_flip', False):
        d_ = -d_
    G['bk'] = {'t0': now, 'dir': d_, 'p': 0.0}

def _set_my(G, sentence):
    # 这一句对应的「我的视角」：和右边那句同时出现（直接出现，不打字），一直停到右边换成下一句，再一起消失。没有对应的就是空
    T_ = G.get('tell')
    if not T_ or not T_.get('told'):
        return
    G['my_prev'] = G.get('my')
    G['my'] = (_my_line(sentence), T_['told'][-1][1])

def _press(G, key, now):
    T = G['tell']
    kind, idx = key
    if G['state'] == 'intro':
        if _cover_on() and not G.get('door_open'):
            if _c('cover_anykey', False):
                G['door_open'] = True     # 想让任意琴键都能开门：cfg cover_anykey=True；默认只认空格键（键盘回调里存 door_open），琴键不会误触发
            return
        return                    # 规则显示期间，按键和手都不会让游戏提前开始（只靠 intro_auto_s 的计时，默认 10 秒）
    if G['state'] == 'tell' and T is not None and now >= T['t0'] and T['n'] < TELL_MAX and not T.get('closed'):
        if _c('key_wait', True) and T['told']:
            lt_, l0_ = T['told'][-1]
            if now < l0_ + len(lt_) / _c('type_cps', TYPE_CPS) + 0.6:
                return                  # 上一句还在打：先忽略这次按键，一个键对应一句话才分得清（想关掉：cfg key_wait=False）
        if kind == 'b' and 0 <= idx < len(BSENT):
            _add_told(G, BSENT[idx], now)
            G['piano'] = (2, idx, now)
            _set_my(G, BSENT[idx])
            _book_turn(G, 'b', idx, BSENT[idx], now)
        elif kind == 'w' and 0 <= idx < len(SENT):
            _add_told(G, SENT[idx], now)
            G['piano'] = (1, idx, now)
            _set_my(G, SENT[idx])
            _book_turn(G, 'w', idx, SENT[idx], now)
    elif G['state'] == 'search':
        G['hint_t'] = now

def _intro_text(wrap):
    out = []
    for s_ in INTRO:
        out.extend(textwrap.wrap(s_, wrap))
        out.append('')
    return chr(10).join(out).strip(chr(10))

def _show_cards(G):
    # 封面期间：把「日历」「光点数」两块牌子整个关掉（它们的黑色底会挡住封面）；游戏开始后再打开，同时关掉封面。
    # 柜门上的书本封面阶段（door_open 还是 False）：游戏规则（封面形状）也先不出现
    want = G['state'] != 'intro'
    rules_on = (not want) and (G.get('door_open') or not _cover_on())
    key_ = (want, rules_on)
    if G.get('cards_on') == key_:
        return
    G['cards_on'] = key_
    try:
        for c in op('/project1/kantanMapper/project/allShapes').children:
            if c.op('parameters') is None or not hasattr(c.op('parameters').par, 'Name'):
                continue
            nm = str(c.op('parameters').par.Name.eval()).strip()
            if nm in ('日历', '光点数'):
                c.par.render = want
            elif nm == '封面':
                c.par.render = rules_on
    except Exception as e_:
        print('开关牌子失败：', repr(e_)[:80])

def _uniq(L):
    seen_, out_ = set(), []
    for s_ in L:
        if s_ not in seen_:
            seen_.add(s_)
            out_.append(s_)
    return out_

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
        e_ = now - G['state_t']
        if e_ < _c('end_angel', END_ANGEL):
            return ''                          # 天使在的时候不打字，祝贺的话由机械声音读出来（见 _frame 里的 end_said）
        # 天使一下子消失后：把这一周找到的所有句子（去掉重复的）按顺序快速重新打一遍（红色，往上滚）
        remaining = int(max(0.0, e_ - _c('end_angel', END_ANGEL) - _c('sum_delay', 1.5)) * _c('sum_cps', SUM_CPS))
        flat = []
        for s_ in _uniq(G.get('week_told', [])):
            take = min(len(s_), remaining)
            if take <= 0:
                break
            flat.extend(textwrap.wrap(s_[:take], WRAP))
            remaining -= len(s_)
        return chr(10).join(flat[-11:])
    if T is not None:
        body = []
        told_ = T['told']
        if (_book_on() or _c('one_page', True)) and told_:
            # 他人视角那块只显示"这一页"的话（最新的一句）。新一句还没开始打时，旧的留到翻页动画一半（没动画就马上换）
            lt_, l0_ = told_[-1]
            if now >= l0_:
                told_ = [told_[-1]]
            elif len(told_) > 1 and now < l0_ - (_c('book_flip_s', 1.3) * 0.4 if _book_on() else 0.0):
                told_ = [told_[-2]]
            else:
                told_ = []
        for text, t0 in told_:
            if now < t0:
                continue
            nshow = min(len(text), int((now - t0) * _c('type_cps', TYPE_CPS)))
            shown = text[:max(0, nshow)]
            if shown:
                body.append(textwrap.wrap(shown, int(_c('sub_wrap', WRAP))))
        maxl = 11
        flat = []
        for b in body:
            flat.extend(b)
        flat = flat[-maxl:]
        lines.extend(flat)
        if T['n'] == 0 and now > T['t0'] and op('/project1/sc_hint_txt') is None:
            lines.extend(textwrap.wrap(_c('book_hint', 'Every key opens a page.'), WRAP))
            lines.extend(['', 'Press one,', 'then read.'])
    elif G['state'] == 'search':
        seen_ = now - G['seen_t'] < 3.0
        near_ = seen_ and math.hypot((G['dot'][0] - G['hx']) * LID_ASPECT, G['dot'][1] - G['hy']) < _c('flash_r', FLASH_R) * 0.95
        if near_:
            lines.append(_c('fist_hint', 'Hold your hand' + chr(10) + 'on the light.'))
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
            G['door_open'] = False
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
    near_ = bool(seen and math.hypot((G['dot'][0] - G['hx']) * LID_ASPECT, G['dot'][1] - G['hy']) < _c('flash_r', FLASH_R) * 0.9)
    if near_ and state == 'search':
        G.setdefault('dwell_t0', now)
    else:
        G.pop('dwell_t0', None)
    auto_ = _c('auto_catch', True) and 'dwell_t0' in G and now - G['dwell_t0'] > _c('auto_catch_s', 0.7)     # 手停在光点上 0.7 秒自动收集（也可以握拳）
    if (_grab(G) or auto_) and state == 'search' and now - G['flash_t0'] > 0.9:
        G.pop('dwell_t0', None)
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
        if state == 'tell' and _c('page_mode', True) and not _c('keys_in_page_mode', False):
            continue          # 挥手翻页模式下，空气钢琴/键盘的音符不再决定"出哪一句"（声音照常响），句子只由翻页决定，避免重复
        _press(G, key, now)
    # --- 开场介绍：先是柜门上的书本封面，门打开（或 cover_s 秒后自动）才出现游戏规则 ---
    if state == 'intro' and not G.get('door_open'):
        if not _cover_on() or me.fetch('door_open', False) or (_c('cover_s', 0.0) > 0 and now - G.get('intro_t0', now) > _c('cover_s', 0.0)):
            G['door_open'] = True
        me.store('door_open', False)
    elif me.fetch('door_open', False):
        me.store('door_open', False)            # 不是封面阶段按的空格不留着（否则下次回到封面会立刻开始）
    if state == 'intro' and G.get('door_open') and _c('intro_hand_start', True):
        if G.get('door_t') is None:
            G['door_t'] = now
        elif now - G['door_t'] > _c('intro_auto_s', 10.0):
            _new_day(G, now)                              # 规则文字显示 intro_auto_s 秒（默认 10）后自动进入游戏，不用按键也不用举手
            state = G['state']
    elif state == 'intro' and not G.get('door_open'):
        G.pop('door_t', None)
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
    if state == 'tell' and T is not None and _c('page_mode', True) and now >= T['t0'] and T['n'] < TELL_MAX and not T.get('closed'):
        pages_ = _pages(G['day'])
        if pages_:
            go_ = _wave(G, now) or (T['n'] == 0 and now - T['t0'] > _c('flip_auto_s', 5.0))      # 挥手翻页；第一页如果没人挥手，几秒后自动翻
            if go_:
                pi_ = T.get('pi')
                if pi_ is None:
                    pi_ = min(len(pages_) - 1, max(0, int((G['dot'][0] - 0.08) / 0.84 * len(pages_))))     # 第一页：光点在盖子上的位置（左→右）对应这一天的页（前→后）
                else:
                    pi_ = (pi_ + 1) % len(pages_)
                n0_ = T['n']
                _press(G, pages_[pi_], now)
                if T['n'] > n0_:
                    T['pi'] = pi_
                    G['wave_t'] = now
    if state == 'tell' and T is not None:
        if T['n'] == 0 and now - T['t0'] > TELL_FIRST and not _c('page_mode', True):
            ri_ = random.randrange(len(SENT))
            _add_told(G, SENT[ri_], now)
            _set_my(G, SENT[ri_])
            _book_turn(G, 'w', ri_, SENT[ri_], now)
        if T['told']:
            ltext, lt0 = T['told'][-1]
            over = now > lt0 + len(ltext) / _c('type_cps', TYPE_CPS) + _c('hold', HOLD_SEC)
            if over and not T.get('closed'):
                # 今天结束前，先出现一句话告诉观众"今天到这里了"（不记进一周的总结里），再过一会儿才换天
                T['closed'] = True
                ct_ = _c('week_end_text', "That's all for this week.") if G['day'] >= 6 else _c('day_end_text', "That's all for today.")
                cs_ = now + (_c('book_flip_s', 1.3) * 0.8 if _book_on() else 0.0)
                T['told'].append((ct_, cs_))
                G['my_prev'] = G.get('my')
                G['my'] = (None, cs_)
                _book_turn(G, 'w', 35, ct_, now)
            elif over:
                if G['day'] >= 6:
                    G['state'] = state = 'end'
                    G['state_t'] = now
                else:
                    G['day'] += 1
                    _new_day(G, now)
                    state = G['state']
    if state == 'end' and now - G['state_t'] > _c('end_angel', END_ANGEL) + _c('sum_delay', 1.5) + sum(len(s_) for s_ in _uniq(G.get('week_told', []))) / _c('sum_cps', SUM_CPS) + _c('sum_hold', SUM_HOLD):
        G['week_told'] = []
        G['day'] = 0
        G['week'] += 1
        G['count'] = 0
        G['lit'] = [False] * 7
        _new_day(G, now)
        if _c('intro', True):
            G['state'] = 'intro'                        # 一周结束后回到封面，等观众按键重新开始（不是直接进入周一）
            G['intro_t0'] = now
            G['door_open'] = False
        state = G['state']
    if state == 'end' and G.get('end_said') != G['week'] and now - G['state_t'] > _c('end_say_delay', 1.2):
        G['end_said'] = G['week']
        try:
            subprocess.Popen(['say', '-v', _c('end_voice', 'Zarvox'), '-r', str(int(_c('end_rate', 120))), _c('end_say', 'Congratulations. You found her secret.')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
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
        lid.par.vec2valuew = G.get('chk_vis', 0.0) if _c('cover_hide', True) else 0.0      # 封面（待机）时盖子上的房间整个隐藏
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
        hide = 0.0 if blank else (1.0 - G.get('chk_vis', 0.0) if _c('cover_hide', True) else 1.0)      # 封面（待机）时人脸万花筒、天使、光点都隐藏
        bed.par.vec0valuex = now % 1000.0
        bed.par.vec0valuey = 1.0 if _c('bed_flip', True) else 0.0
        bed.par.vec0valuez = 1920.0 / 1200.0
        bed.par.vec0valuew = _c('bed_angel', 0.0) * hide
        bed.par.vec1valuex, bed.par.vec1valuey = _c('bed_angel_pos', (0.5, 0.7))
        bed.par.vec1valuez = _c('bed_angel_size', 0.5)
        bed.par.vec1valuew = 1920.0 / 1080.0
        zx0, zy0, zx1, zy1 = _c('bed_dotbox', (0.62, 0.28, 0.94, 0.82))     # 光点区：不管盒盖上光点在哪，投到被子上都缩进这个框（默认在右床，没有万花筒的那张）
        bed.par.vec2valuex = zx0 + (G['dot'][0] - 0.08) / 0.84 * (zx1 - zx0)
        bed.par.vec2valuey = zy0 + (G['dot'][1] - 0.2) / 0.6 * (zy1 - zy0)
        bed.par.vec2valuez = G['bed_da'] * hide * _c('bed_dot_gain', 1.4)
        bed.par.vec2valuew = G['bed_found_t'] if G.get('bed_found_t') is not None else 0.0
        bed.par.vec3valuex, bed.par.vec3valuey = fx, fy
        bed.par.vec3valuez = G['bed_ha'] * hide * (1.0 if _c('bed_hand', False) else 0.0)     # 默认不显示木头手和光圈（被子不平，投上去不好看）
        bed.par.vec3valuew = max(0.0, min(1.0, 1.0 - sc))
        bed.par.vec4valuex = LID_ASPECT
        bed.par.vec4valuey = _c('bed_room_scale', 1.0)
        bed.par.vec4valuez = _c('bed_room_dim', 0.30) * hide
        bed.par.vec4valuew = R
        bed.par.vec5valuex = _c('bed_hand_size', 0.55)
        bed.par.vec5valuey = _c('bed_hand_bob', 0.012)
        bed.par.vec6valuex, bed.par.vec6valuey, bed.par.vec6valuez, bed.par.vec6valuew = _c('bed_box', (0.025, 0.2, 0.4, 0.8))   # 人脸万花筒矩形（左床，我的情绪）：x0, y0, x1, y1
        bed.par.vec7valuex = 1.0 if _c('bed_frame', False) else 0.0
        bed.par.vec7valuey = _c('bed_kal', 1.0) * hide
        bed.par.vec8valuex, bed.par.vec8valuey, bed.par.vec8valuez, bed.par.vec8valuew = _c('bed_tbox', (0.06, 0.30, 0.39, 0.40))     # 镜像字的小块：x0, y0, x1, y1
        bed.par.vec7valuez = _c('bed_text', 1.0) * hide * (G['bed_da'] if _c('bed_text_follow', False) else 1.0)     # 镜像字：默认一直显示；bed_text_follow=True 时找到光点才浮现
        bed.par.vec5valuez = 1.0 if _c('bed_room', False) else 0.0       # 默认不画房间（背景黑，之后用 Kantan 把光投到被子和杂物上）
    # --- 柜门上的书（sc_book，Kantan 形状「书本」）：开场是"封面"（线框书合着），门打开后封面消失；book_play=True 时听故事期间还会显示翻页的线框书 ---
    bk_ = p.op('sc_book')
    book_on_ = bk_ is not None and _c('book_mode', True)
    if book_on_:
        cover_ = G['state'] == 'intro' and not G.get('door_open') and _cover_on()
        play_ = _book_on() and G['state'] == 'tell'
        edit_ = _c('book_edit', False)                                # book_edit=True：编辑模式，书一直显示，方便在 Kantan 里摆位置
        show_ = cover_ or play_ or edit_
        G['bk_vis'] = G.get('bk_vis', 0.0) + ((1.0 if show_ else 0.0) - G.get('bk_vis', 0.0)) * min(1.0, dt_ * (5.0 if show_ else 12.0))
        b_ = G.get('bk')
        if b_ is None:
            b_ = G['bk'] = {'t0': -9.0, 'dir': 1.0, 'p': 1.0}
        if b_['p'] < 1.0:
            b_['p'] = min(1.0, (now - b_['t0']) / _c('book_flip_s', 1.3))
        if G.get('bkshape_path') is None:
            for c_ in op('/project1/kantanMapper/project/allShapes').findChildren(maxDepth=4):
                sp_ = c_.op('parameters')
                if sp_ is not None and hasattr(sp_.par, 'Name') and str(sp_.par.Name.eval()).strip() in (_c('book_shape', '翻页书'), '书本'):
                    G['bkshape_path'] = c_.path
        bs_ = op(G['bkshape_path']) if G.get('bkshape_path') else None
        if bs_ is not None:
            bon_ = show_ or G['bk_vis'] > 0.02
            if bon_ != G.get('bkshape_on'):
                G['bkshape_on'] = bon_
                bs_.par.render = bon_
        geo_ = p.fetch('bk_geo', (1920, 1080))
        bk_.par.vec0valuex = b_['p']
        bk_.par.vec0valuey = b_['dir']
        bk_.par.vec0valuez = geo_[0] / float(geo_[1])
        bk_.par.vec0valuew = now % 1000.0
        bk_.par.vec1valuex = _c('book_line', 1.0) * G['bk_vis']
        bk_.par.vec1valuey = _c('book_thick', 0.0025)
        bk_.par.vec1valuez = _c('book_margin', 0.085)
        bk_.par.vec1valuew = _c('book_lift', 0.06)
        try:
            bk_.par.vec2valuex = 1.0 if (cover_ or (edit_ and G['state'] == 'intro')) else 0.0    # 1 = 封面（合着的书）
            bk_.par.vec2valuey = 1.0 if _c('book_single', True) else 0.0                          # 1 = 单页模式（整个竖屏一张纸，翻页是一条页边从左扫到右）
        except Exception:
            pass
    # --- 被子上的红蓝格子（sc_checker）：待机（封面）时铺满「格子初始」形状，门打开/游戏开始后消失；找光点时手碰到盖子房间里的行李箱，「行李箱」形状亮一下 ---
    ck_ = p.op('sc_checker')
    if ck_ is not None:
        ck_.par.vec0valuex = _c('chk_cells', 14.0)
        ck_.par.vec0valuey = 1.0
        ck_.par.vec0valuez = now % 1000.0
        stand_ = G['state'] == 'intro' and not G.get('door_open')
        G['chk_vis'] = G.get('chk_vis', 0.0) + ((1.0 if stand_ else 0.0) - G.get('chk_vis', 0.0)) * min(1.0, dt_ * (6.0 if stand_ else 12.0))
        for i_, nm_ in enumerate(_c('cover_hide_shapes', ('右脸(一直说话)',))):          # 封面（待机）时盖子 Kantan 里这些形状先关掉（右边一直说话的脸），门打开后再显示
            sh2_ = _bed_shape(G, 'cvh%d_path' % i_, nm_, now, '/project1/kantanMapper')
            if sh2_ is not None:
                want2_ = not (G['chk_vis'] > 0.02)
                if want2_ != G.get('cvh%d_on' % i_):
                    G['cvh%d_on' % i_] = want2_
                    sh2_.par.render = want2_
        cm_, cs_ = p.op('sc_chk_main'), p.op('sc_chk_suit')
        if cm_ is not None:
            cm_.par.brightness1 = _c('chk_level', 1.0) * G['chk_vis']
            sh_ = _bed_shape(G, 'chk_path', _c('chk_shape', '格子初始'), now)
            if sh_ is not None:
                on_ = G['chk_vis'] > 0.02
                if on_ != G.get('chk_on'):
                    G['chk_on'] = on_
                    sh_.par.render = on_
        if cs_ is not None:
            sx0_, sy0_, sx1_, sy1_ = _c('suit_box', (0.075, 0.208, 0.219, 0.39))       # 盖子房间图里行李箱的位置（盖子 0~1 坐标，y 向上）
            pad_ = _c('suit_pad', 0.02)
            hov_ = seen and G['state'] == 'search' and sx0_ - pad_ <= fx <= sx1_ + pad_ and sy0_ - pad_ <= fy <= sy1_ + pad_
            if hov_:
                G['suit_hold'] = now + _c('suit_hold', 0.35)
            tgt_ = 1.0 if (hov_ or now < G.get('suit_hold', 0.0)) else 0.0
            sa_ = G.get('suit_a', 0.0)
            G['suit_a'] = sa_ + (tgt_ - sa_) * min(1.0, dt_ * (14.0 if tgt_ > sa_ else 3.0))
            cs_.par.brightness1 = _c('suit_level', 1.0) * G['suit_a']
            ss_ = _bed_shape(G, 'suit_path', _c('suit_shape', '行李箱'), now)
            if ss_ is not None:
                on2_ = G['suit_a'] > 0.02
                if on2_ != G.get('suit_on'):
                    G['suit_on'] = on2_
                    ss_.par.render = on2_
    # --- 被子 Kantan 的纹理守护：Kantan 重新加载会清掉脚本贴的纹理，这里每 4 秒检查「人脸万花筒」「光点出现区域」「行李箱」，被清了就贴回去（「格子初始」故意不贴，显示 Kantan 自带的测试线框）。不想要：cfg tex_guard=False ---
    if p.op('sc_checker') is not None and _c('tex_guard', True) and now - G.get('tg_t', -9.0) > 4.0:
        G['tg_t'] = now
        for key_, nm_, tex_ in (('face_path', _c('face_shape', '人脸万花筒'), '/project1/sc_bed_face'), ('dot_path', _c('dot_shape', '光点出现区域'), '/project1/sc_bed_dot'), ('suit_path', _c('suit_shape', '行李箱'), '/project1/sc_chk_suit')):
            if op(tex_) is None:
                continue
            sh3_ = _bed_shape(G, key_, nm_, now)
            sp3_ = sh3_.op('parameters') if sh3_ is not None else None
            if sp3_ is not None and hasattr(sp3_.par, 'Texture'):
                cur3_ = sp3_.par.Texture.eval()
                if str(getattr(cur3_, 'path', cur3_)) != tex_:
                    sp3_.par.Texture = tex_
                    sp3_.par.Showtexture = True
    # --- 左边「我的视角」（sc_my_txt / sc_my）：跟着右边那句话走，没有对应的就不出现 ---
    mt_, ml_ = p.op('sc_my_txt'), p.op('sc_my')
    if mt_ is not None and ml_ is not None and _c('my_follow', True):
        mex_ = p.op('sc_my_exec')
        if mex_ is not None and mex_.par.active.eval():
            mex_.par.active = False                       # 关掉自己循环播放的老脚本，改由琴键驱动
        cur_, prev_ = G.get('my'), G.get('my_prev')
        a_, show_ = 0.0, None
        if cur_ is not None and G['state'] == 'tell':
            tx_, l0_ = cur_
            if now >= l0_ + _c('my_delay', 0.0):
                show_, a_ = tx_, min(1.0, (now - l0_) / 0.15)       # 直接出现（只有极短的淡入，不打字）
            elif prev_ is not None and prev_[0] and now < l0_ - _c('book_flip_s', 1.3) * 0.4 * (1.0 if _book_on() else 0.0):
                show_, a_ = prev_[0], 1.0                          # 新一页还没翻过来：旧的留到右边旧的消失的时候
        if not show_:
            a_ = 0.0
        if show_ and G.get('my_shown') != show_:
            G['my_shown'] = show_
            mt_.par.text = chr(10).join(textwrap.wrap(show_, int(_c('my_chars', 24))))
            mt_.par.fontsizex = _c('my_px', 44)
            try:
                mt_.par.font = _c('my_font', 'Avenir Next')
            except Exception:
                pass
        ml_.par.opacity = max(0.0, a_)
    # --- 提示层（sc_hint_txt，另一种字体、更大）：只在抓到光点后、第一次按键之前显示 ---
    ht_ = p.op('sc_hint_txt')
    if ht_ is not None:
        T_ = G['tell']
        want_ = ''
        if G['state'] == 'tell' and T_ is not None and now > T_['t0'] and T_['n'] == 0:
            want_ = ('Wave your hand' + chr(10) + 'to turn the page.') if _c('page_mode', True) else ('Every key' + chr(10) + 'opens a page.' + chr(10) + chr(10) + 'Press one,' + chr(10) + 'then read.')
        if want_ != G.get('last_hint'):
            G['last_hint'] = want_
            ht_.par.text = want_ if want_ else ' '
            ht_.par.fontsizex = _c('hint_px', 70)
    # --- 写给右墙 ---
    txt = p.op('sc_sub_txt')
    lv = p.op('sc_sub')
    if txt is not None and lv is not None:
        s = _text(G, now)
        if s != G.get('last_txt'):
            G['last_txt'] = s
            txt.par.text = s
            txt.par.fontsizex = _c('sub_px', FONT_PX) if G['state'] == 'tell' else FONT_PX      # 听故事时（他人视角那块）字号可以单独调
        lv.par.opacity = 1.0
        red_ = G['state'] == 'end' and now - G['state_t'] >= _c('end_angel', END_ANGEL)
        if red_ != G.get('last_red'):
            G['last_red'] = red_
            for k_, v_ in (('fontcolorr', 1.0), ('fontcolorg', 0.12 if red_ else 1.0), ('fontcolorb', 0.12 if red_ else 1.0)):
                try:
                    setattr(txt.par, k_, v_)
                except Exception:
                    pass
    # --- 结尾的天使：就是 Kantan 里「云朵气泡」（item4）显示的那只红色眨眼天使；平时关掉，第 7 天结尾打开并触发警报（变大变红震动）。把形状拖到右边放大即可 ---
    try:
        if G.get('ang_path') is None:
            for c_ in op('/project1/kantanMapper/project/allShapes').children:
                if c_.name == _c('ang_shape', 'item4'):
                    G['ang_path'] = c_.path
        ang_ = op(G['ang_path']) if G.get('ang_path') else None
        if ang_ is not None:
            e_ = now - G['state_t'] if G['state'] == 'end' else -1.0
            on_ = _c('ang_always', False) or (0.0 <= e_ < _c('end_angel', END_ANGEL))
            if on_ != G.get('ang_on'):
                G['ang_on'] = on_
                ang_.par.render = on_
            if G['state'] == 'end' and G.get('ang_alarm') != G['week'] and e_ >= 0.0:
                G['ang_alarm'] = G['week']
                ex_ = op('/project1/sc_exec')
                if ex_ is not None:
                    ex_.store('alarm', (now, now + _c('end_angel', END_ANGEL) - 0.3))
    except Exception as e_:
        if G.get('ang_err') != repr(e_)[:80]:
            G['ang_err'] = repr(e_)[:80]
            print('sc_game_exec 天使开关出错：', G['ang_err'])
    # --- 钢琴形状（钢琴书）只在听故事时显示，其余时候（尤其是结尾）整个关掉，不会挡住天使 ---
    try:
        if G.get('pshape_path') is None:
            for c_ in op('/project1/kantanMapper/project/allShapes').children:
                sp_ = c_.op('parameters')
                if sp_ is not None and hasattr(sp_.par, 'Name') and str(sp_.par.Name.eval()).strip() == _c('piano_shape', '钢琴书'):
                    G['pshape_path'] = c_.path
        ps_ = op(G['pshape_path']) if G.get('pshape_path') else None
        if ps_ is not None:
            pon_ = _c('piano_edit', False) or (G['state'] == 'tell' and not _c('page_mode', True)) or (G.get('piano_vis', 0.0) > 0.02 and not _c('page_mode', True))     # piano_edit=True：编辑模式，钢琴形状一直显示，方便在 Kantan 里调
            if pon_ != G.get('pshape_on'):
                G['pshape_on'] = pon_
                ps_.par.render = pon_
    except Exception as e_:
        if G.get('pshape_err') != repr(e_)[:80]:
            G['pshape_err'] = repr(e_)[:80]
            print('sc_game_exec 钢琴形状开关出错：', G['pshape_err'])
    # --- 字幕下面的小钢琴（Kantan 里叫「钢琴书」的形状，纹理 sc_piano）：按下的键亮着直到这句打完，再慢慢暗掉 ---
    pn_ = p.op('sc_piano')
    if pn_ is not None:
        k_, i_, t_ = G.get('piano', (0, 0, -99.0))
        T_ = G['tell']
        hold_ = t_ + 0.5
        if T_ is not None and T_['told']:
            lt_, l0_ = T_['told'][-1]
            hold_ = max(hold_, l0_ + len(lt_) / _c('type_cps', TYPE_CPS) + 0.4)
        b_ = 1.0 if now < hold_ else math.exp(-(now - hold_) / 0.8)
        if G['state'] != 'tell' or b_ < 0.01:
            k_, b_ = 0, 0.0
        pn_.par.vec0valuey, pn_.par.vec0valuez, pn_.par.vec0valuew = float(k_), float(i_), b_
        pn_.par.vec1valuex = pn_.par.vec1valuey = pn_.par.vec1valuez = pn_.par.vec1valuew = 0.0   # 不记录按过的键，只亮当前按下的那个
        tgt_ = 1.0 if (G['state'] == 'tell' or _c('piano_edit', False)) else 0.0                  # 钢琴只在"该按键听故事"的时候出现
        G['piano_vis'] = G.get('piano_vis', 0.0) + (tgt_ - G.get('piano_vis', 0.0)) * min(1.0, dt_ * 6.0)
        pn_.par.vec2valuex = G['piano_vis']
    _show_cards(G)
    # --- 写给封面牌子（Kantan 里叫 封面 的形状） ---
    cov = p.op('sc_intro')
    if cov is not None:
        cv = _intro_text(30) if G['state'] == 'intro' else ' '
        if cv != G.get('last_cover'):
            G['last_cover'] = cv
            cov.par.text = cv
            n_ = max(1, len(cv.split(chr(10))))
            try:
                cov.par.fontsizex = max(16, min(32, int(_c('intro_h', 720) / (n_ * 1.28))))      # 行数多就自动缩小字号，不超出画面
            except Exception:
                pass
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
        cs_ = ' ' if G['state'] == 'intro' else _c('count_label', 'Lights') + chr(10) + str(G['count']) + ' / 7'
        if cs_ != G.get('last_count'):
            G['last_count'] = cs_
            ctx.par.text = cs_
            ctx.par.fontsizex = _c('count_px', 34)
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

FXJSON = BASE + '/../td_live/gaze_bridge/audio_fx.json'

def _bed_display():
    # 被子投影仪的屏幕号：cfg['bed_display'] 优先；否则读 audio_fx.json 里的 bed_display（重开 TD 不会丢）；再不行用 1
    v = _c('bed_display', None)
    if v is not None:
        return int(v)
    try:
        import json as _j
        t_ = me.fetch('bd_t', 0.0)
        if time.time() - t_ > 5.0:
            me.store('bd_t', time.time())
            with open(FXJSON, encoding='utf-8') as fh_:
                me.store('bd_v', int(_j.load(fh_).get('bed_display', 1)))
        return int(me.fetch('bd_v', 1))
    except Exception:
        return 1

def _keep_bed_window(frame):
    # 表演窗口开着、被子窗口没开时，自动把被子窗口（第二个场景）打开到屏幕 bed_display；想关掉：cfg 里 bed_autoopen=False
    if frame % 60 != 0 or not _c('bed_autoopen', True):
        return
    g_, b_ = op('/project1/gz_win'), op('/project1/sc_win2')
    if g_ is None or b_ is None or not g_.isOpen or b_.isOpen:
        return
    b_.par.justifyoffsetto = 'specifydisplay'
    b_.par.display = _bed_display()
    b_.par.justifyh, b_.par.justifyv = 'left', 'top'
    b_.par.winoffsetx = b_.par.winoffsety = 0
    b_.par.winw, b_.par.winh = 1920, 1200
    b_.par.borders = False
    b_.par.winopen.pulse()
    print('sc_game_exec：被子窗口没开，已自动打开（屏幕 %d）' % _bed_display())

def onFrameEnd(frame):
    try:
        _keep_bed_window(frame)
    except Exception as e:
        print('sc_game_exec 自动开被子窗口失败：', repr(e)[:100])
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
        if not _c('perf_auto', False):
            for n_ in ('sc_perfswitch', 'sc_viewswitch'):          # 表演窗口固定显示游戏、被子窗口固定显示第二个场景（不再 3 秒自动切换）
                o_ = op('/project1/' + n_)
                if o_ is not None:
                    o_.par.index.mode = ParMode.CONSTANT
                    o_.par.index = 0
        print('sc_game_exec 启动：已关掉用不到的 MediaPipe 检测，游戏回到封面')
    except Exception as e:
        print('sc_game_exec 启动设置失败：', repr(e)[:100])
