# 在 TD 的 Textport 里运行：
#   exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/code/td_scripts/gaze_setup.py', encoding='utf-8').read())
# 作用：新建/更新 gz_out、gz_heat、gz_kb、gz_exec、gz_switch、gz_tile、gz_fit，并让 gz_win 读 gz_fit。可重复运行。
BRIDGE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'

EXEC_CODE = '''
import json, os, time, re, random
BRIDGE = %r

FLIP_X = False        # 目光左右反了就改 True
FLIP_Y = False        # 上下反了就改 True
SEND_EVERY = 3        # 没有变化时，每几帧写一次 params.json（有变化会立刻写）
GAIN_X, GAIN_Y = 4.5, 4.0   # 没有校准文件时用的放大倍数
SPREAD = 0.9          # 校准后，左右/上下极端位置对应 0.05~0.95
VERT_WEIGHTS = (('nosey', 0.5), ('facey', 0.3), ('dy', 0.2))   # 上下：鼻尖/脸位置/眼珠的混合比例
CAL = __CAL__         # 校准值（由 gaze_setup 从 calibration_test.json 算出；None=没校准）
SMOOTH = 0.35         # 目光平滑：越小越稳、越慢
MIDI_ROWS = [         # TD 的 MIDI 设备表在 /local，重启会丢，所以由脚本定期补回
    {'id': '1', 'indevice': 'KL Essential 61 mk3 MIDI', 'channel': '1'},   # 琴（midiin1 的 Device ID = 1）
    {'id': '2', 'outdevice': 'IAC Driver Bus 1', 'channel': '1'},          # 发给 GarageBand（air_out 的 id = 2）
]
STALE_FRAMES = 45
# ---- 空气乐器（手 -> 五声音阶）----
AIR_ZONES = 5                          # 画面左右分几个区
AIR_NOTES = [60, 62, 64, 67, 69]       # 每个区的音（C D E G A，五声音阶），发给 GarageBand
AIR_LUCY_NOTES = [61, 63, 65, 66, 68]  # 同时"伪装成琴键"给 Lucy 画面用的编号（对应前 5 个乐器；琴有 +1 偏移）
AIR_FLIP_X = False                     # 左右反了改 True
AIR_Y0, AIR_Y1 = 0.0, 0.8              # 手的高度范围（食指根部 y）：低 -> 轻，高 -> 重
AIR_PITCH_FROM = 'y'                   # 音高来自：'y'=手的高度（越高越高音）；'x'=左右 5 个区
AIR_Y_NOTES = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81]   # 手从低到高的 10 个音（C D E G A C D E G A，五声音阶两个八度）
AIR_VEL = 0.8                          # 弹音的力度（音高来自高度时用固定力度）
AIR_Y_MARGIN = 0.25                    # 换音的"粘滞"（0~0.5，越大越不容易抖）
AIR_TOGGLE_PAD = 'ch11n46'             # 开/关空气乐器的打击垫（第 2 个垫）
SND_TOGGLE_PAD = 'ch11n47'             # TD 声音总开关（第 3 个打击垫）
SND_GAIN_LO, SND_GAIN_HI = 15.0, 300.0 # 放大倍数：手低 -> LO，手高 -> HI（指数变化；越大越失真）
SND_VOL_LO, SND_VOL_HI = 0.25, 0.5     # 总音量：手低 -> LO，手高 -> HI（上限别太高，小心耳朵）
SND_SMOOTH = 0.15                      # 变化的平滑
AIR_VEL_MIN = 0.4                      # 最轻的力度
AIR_DEBOUNCE = 3                       # 换区需要连续几帧（防抖）
AIR_LOST = 10                          # 手消失连续几帧才停音
HAND_PATHS = ['/project1/hand_tracking2/null2', '/project1/hand_tracking/null2']
HAND_PATHS_2 = [HAND_PATHS, ['/project1/hand_tracking2/null3']]
     # 连续这么多帧数据一模一样 = 追踪已停止（数据被保持住了），不再当作在看

NOTE_RE = re.compile(r'ch\\d+n(\\d+)$')
TILE_MAX = 6.0        # 最高音时一排最多几张脸（缩放 1/N）
TILE_SKIP = (61, 73)  # 这几个键是乐器键，不改张数（琴实际发出的编号）
TILE_LOW, TILE_HIGH = 37, 97   # 琴最低、最高键的编号
TILE_SMOOTH = 0.12    # 张数变化的平滑（越小越慢）
NOTE_OFFSET = 1       # 琴发出的编号比标准多多少（你的琴最低键发 37，所以是 1）
BLACK_PC = (1, 3, 6, 8, 10)   # 黑键在一个八度里的位置（C=0）


def _state():
    st = me.fetch('st', None, search=False)
    if st is None:
        st = {'lo': [None, None], 'hi': [None, None], 'new_face': 0, 'reset': 0, 'prev_n': 0}
        me.store('st', st)
    return st


def _is_stale(st, key, values):
    """真实追踪每帧都有微小变化；连续 STALE_FRAMES 帧完全一样就是被保持住的旧数据。"""
    sig = tuple(round(v, 7) for v in values)
    last = st.get('sig_' + key)
    if sig == last:
        st['same_' + key] = st.get('same_' + key, 0) + 1
    else:
        st['same_' + key] = 0
        st['sig_' + key] = sig
    return st['same_' + key] >= STALE_FRAMES


def _read_gaze(st):
    src = op('face_xyz')
    if src is None or src.numChans < 2:
        return None
    vals = [src[0].eval(), src[1].eval()]
    if abs(vals[0]) < 1e-9 and abs(vals[1]) < 1e-9:      # 全是 0：没有数据，不是"在看左上角"
        return None
    if _is_stale(st, 'xyz', vals):                        # 数据冻住了：追踪已停止
        return None
    out = []
    for i, v in enumerate(vals):
        if st['lo'][i] is None:
            st['lo'][i], st['hi'][i] = v - 0.01, v + 0.01
        st['lo'][i] = min(v, st['lo'][i] + 0.0005 * (st['hi'][i] - st['lo'][i]))
        st['hi'][i] = max(v, st['hi'][i] - 0.0005 * (st['hi'][i] - st['lo'][i]))
        span = max(st['hi'][i] - st['lo'][i], 1e-6)
        out.append(min(1.0, max(0.0, (v - st['lo'][i]) / span)))
    x, y = out
    if FLIP_X: x = 1 - x
    if FLIP_Y: y = 1 - y
    return x, y


def _read_iris(st):
    chop = op('/project1/face_control_in')
    if chop is None or chop['x'] is None or chop.numSamples < 478:
        return None
    X = chop['x']; Y = chop['y']
    if X[473] == 0 and Y[473] == 0:      # 没检测到脸
        return None
    if _is_stale(st, 'iris', (X[473], Y[473], X[468], Y[468])):   # 数据冻住了：MediaPipe 已停止
        return None
    dxs, dys = [], []
    for iris, a, b, top, bot in ((468, 33, 133, 159, 145), (473, 263, 362, 386, 374)):
        w = abs(X[a] - X[b])
        if w < 1e-6:
            return None
        dxs.append((X[iris] - (X[a] + X[b]) / 2) / w)
        dys.append((Y[iris] - (Y[top] + Y[bot]) / 2) / w)
    dx = sum(dxs) / 2
    dy = sum(dys) / 2
    face_h = Y[152] - Y[10]
    st['dbg'] = {'dx': dx, 'dy': dy,
                 'pitch': (Y[1] - (Y[10] + Y[152]) / 2) / face_h if abs(face_h) > 1e-6 else 0,
                 'facey': (Y[10] + Y[152]) / 2, 'facex': (X[10] + X[152]) / 2,
                 'nosey': Y[1], 'noseyrel_eye': Y[1] - (Y[33] + Y[263]) / 2}
    d = st['dbg']
    if CAL:
        sx = (d['dx'] - CAL['dx_mid']) / CAL['dx_span']
        sy = sum(w * (d[k] - CAL[k + '_mid']) / CAL[k + '_span'] for k, w in VERT_WEIGHTS)
        x = min(1.0, max(0.0, 0.5 + SPREAD * sx))
        y = min(1.0, max(0.0, 0.5 + SPREAD * sy))
    else:
        x = min(1.0, max(0.0, 0.5 + dx * GAIN_X))
        y = min(1.0, max(0.0, 0.5 + dy * GAIN_Y))
    if FLIP_X: x = 1 - x
    if FLIP_Y: y = 1 - y
    p = st.get('prev')
    if p:
        x = p[0] + (x - p[0]) * SMOOTH
        y = p[1] + (y - p[1]) * SMOOTH
    st['prev'] = (x, y)
    return x, y


def _write(st, gaze):
    d = {'gaze': {'x': gaze[0] if gaze else 0.5, 'y': gaze[1] if gaze else 0.5, 'on': 1 if gaze else 0},
         'new_face': st['new_face'], 'reset': st['reset'], 'dbg': st.get('dbg'), 'midi': st.get('midi'), 'air': {'on': st.get('air_on', False), 'dbg': st.get('air_dbg')}, 'snd': st.get('snd_dbg'), 'clap': st.get('clap_dbg'), 'scene': {'now': st.get('scene'), 'xf': (round(st['xf'], 2) if st.get('xf') is not None else None), 'i': st.get('scene_i', 0), 'xa': (round(st['xa'], 2) if st.get('xa') is not None else None)}}
    tmp = BRIDGE + '/params.json.' + str(int(time.time() * 1000)) + '.tmp'
    try:
        with open(tmp, 'w') as f:
            json.dump(d, f)
        os.replace(tmp, BRIDGE + '/params.json')
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _ensure_midi_table():
    t = op('/local/midi/device')
    if t is None or t.numRows < 1:
        return
    hdr = [c.val for c in t.row(0)]
    for want in MIDI_ROWS:
        r = None
        for i in range(1, t.numRows):
            if t[i, 0].val == want['id']:
                r = i
                break
        if r is None:
            t.appendRow([want.get(h, '') for h in hdr])
            continue
        for h in hdr:
            if want.get(h) and t[r, h].val != want[h]:
                t[r, h] = want[h]


def _hand_node():
    for p in HAND_PATHS:
        n = op(p)
        if n is not None:
            return n
    return None


AIR_MAX_CH = 32                        # air_note 里最多预留多少个音符通道
AIR_SCALES = {'pentatonic': [0, 2, 4, 7, 9], 'major': [0, 2, 4, 5, 7, 9, 11], 'minor': [0, 2, 3, 5, 7, 8, 10], 'chromatic': list(range(12))}


def _air_notes(cfg):
    """按设置生成从低到高的音符列表：音阶 × 几个八度，再加最顶上的一个音。"""
    iv = AIR_SCALES.get(cfg.get('air_scale', 'pentatonic'), AIR_SCALES['pentatonic'])
    base = int(cfg.get('air_base', 48))
    octs = max(1, int(cfg.get('air_octaves', 3)))
    notes = []
    for o in range(octs):
        for i_ in iv:
            notes.append(base + 12 * o + i_)
    notes.append(base + 12 * octs)
    notes = [nt for nt in notes if 0 <= nt <= 127][:AIR_MAX_CH]
    return notes


def _hand_nodes():
    out = []
    for lst in HAND_PATHS_2:
        n = None
        for p in lst:
            n = op(p)
            if n is not None:
                break
        out.append(n)
    return out


def _read_one_hand(st, hs, n, cfg):
    """读一只手：返回 dict(x,y,frac,pitch,closed,...) 或 None（没有这只手）。hs 是这只手自己的状态。"""
    if n is None:
        hs['fist_state'] = False
        hs['fist_cnt'] = 0
        hs['pinch_cnt'] = 0
        hs['pinch_state'] = False
        return None
    pts = list(n.points)
    if len(pts) <= 20:
        hs['fist_state'] = False
        hs['fist_cnt'] = 0
        hs['pinch_cnt'] = 0
        hs['pinch_state'] = False
        return None
    x, y = pts[9].x, pts[9].y
    if cfg.get('air_flip_x', AIR_FLIP_X):
        x = 1.0 - x
    openness = None
    closed = False
    w = pts[0]
    m = pts[9]
    palm = ((m.x - w.x) ** 2 + (m.y - w.y) ** 2) ** 0.5
    pinch_ratio = None
    if palm > 1e-4:
        if cfg.get('fist_on', True):
            tips = [pts[8], pts[12], pts[16], pts[20]]
            openness = sum(((t.x - w.x) ** 2 + (t.y - w.y) ** 2) ** 0.5 for t in tips) / (4.0 * palm)
            was = hs.get('fist_state', False)
            cand = openness < float(cfg['fist_exit' if was else 'fist_enter'])
            hs['fist_cnt'] = (hs.get('fist_cnt', 0) + 1) if cand else 0
            if was:
                closed = cand
            else:
                closed = hs['fist_cnt'] >= int(cfg.get('fist_frames', 5))
            if closed and not was and st.get('fist_since', 999) > int(cfg['fist_gap_frames']):
                st['new_face'] = st.get('new_face', 0) + 1      # 任何一只手 张开 -> 握拳：换新脸
                st['fist_since'] = 0
                st['fist_n'] = st.get('fist_n', 0) + 1
            hs['fist_state'] = closed
        if cfg.get('pinch_on', True):
            th = pts[4]
            ix = pts[8]
            pinch_ratio = (((th.x - ix.x) ** 2 + (th.y - ix.y) ** 2) ** 0.5) / palm
            cand_p = pinch_ratio < float(cfg['pinch_enter']) and not closed
            hs['pinch_cnt'] = (hs.get('pinch_cnt', 0) + 1) if cand_p else 0
            is_p = hs['pinch_cnt'] >= int(cfg['pinch_frames'])
            if is_p and not hs.get('pinch_state', False) and st.get('pinch_since', 999) > int(cfg['pinch_gap_frames']):
                st['scene_next'] = True
                st['pinch_since'] = 0
                st['pinch_n'] = st.get('pinch_n', 0) + 1
            hs['pinch_state'] = is_p
    mute_fist = bool(closed and cfg.get('fist_mutes', True))
    r = {'x': x, 'y': y, 'closed': closed, 'mute': mute_fist, 'open': openness, 'pinch': pinch_ratio, 'frac': 0.0, 'pitch': None, 'zone': None}
    if mute_fist:
        return r
    # 高度范围（两只手共用一个范围）
    if st.get('y_lo') is None:
        st['y_lo'], st['y_hi'] = y - 0.15, y + 0.15
    lo, hi = st['y_lo'], st['y_hi']
    span = hi - lo
    lo = min(y, lo + span * 0.001)
    hi = max(y, hi - span * 0.001)
    if hi - lo < 0.3:
        mid = (hi + lo) / 2.0
        lo, hi = mid - 0.15, mid + 0.15
    st['y_lo'], st['y_hi'] = lo, hi
    r['frac'] = min(1.0, max(0.0, (y - lo) / (hi - lo)))
    r['zone'] = int(min(AIR_ZONES - 1, max(0.0, x * AIR_ZONES)))
    notes = _air_notes(cfg)
    st['air_notes'] = notes
    marg = float(cfg.get('air_margin', 0.25))
    if cfg.get('air_pitch_from', 'x') == 'y':
        fpos = r['frac']
    else:
        xlo, xhi = float(cfg.get('air_x_lo', 0.12)), float(cfg.get('air_x_hi', 0.88))
        fpos = min(1.0, max(0.0, (x - xlo) / max(xhi - xlo, 0.05)))
    p = fpos * len(notes)
    k = int(min(len(notes) - 1, p))
    cur_k = hs.get('air_k')
    if cur_k is not None and cur_k < len(notes) and abs(p - (cur_k + 0.5)) < 0.5 + marg:
        k = cur_k
    r['pitch'] = notes[k]
    r['k'] = k
    return r


def _update_air(st):
    """两只手都能弹：每只手各自按左右位置选音（左低右高），可同时按住两个不同的音。
    手抬得越高(取两只手里更高的那只)越响越失真。握拳=该手停音(任一手握拳换新脸)，捏合=切场景。"""
    on = st.get('air_on', False)
    cfg = _fx_cfg(st)
    nodes = _hand_nodes() if on else [None, None]
    st['fist_since'] = st.get('fist_since', 999) + 1
    st['pinch_since'] = st.get('pinch_since', 999) + 1
    reads = []
    cur_notes = set()
    best_frac = None
    dbg = []
    for hi_, n in enumerate(nodes):
        hs = st.setdefault('hand' + str(hi_), {})
        r = _read_one_hand(st, hs, n, cfg)
        reads.append(r)
        key = r['pitch'] if r is not None else None
        # 每只手各自防抖
        if key == hs.get('cand'):
            hs['cand_n'] = hs.get('cand_n', 0) + 1
        else:
            hs['cand'] = key
            hs['cand_n'] = 1
        mute = r is not None and r['mute']
        need = (1 if mute else AIR_LOST) if key is None else AIR_DEBOUNCE
        cur = hs.get('note_cur')
        if hs['cand_n'] >= need and key != cur:
            cur = key
            hs['note_cur'] = cur
            hs['air_k'] = r['k'] if key is not None else None
        if not on:
            cur = None
            hs['note_cur'] = None
            hs['air_k'] = None
        hs['cur'] = cur
        if cur is not None:
            cur_notes.add(cur)
            if r is not None and r['pitch'] is not None:
                fr = r['frac']
                best_frac = fr if best_frac is None else max(best_frac, fr)
        if on:
            if r is None:
                dbg.append({'note': hs.get('note_cur')})
            else:
                dbg.append({'x': round(r['x'], 3), 'y': round(r['y'], 3), 'frac': round(r['frac'], 2), 'note': hs.get('note_cur'), 'zone': r['zone'], 'open': (round(r['open'], 2) if r['open'] is not None else None), 'fist': r['closed'], 'pinch': (round(r['pinch'], 2) if r['pinch'] is not None else None)})
    st['air_frac'] = best_frac
    st['air_dbg'] = ({'hands': dbg, 'fist_n': st.get('fist_n', 0), 'pinch_n': st.get('pinch_n', 0)} if on else None)
    c = op('air_note')
    if c is not None:
        notes_now = _air_notes(cfg)
        if tuple(notes_now) != st.get('air_notes_set'):
            if st.get('air_pending') is None:                # 第一步：先把所有通道清零（让 GarageBand 收到音符结束）
                for i in range(AIR_MAX_CH):
                    setattr(c.par, 'value' + str(i), 0.0)
                    st['air_v' + str(i)] = 0.0
                st['air_pending'] = 3
            else:
                st['air_pending'] -= 1
                if st['air_pending'] <= 0:                    # 第二步：几帧后再改通道名
                    for i in range(AIR_MAX_CH):
                        setattr(c.par, 'name' + str(i), ('ch1n' + str(notes_now[i])) if i < len(notes_now) else ('unused' + str(i)))
                    st['air_notes_set'] = tuple(notes_now)
                    st['air_pending'] = None
        else:
            for i, nt in enumerate(notes_now):
                v = AIR_VEL if nt in cur_notes else 0.0
                if st.get('air_v' + str(i)) != v:
                    setattr(c.par, 'value' + str(i), v)
                    st['air_v' + str(i)] = v
    if st.get('midi') is not None:
        for hi_, r in enumerate(reads):
            hs = st.get('hand' + str(hi_), {})
            if r is not None and hs.get('cur') is not None and r['zone'] is not None:
                lv = round(AIR_VEL_MIN + (1.0 - AIR_VEL_MIN) * r['frac'], 2)
                kk = 'ch1n' + str(AIR_LUCY_NOTES[r['zone']])
                st['midi'][kk] = max(lv, st['midi'].get(kk, 0.0))


def _fx_cfg(st):
    """每约 2 秒读一次 audio_fx.json（手动改了保存就生效）。读不到就用内置默认。"""
    if st.get('fx_cfg') is None or st.get('fx_age', 999) >= 60:
        st['fx_age'] = 0
        cfg = {'gain_lo': SND_GAIN_LO, 'gain_hi': SND_GAIN_HI, 'vol_lo': SND_VOL_LO, 'vol_hi': SND_VOL_HI, 'clip_type': 'clamp',
               'clap_on': False, 'clap_min': 0.1, 'clap_ratio': 6.0, 'clap_gap_frames': 20,
               'fist_on': True, 'fist_enter': 1.3, 'fist_exit': 1.55, 'fist_mutes': True, 'fist_gap_frames': 30, 'fist_frames': 5,
               'visual_mode': 'auto', 'crowd_max': 20, 'crowd_min': 3, 'crowd_big': 0.7,
               'scenes': ['crowd', 'mirror', 'attn'], 'scene_auto_sec': 45, 'xfade_speed': 0.06,
               'pinch_on': True, 'pinch_enter': 0.35, 'pinch_frames': 4, 'pinch_gap_frames': 60,
               'air_pitch_from': 'x', 'air_scale': 'pentatonic', 'air_base': 48, 'air_octaves': 3,
               'air_x_lo': 0.12, 'air_x_hi': 0.88, 'air_flip_x': False, 'air_margin': 0.25}
        try:
            with open(BRIDGE + '/audio_fx.json', encoding='utf-8') as fh:
                j = json.load(fh)
            for k in cfg:
                if k in j:
                    cfg[k] = j[k]
        except Exception:
            pass
        cfg['vol_lo'] = min(0.8, max(0.0, float(cfg['vol_lo'])))      # 音量硬上限，保护耳朵
        cfg['vol_hi'] = min(0.8, max(0.0, float(cfg['vol_hi'])))
        st['fx_cfg'] = cfg
    st['fx_age'] = st.get('fx_age', 0) + 1
    return st['fx_cfg']


def _update_snd(st):
    """TD 里处理 GarageBand 的声音：手越高，放大倍数越大（越失真）、总音量越大。默认静音，S 键/打击垫 3 开关。参数在 audio_fx.json。"""
    g = op('snd_gain')
    v = op('snd_vol')
    if g is None or v is None:
        return
    cfg = _fx_cfg(st)
    c = op('snd_clip')
    if c is not None and cfg['clip_type'] != st.get('clip_set'):
        try:
            c.par.type = cfg['clip_type']
            st['clip_set'] = cfg['clip_type']
        except Exception:
            pass
    on = st.get('snd_on', False)
    frac = st.get('air_frac') if st.get('air_on') else None
    f = frac if frac is not None else 0.0
    glo, ghi = float(cfg['gain_lo']), float(cfg['gain_hi'])
    tg = glo * ((ghi / glo) ** f)
    tv = (cfg['vol_lo'] + (cfg['vol_hi'] - cfg['vol_lo']) * f) if on else 0.0
    cg = st.get('snd_g_cur', glo)
    cv = st.get('snd_v_cur', 0.0)
    cg += (tg - cg) * SND_SMOOTH
    cv += (tv - cv) * SND_SMOOTH
    st['snd_g_cur'], st['snd_v_cur'] = cg, cv
    if abs(cg - st.get('snd_g_set', -1.0)) > 0.01 * max(cg, 1.0):
        g.par.gain = cg
        st['snd_g_set'] = cg
    if abs(cv - st.get('snd_v_set', -1.0)) > 0.002:
        v.par.gain = cv
        st['snd_v_set'] = cv
    st['snd_n'] = st.get('snd_n', 0) + 1
    if st['snd_n'] %% 10 == 0:                       # 每 10 帧量一次：进来/放大后/最后输出 的最大音量
        lv = {}
        for key, nm in (('in', 'snd_in'), ('clip', 'snd_clip'), ('out', 'snd_vol')):
            o = op(nm)
            try:
                lv[key] = round(float(abs(o.numpyArray()).max()), 4)
            except Exception:
                lv[key] = None
        st['snd_dbg'] = {'on': on, 'gain': round(cg, 1), 'vol': round(cv, 3), 'clip': st.get('clip_set'), 'lvl': lv, 'frac': (round(frac, 2) if frac is not None else None)}


def _update_clap(st):
    """麦克风听拍手：忽然比平时响很多 -> 换新脸（new_face 加 1）。参数在 audio_fx.json。"""
    cfg = _fx_cfg(st)
    o = op('clap_in')
    if o is None or not cfg.get('clap_on', True):
        return
    try:
        peak = float(abs(o.numpyArray()).max())
    except Exception:
        return
    base = st.get('clap_base', 0.01)
    st['clap_since'] = st.get('clap_since', 999) + 1
    ratio = float(cfg['clap_ratio'])
    is_clap = peak > float(cfg['clap_min']) and peak > ratio * max(base, 0.003) and st['clap_since'] > int(cfg['clap_gap_frames'])
    if is_clap:
        st['new_face'] = st.get('new_face', 0) + 1
        st['clap_since'] = 0
        st['clap_n'] = st.get('clap_n', 0) + 1
    elif peak < 3.0 * max(base, 0.003):               # 平时的响度慢慢更新（拍手那种突然的大响声不参与）
        st['clap_base'] = base * 0.98 + peak * 0.02
    st['clap_dbg'] = {'peak': round(peak, 4), 'base': round(st.get('clap_base', base), 4), 'n': st.get('clap_n', 0)}


CROWD_N = 20                           # 脸群最多几个"变换节点"（cf0~cf19）


def _crowd_layout(seed, n):
    """给一个种子，生成 n 张脸的布局：少数大、多数小；大的在前（在底层）。"""
    rng = random.Random(seed * 7919 + 13)
    sizes = sorted([0.10 + 0.60 * (rng.random() ** 2.5) for _ in range(n)], reverse=True)
    out = []
    for s_ in sizes:
        out.append({'s': s_, 'tx': rng.uniform(-0.42, 0.42), 'ty': rng.uniform(-0.38, 0.38), 'rot': rng.uniform(-18.0, 18.0)})
    return out


def _update_scene(st):
    """场景系统：auto=自动轮换(每隔 N 秒) + 捏合手势切下一个；也可固定 crowd/mirror/attn。
    gz_xfade(Cross) 管 镜像<->群像，gz_xfade2(Cross) 再管 (它们)<->黑白 AI 注意力图。"""
    cfg = _fx_cfg(st)
    mode = cfg.get('visual_mode', 'auto')
    valid = ('crowd', 'mirror', 'attn')
    scenes = [x_ for x_ in (cfg.get('scenes') or ['crowd', 'mirror']) if x_ in valid] or ['crowd']
    now = time.time()
    if mode == 'auto':
        i = st.get('scene_i', 0)
        if st.get('scene_t') is None:
            st['scene_t'] = now
        sec = float(cfg.get('scene_auto_sec', 45))
        if sec > 0 and now - st['scene_t'] > sec:
            i += 1
            st['scene_t'] = now
        if st.pop('scene_next', False):
            i += 1
            st['scene_t'] = now
        st['scene_i'] = i
        scene = scenes[i %% len(scenes)]
    else:
        st.pop('scene_next', None)
        scene = mode if mode in valid else 'crowd'
    st['scene'] = scene
    speed = float(cfg.get('xfade_speed', 0.06))
    # 镜像<->群像：只有在 mirror/crowd 时才改目标；切到 attn 时保持不动（被 attn 盖住）
    if scene in ('crowd', 'mirror'):
        tx_ = 1.0 if scene == 'crowd' else 0.0
    else:
        tx_ = st.get('xf', 1.0)
    xf = st.get('xf', tx_)
    xf += (tx_ - xf) * speed
    if abs(tx_ - xf) < 0.002:
        xf = tx_
    st['xf'] = xf
    ta_ = 1.0 if scene == 'attn' else 0.0
    xa = st.get('xa', ta_)
    xa += (ta_ - xa) * speed
    if abs(ta_ - xa) < 0.002:
        xa = ta_
    st['xa'] = xa
    node = op('gz_xfade')
    if node is not None and abs(xf - st.get('xf_set', -1.0)) > 0.002:
        node.par.cross = xf
        st['xf_set'] = xf
    node2 = op('gz_xfade2')
    if node2 is not None and abs(xa - st.get('xa_set', -1.0)) > 0.002:
        node2.par.cross = xa
        st['xa_set'] = xa


def _update_crowd(st):
    """脸的群像：手越高脸越多；换脸（new_face 变）时整群重新洗牌，位置/大小平滑过渡。"""
    cfg = _fx_cfg(st)
    if st.get('scene', 'crowd') == 'mirror' and st.get('xf', 0.0) < 0.02:
        return                                   # 完全切到镜像后不用再算群像
    if st.get('scene') == 'attn' and st.get('xa', 0.0) > 0.98:
        return                                   # 完全切到黑白注意力图后也不用算
    seed = st.get('new_face', 0)
    if st.get('crowd_seed') != seed or st.get('crowd_layout') is None:
        st['crowd_seed'] = seed
        st['crowd_layout'] = _crowd_layout(seed, CROWD_N)
    layout = st['crowd_layout']
    fr = st.get('air_frac')
    if fr is not None:
        st['crowd_frac'] = fr
    f = st.get('crowd_frac', 0.5)
    nmax = min(CROWD_N, int(cfg.get('crowd_max', 20)))
    nmin = min(nmax, int(cfg.get('crowd_min', 3)))
    nvis = nmin + f * (nmax - nmin)
    fit = op('gz_fit')
    try:
        aspect = float(fit.par.resolutionh) / float(fit.par.resolutionw)
    except Exception:
        aspect = 0.65
    big = float(cfg.get('crowd_big', 0.7)) / 0.7
    cur = st.get('crowd_cur')
    if cur is None:
        cur = [{'s': 0.0, 'tx': 0.0, 'ty': 0.0, 'rot': 0.0} for _ in range(CROWD_N)]
        st['crowd_cur'] = cur
    for i in range(CROWD_N):
        t_ = layout[i]
        vis = min(1.0, max(0.0, nvis - i))
        c_ = cur[i]
        c_['s'] += (t_['s'] * big * vis - c_['s']) * 0.12
        c_['tx'] += (t_['tx'] - c_['tx']) * 0.10
        c_['ty'] += (t_['ty'] - c_['ty']) * 0.10
        c_['rot'] += (t_['rot'] - c_['rot']) * 0.10
        node = op('cf' + str(i))
        if node is None:
            continue
        key = (round(c_['s'], 3), round(c_['tx'], 3), round(c_['ty'], 3), round(c_['rot'], 1))
        if st.get('crowd_set_' + str(i)) != key:
            node.par.sx = max(1e-4, c_['s'] * aspect)        # 脸是方的，画布是长方形：宽要乘 高/宽
            node.par.sy = max(1e-4, c_['s'])
            node.par.tx = c_['tx']
            node.par.ty = c_['ty']
            node.par.rotate = c_['rot']
            st['crowd_set_' + str(i)] = key


def _update_tiles(st):
    """最近按的琴键音高 -> 脸的张数（低音少、高音多），平滑过渡，写进 gz_tile 的缩放。"""
    cur_notes = {}
    for nm, v in (st.get('midi') or {}).items():
        m = NOTE_RE.match(nm)
        if m:
            cur_notes[int(m.group(1))] = v
    prev = st.get('prev_notes', {})
    for n, v in cur_notes.items():
        if v > 0 and prev.get(n, 0) == 0 and not (TILE_SKIP[0] <= n <= TILE_SKIP[1]):
            frac = (min(TILE_HIGH, max(TILE_LOW, n)) - TILE_LOW) / float(TILE_HIGH - TILE_LOW)
            st['tiles_target'] = 1.0 + frac * (TILE_MAX - 1.0)
    st['prev_notes'] = cur_notes
    tc = st.get('tiles_cur', 1.0)
    tc += (st.get('tiles_target', 1.0) - tc) * TILE_SMOOTH
    st['tiles_cur'] = tc
    t = op('gz_tile')
    if t is not None:
        sc = 1.0 / max(1.0, tc)
        if abs(sc - st.get('tile_s', -1.0)) > 0.002:
            t.par.sx = sc
            t.par.sy = sc
            st['tile_s'] = sc


def _update_view(st):
    """按住任意黑键 -> AI 注意力叠图(2)；V 键锁定 -> 人的目光热图(1)；否则脸(0)。黑键优先。"""
    held = False
    for nm, v in (st.get('midi') or {}).items():
        m = NOTE_RE.match(nm)
        if m and v > 0 and ((int(m.group(1)) - NOTE_OFFSET) %% 12) in BLACK_PC:
            held = True
    idx = 2 if held else (1 if st.get('view', 0) else 0)
    if idx != st.get('sw_idx'):
        sw = op('gz_switch')
        if sw is not None:
            sw.par.index = idx
        st['sw_idx'] = idx


def onFrameEnd(frame):
    st = _state()
    kb = op('gz_kb')
    if kb is not None and kb.numChans > 0:
        n = kb['n']
        cur = int(n.eval()) if n is not None else 0
        if cur == 1 and st['prev_n'] == 0:
            st['new_face'] += 1
        st['prev_n'] = cur
        v = kb['v']
        curv = int(v.eval()) if v is not None else 0
        if curv == 1 and st.get('prev_v', 0) == 0:
            st['view'] = 1 - st.get('view', 0)
        st['prev_v'] = curv
        ka = kb['a']
        cura = int(ka.eval()) if ka is not None else 0
        if cura == 1 and st.get('prev_a', 0) == 0:
            st['air_on'] = not st.get('air_on', False)
        st['prev_a'] = cura
        ks = kb['s']
        curs = int(ks.eval()) if ks is not None else 0
        if curs == 1 and st.get('prev_s', 0) == 0:
            st['snd_on'] = not st.get('snd_on', False)
        st['prev_s'] = curs

    mi = op('midiin1')
    if mi is not None:
        try:
            st['midi'] = {c.name: round(float(c.eval()), 3) for c in mi.chans()}
        except Exception:
            st['midi'] = {}

    pad = float((st.get('midi') or {}).get(AIR_TOGGLE_PAD, 0.0))
    if pad > 0 and st.get('prev_pad', 0.0) == 0:
        st['air_on'] = not st.get('air_on', False)
        st['y_lo'], st['y_hi'] = None, None
    st['prev_pad'] = pad
    try:
        _update_air(st)
    except Exception as e:
        if not st.get('air_err'):
            st['air_err'] = 1
            print('gz_exec 空气乐器出错（只打印一次）:', repr(e))
    try:
        _update_scene(st)
    except Exception as e:
        if not st.get('scene_err'):
            st['scene_err'] = 1
            print('gz_exec 场景切换出错（只打印一次）:', repr(e))
    try:
        _update_crowd(st)
    except Exception as e:
        if not st.get('crowd_err'):
            st['crowd_err'] = 1
            print('gz_exec 脸群像出错（只打印一次）:', repr(e))
    try:
        _update_clap(st)
    except Exception as e:
        if not st.get('clap_err'):
            st['clap_err'] = 1
            print('gz_exec 拍手出错（只打印一次）:', repr(e))
    pad3 = float((st.get('midi') or {}).get(SND_TOGGLE_PAD, 0.0))
    if pad3 > 0 and st.get('prev_pad3', 0.0) == 0:
        st['snd_on'] = not st.get('snd_on', False)
    st['prev_pad3'] = pad3
    try:
        _update_snd(st)
    except Exception as e:
        if not st.get('snd_err'):
            st['snd_err'] = 1
            print('gz_exec TD 声音出错（只打印一次）:', repr(e))
    if frame %% 90 == 0:
        try:
            _ensure_midi_table()
        except Exception as e:
            if not st.get('midi_tab_err'):
                st['midi_tab_err'] = 1
                print('gz_exec 补 MIDI 设备表出错（只打印一次）:', repr(e))
    try:
        _update_view(st)
    except Exception as e:
        if not st.get('view_err'):
            st['view_err'] = 1
            print('gz_exec 切换画面出错（只打印一次）:', repr(e))
    try:
        _update_tiles(st)
    except Exception as e:
        if not st.get('tile_err'):
            st['tile_err'] = 1
            print('gz_exec 张数出错（只打印一次）:', repr(e))

    changed = (st.get('midi') != st.get('sent_midi')) or (st['new_face'] != st.get('sent_new')) or (st['reset'] != st.get('sent_reset'))
    if frame %% SEND_EVERY == 0 or changed:
        try:
            g = _read_iris(st)
        except Exception as e:
            g = None
            if not st.get('err'):
                st['err'] = 1
                print('gz_exec 读虹膜出错（只打印一次）:', repr(e))
        _write(st, g or _read_gaze(st))
        st['sent_midi'] = dict(st.get('midi') or {})
        st['sent_new'] = st['new_face']
        st['sent_reset'] = st['reset']

    if frame %% 2 == 0:
        for name, fn in (('gz_out', 'out.png'), ('gz_heat', 'heat.png'), ('gz_ai', 'ai_heat.png'), ('gz_attn', 'ai_attn.png')):
            try:
                mt = os.path.getmtime(BRIDGE + '/' + fn)
            except Exception:
                continue
            if st.get('mt_' + name) != mt:
                st['mt_' + name] = mt
                o = op(name)
                if o is not None:
                    o.par.reloadpulse.pulse()
    me.store('st', st)
    return
''' % BRIDGE

import json as _json
_cal = None
try:
    _c = _json.load(open(BRIDGE + '/calibration_test.json'))
    _cal = {'dx_mid': (_c['left']['dbg']['dx'] + _c['right']['dbg']['dx']) / 2,
            'dx_span': _c['right']['dbg']['dx'] - _c['left']['dbg']['dx']}
    for _k in ('nosey', 'facey', 'dy'):
        _u, _d = _c['up']['dbg'][_k], _c['down']['dbg'][_k]
        _cal[_k + '_mid'] = (_u + _d) / 2
        _cal[_k + '_span'] = _d - _u
    print('已读入校准:', {k: round(v, 4) for k, v in _cal.items()})
except Exception as e:
    print('没有找到可用校准（用默认放大倍数）:', repr(e))
EXEC_CODE = EXEC_CODE.replace('__CAL__', repr(_cal))

try:
    p = ui.panes.current.owner      # 你当前打开的那个网络窗口
except Exception:
    p = None
if p is None or not hasattr(p, 'create'):
    p = op('/project1')
print('将创建在:', p.path)
out = p.op('gz_out') or p.create(moviefileinTOP, 'gz_out')
heat = p.op('gz_heat') or p.create(moviefileinTOP, 'gz_heat')
out.par.file = BRIDGE + '/out.png'
heat.par.file = BRIDGE + '/heat.png'
kb = p.op('gz_kb') or p.create(keyboardinCHOP, 'gz_kb')
try:
    kb.par.keys = 'n v a s'
except Exception as e:
    print('keyboardin keys 设置失败（手动在 gz_kb 的 Keys 里填 n）:', e)
ex = p.op('gz_exec') or p.create(executeDAT, 'gz_exec')
ex.text = EXEC_CODE
ex.par.frameend = True
ex.par.active = True
out.nodeX, out.nodeY = 0, -600
heat.nodeX, heat.nodeY = 250, -600
kb.nodeX, kb.nodeY = 500, -600
ex.nodeX, ex.nodeY = 750, -600
print('OK: 已创建 gz_out, gz_heat, gz_kb, gz_exec，位置:', p.path)

# --- 切换 + 放大成整屏 ---
src0 = p.op('null1') or out
src1 = p.op('null2') or heat
sw = p.op('gz_switch') or p.create(switchTOP, 'gz_switch')
sw.inputConnectors[0].connect(src0)
sw.inputConnectors[1].connect(src1)
ai = p.op('gz_ai') or p.create(moviefileinTOP, 'gz_ai')
ai.par.file = BRIDGE + '/ai_heat.png'
ai.nodeX, ai.nodeY = 750, -600
try:
    sw.inputConnectors[2].connect(ai)
except Exception as e:
    print('gz_switch 第 3 个输入连接失败，请手动把 gz_ai 拖到 gz_switch：', e)
sw.par.index = 0
fit = p.op('gz_fit') or p.create(fitTOP, 'gz_fit')
tile = p.op('gz_tile') or p.create(transformTOP, 'gz_tile')
tile.inputConnectors[0].connect(sw)
try:
    tile.par.extend = 'mirror'   # 镜像平铺（想要普通重复改成 'repeat'）
except Exception as e:
    print('gz_tile 的 extend 设置失败，请手动选 Mirror:', e)
fit.inputConnectors[0].connect(tile)
tile.nodeX, tile.nodeY = 250, -950
try:
    W, H = monitors[0].scaledWidth, monitors[0].scaledHeight    # 点（不是像素）：视网膜屏的窗口用点
except Exception:
    W, H = 1920, 1080
try:
    fit.par.outputresolution = 'custom'
    fit.par.resolutionw = W
    fit.par.resolutionh = H
except Exception as e:
    print('gz_fit 分辨率设置失败，请手动在 gz_fit 里设:', e)
try:
    fit.par.fit = 'fill'
except Exception as e:
    print('gz_fit 的 Fit 设置失败，请手动选 Fill:', e)
sw.nodeX, sw.nodeY = 250, -800
fit.nodeX, fit.nodeY = 500, -800
win = p.op('gz_win')
if win is not None:
    win.par.winop = fit.path
    print('gz_win 已改成读取 gz_fit')
else:
    print('没找到 gz_win，请手动把 gz_win 的 Window Operator 设成', fit.path)

# --- 空气乐器：air_note(5 个音) -> air_out(MIDI Out，ID 2 = IAC Driver Bus 1，发给 GarageBand) ---
an = p.op('air_note') or p.create(constantCHOP, 'air_note')
_def_notes = [48 + 12 * _o + _iv for _o in range(3) for _iv in (0, 2, 4, 7, 9)] + [84]
for _i in range(32):
    setattr(an.par, 'name%d' % _i, ('ch1n%d' % _def_notes[_i]) if _i < len(_def_notes) else ('unused%d' % _i))
    setattr(an.par, 'value%d' % _i, 0)
ao = p.op('air_out') or p.create(midioutCHOP, 'air_out')
try:
    ao.inputConnectors[0].connect(an)
    ao.par.id = '2'
except Exception as e:
    print('air_out 连接/设置失败，请手动：', e)
print('空气乐器节点就绪（按 TD 里的 A 键开/关；默认关）')

# --- TD 声音链：snd_in(BlackHole) -> snd_gain -> snd_clip -> snd_vol -> snd_out（默认静音 snd_vol.gain=0）---
_si = p.op('snd_in') or p.create(audiodeviceinCHOP, 'snd_in')
try:
    _si.par.device = 'BlackHole2ch_UID'
except Exception as e:
    print('snd_in 设备设置失败，请手动选 BlackHole 2ch:', e)
_sg = p.op('snd_gain') or p.create(mathCHOP, 'snd_gain')
_sc = p.op('snd_clip') or p.create(limitCHOP, 'snd_clip')
_sv = p.op('snd_vol') or p.create(mathCHOP, 'snd_vol')
_so = p.op('snd_out') or p.create(audiodeviceoutCHOP, 'snd_out')
_sg.inputConnectors[0].connect(_si)
_sc.inputConnectors[0].connect(_sg)
_sv.inputConnectors[0].connect(_sc)
_so.inputConnectors[0].connect(_sv)
try:
    _sc.par.type = 'clamp'
except Exception as e:
    print('snd_clip 的 type 设置失败，请手动选 clamp:', e)
_sg.par.gain = 15
_sv.par.gain = 0
print('TD 声音链就绪（默认静音；琴上第 3 个打击垫开/关声音）')

# --- 拍手：clap_in(麦克风) -> gz_exec 里 _update_clap 判断 ---
_ci = p.op('clap_in') or p.create(audiodeviceinCHOP, 'clap_in')
try:
    _ci.par.device = 'BuiltInMicrophoneDevice'
    _ci.par.numchan = 1
except Exception as e:
    print('clap_in 设备设置失败，请手动选 MacBook Pro Microphone:', e)
_ci.nodeX, _ci.nodeY = 0, -1900
print('拍手监听就绪（clap_in 听 MacBook 麦克风；macOS 可能会问你要不要允许 TouchDesigner 使用麦克风，请点允许）')

# --- 脸的群像：crowd_bg(黑底) + cf0..cf19(每张脸一个变换) -> crowd_comp(叠合) ；gz_mode 在 镜像(gz_tile) 和 群像(crowd_comp) 间切换 ---
_bg = p.op('crowd_bg') or p.create(constantTOP, 'crowd_bg')
try:
    _bg.par.outputresolution = 'custom'
    _bg.par.resolutionw = W
    _bg.par.resolutionh = H
    _bg.par.colorr = 0
    _bg.par.colorg = 0
    _bg.par.colorb = 0
except Exception as e:
    print('crowd_bg 设置失败:', e)
_comp = p.op('crowd_comp') or p.create(compositeTOP, 'crowd_comp')
try:
    _comp.par.operand = 'brightest'      # 'over' 在这里输出纯黑（实测），改成每个像素取最亮的
except Exception as e:
    print('crowd_comp 的 operand 设置失败，请手动选 Brightest:', e)
_comp.inputConnectors[0].connect(_bg)
for _i in range(20):
    _cf = p.op('cf' + str(_i)) or p.create(transformTOP, 'cf' + str(_i))
    _cf.inputConnectors[0].connect(sw)
    try:
        _cf.par.extend = 'zero'
        _cf.par.outputresolution = 'custom'
        _cf.par.resolutionw = W
        _cf.par.resolutionh = H
        _cf.par.sx = 0.0001
        _cf.par.sy = 0.0001
    except Exception as e:
        print('cf' + str(_i), '设置失败:', e)
    _comp.inputConnectors[_i + 1].connect(_cf)
    _cf.nodeX, _cf.nodeY = 1200 + 160 * (_i % 10), -950 - 140 * (_i // 10)
_bg.nodeX, _bg.nodeY = 1000, -800
_comp.nodeX, _comp.nodeY = 1000, -1300
_gm = p.op('gz_mode') or p.create(switchTOP, 'gz_mode')
_gm.inputConnectors[0].connect(tile)
_gm.inputConnectors[1].connect(_comp)
_xf = p.op('gz_xfade') or p.create(crossTOP, 'gz_xfade')
_xf.inputConnectors[0].connect(tile)
_xf.inputConnectors[1].connect(_comp)
try:
    _xf.par.cross = 1.0
except Exception as e:
    print('gz_xfade 的 cross 参数设置失败（名字可能不对），请把下面这行发给我:', [x.name for x in _xf.pars()][:30], e)
_at = p.op('gz_attn') or p.create(moviefileinTOP, 'gz_attn')
_at.par.file = BRIDGE + '/ai_attn.png'
_at.nodeX, _at.nodeY = 700, -1300
_xf2 = p.op('gz_xfade2') or p.create(crossTOP, 'gz_xfade2')
_xf2.inputConnectors[0].connect(_xf)
_xf2.inputConnectors[1].connect(_at)
try:
    _xf2.par.cross = 0.0
except Exception as e:
    print('gz_xfade2 的 cross 设置失败:', e)
fit.inputConnectors[0].connect(_xf2)
_xf2.nodeX, _xf2.nodeY = 950, -1100
_xf.nodeX, _xf.nodeY = 700, -1100
_gm.nodeX, _gm.nodeY = 700, -950
print('脸群像就绪：audio_fx.json 里 visual_mode 可切换 crowd / mirror')
