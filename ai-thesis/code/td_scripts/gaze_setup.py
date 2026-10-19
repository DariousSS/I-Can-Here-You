# 在 TD 的 Textport 里运行：
#   exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/code/td_scripts/gaze_setup.py', encoding='utf-8').read())
# 作用：新建/更新 gz_out、gz_heat、gz_kb、gz_exec、gz_switch、gz_tile、gz_fit，并让 gz_win 读 gz_fit。可重复运行。
BRIDGE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'

EXEC_CODE = '''
import json, os, time, re, random, math
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
               'air_x_lo': 0.12, 'air_x_hi': 0.88, 'air_flip_x': False, 'air_margin': 0.25, 'screen_w': 0, 'screen_h': 0, 'ball_on': True, 'ball_rise': 0.5, 'ball_hold': 2.2, 'ball_fall': 1.0, 'mapping_on': False, 'win_display': 0, 'auto_open_window': False, 'castle_ball_w': 1920, 'castle_ball_h': 640, 'ball_with_flash': False, 'castle_ball_auto': True, 'ball_auto_min': 0, 'ball_auto_max': 0, 'ball_every_switches': 3, 'ball_need_hand': True, 'ball_hand_sec': 4.0, 'castle_ball_phys_aspect': 0, 'castle_tiles_min': 3, 'hand_on': True, 'hand_need_hand': False, 'hand_target_max_frac': 0.5, 'poke_fx_on': True, 'poke_fx_amp': 1.0, 'puppet_on': True, 'puppet_need_hand': False, 'angel_on': True, 'angel_idle_level': 0.5, 'angel_x': 0.62, 'angel_y': 0.30, 'angel_scale': 0.75, 'angel_hold': 9.0, 'angel_auto_min': 60, 'angel_auto_max': 120, 'angel_follow_hand': True, 'puppet_every_switches': 0, 'puppet_auto_min': 0, 'puppet_auto_max': 0, 'puppet_hand_scale': 0.38, 'puppet_scale': 0.36, 'puppet_string_len': 0.17, 'puppet_rot_sign': 1, 'hand_scale': 0.6, 'hand_fps': 10, 'hand_every_switches': 0, 'hand_auto_min': 0, 'hand_auto_max': 0, 'hand_canvas_w': 1920, 'hand_canvas_h': 1080, 'castle_spin_deg_s': 6.0, 'scene_hold': {'mirror': 60, 'face': 12, 'attn': 25, 'crowd': 30}, 'scene_weights': {'face': 1, 'attn': 2, 'crowd': 1}, 'ball_sfx_vol': 0.6}
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
    """场景系统：镜像(万花筒)是主场景，停留最久；纯人脸(face)和黑白注意力图(attn)偶尔插进来，然后回到镜像。
    gz_xfade(Cross) 管 镜像<->群像，gz_xfade2(Cross) 再管 (它们)<->黑白图；castle_mix 管城堡方块上 万花筒<->纯人脸。"""
    cfg = _fx_cfg(st)
    st['sc_age'] = st.get('sc_age', 0) + 1
    if st['sc_age'] >= 30:                      # 每约半秒清掉"上次写了什么"的记忆，强制把值重新写给节点（重装脚本会把节点重置，不清的话画面会卡住）
        st['sc_age'] = 0
        for k_ in ('xf_set', 'xa_set', 'cx_set', 'cm_set'):
            st.pop(k_, None)
    mode = cfg.get('visual_mode', 'auto')
    valid = ('crowd', 'mirror', 'attn', 'face')
    scenes = [x_ for x_ in (cfg.get('scenes') or ['mirror']) if x_ in valid] or ['mirror']
    now = time.time()
    cur = st.get('scene')
    if mode == 'auto':
        if cur not in scenes:
            cur = 'mirror' if 'mirror' in scenes else scenes[0]
            st['scene_t'] = now
        if st.get('scene_t') is None:
            st['scene_t'] = now
        holds = cfg.get('scene_hold') or {}
        hold = float(holds.get(cur, cfg.get('scene_auto_sec', 45)))
        go = st.pop('scene_next', False)
        if hold > 0 and now - st['scene_t'] > hold:
            go = True
        if go and len(scenes) > 1:
            others = [x_ for x_ in scenes if x_ != cur]
            if 'mirror' in scenes and cur != 'mirror':
                nxt = 'mirror'                                  # 从别的场景一律先回到镜像
            else:
                wts = cfg.get('scene_weights') or {}
                nxt = random.choices(others, weights=[float(wts.get(x_, 1)) for x_ in others])[0]
            cur = nxt
            st['scene_t'] = now
            st['scene_i'] = st.get('scene_i', 0) + 1
            st['switches'] = st.get('switches', 0) + 1
            every = int(cfg.get('ball_every_switches', 3))
            if cfg.get('ball_on', True) and every > 0 and st['switches'] %% every == 0:
                st['ball_pending'] = now + 0.5                    # 夹在切换中间：切换开始半秒后，海洋球涌出来（要有手才触发）
            pev = int(cfg.get('puppet_every_switches', 0))
            if cfg.get('puppet_on', True) and pev > 0 and st['switches'] %% pev == 0:
                st['puppet_pending'] = now + 1.0
            hev = int(cfg.get('hand_every_switches', 0))
            if cfg.get('hand_on', True) and hev > 0 and st['switches'] %% hev == 0:
                st['hand_pending'] = now + 1.0
        scene = cur
    else:
        st.pop('scene_next', None)
        scene = mode if mode in valid else 'mirror'
    st['scene'] = scene
    speed = float(cfg.get('xfade_speed', 0.06))
    if 'crowd' not in scenes:
        tx_ = 0.0                                 # 轮换里没有脸群：始终停在镜像，不让脸群在黑白图切换时透出来
    elif scene in ('crowd', 'mirror', 'face'):
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
    tm_ = 1.0 if scene == 'face' else 0.0
    cm = st.get('cm', tm_)
    cm += (tm_ - cm) * speed
    if abs(tm_ - cm) < 0.002:
        cm = tm_
    st['cm'] = cm
    node = op('gz_xfade')
    if node is not None and abs(xf - st.get('xf_set', -1.0)) > 0.002:
        node.par.cross = xf
        st['xf_set'] = xf
    node2 = op('gz_xfade2')
    if node2 is not None and abs(xa - st.get('xa_set', -1.0)) > 0.002:
        node2.par.cross = xa
        st['xa_set'] = xa
    cx = op('castle_xf')
    if cx is not None and abs(xa - st.get('cx_set', -1.0)) > 0.002:
        cx.par.cross = xa
        st['cx_set'] = xa
    cmix = op('castle_mix')
    if cmix is not None and abs(cm - st.get('cm_set', -1.0)) > 0.002:
        cmix.par.cross = cm
        st['cm_set'] = cm


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
    ct = op('castle_tile')
    if ct is not None:
        cfg_ = _fx_cfg(st)
        sc_c = 1.0 / max(float(cfg_.get('castle_tiles_min', 3)), tc)      # 城堡万花筒：至少平铺这么多张，琴键/手让它更多
        if abs(sc_c - st.get('ctile_s', -1.0)) > 0.002:
            ct.par.sx = sc_c
            ct.par.sy = sc_c
            st['ctile_s'] = sc_c
        spin = float(cfg_.get('castle_spin_deg_s', 6.0))
        rot = (time.time() * spin) %% 360.0
        if abs(rot - st.get('ctile_r', -9.0)) > 0.3:
            ct.par.rotate = rot
            st['ctile_r'] = rot


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


def _update_screen(st):
    """自动适应屏幕：每约 1 秒看一次主屏幕大小（或 audio_fx.json 里手动指定的 screen_w/screen_h），变了就更新所有跟屏幕大小有关的节点。"""
    st['scr_age'] = st.get('scr_age', 999) + 1
    if st['scr_age'] < 30:
        return
    st['scr_age'] = 0
    cfg = _fx_cfg(st)
    try:
        W, H = int(cfg.get('screen_w', 0)), int(cfg.get('screen_h', 0))
        if W <= 0 or H <= 0:
            m = monitors[0]
            W, H = int(m.scaledWidth), int(m.scaledHeight)
    except Exception:
        return
    if W < 64 or H < 64 or (W, H) == st.get('scr_wh'):
        return
    st['scr_wh'] = (W, H)
    names = ['gz_fit', 'gz_tile', 'crowd_bg', 'ball_fit', 'map_fit', 'hand_fit'] + ['cf' + str(i_) for i_ in range(CROWD_N)]
    for nm in names:
        o = op(nm)
        if o is None:
            continue
        try:
            o.par.outputresolution = 'custom'
            o.par.resolutionw = W
            o.par.resolutionh = H
        except Exception:
            pass
    st['crowd_layout'] = None            # 屏幕比例变了，脸群重新排一次
    print('gz_exec 屏幕大小变为', W, 'x', H, '，已自动调整')


_BOOT = {'t': None, 'opened': False}      # 只在这次启动里有效（不存进 .toe），所以每次打开 TD 都会重新判断


def _update_output(st):
    """输出：mapping_on=true 时窗口显示 Kantan Mapper 对准后的画面，否则显示原画面；win_display 选哪块屏幕；auto_open_window=true 时打开 TD 后约 8 秒自动打开表演窗口。"""
    st['out_age'] = st.get('out_age', 99) + 1
    if st['out_age'] < 30:
        return
    st['out_age'] = 0
    cfg = _fx_cfg(st)
    w = op('gz_win')
    if w is None:
        return
    want = '/project1/gz_final' if op('gz_final') is not None else '/project1/gz_over'
    if cfg.get('mapping_on', False):
        k = op('map_fit')
        if k is not None:
            want = k.path
    if str(w.par.winop.eval()) != want:
        w.par.winop = want
        print('gz_exec 输出已切换为', want)
    fx = op('poke_fx')
    mf = op('map_fit')
    msel = op('map_sel')
    if fx is not None and mf is not None and msel is not None:
        try:
            err = str(fx.errors() or '').strip()
        except Exception:
            err = ''
        want_in = msel if (err or not cfg.get('poke_fx_on', True)) else fx
        cur_in = mf.inputs[0] if mf.inputs else None
        if cur_in is None or cur_in.path != want_in.path:
            mf.inputConnectors[0].connect(want_in)
            if err:
                print('gz_exec 水波特效着色器有错，已绕开特效（画面不受影响）:', err[:200])
    try:
        disp = int(cfg.get('win_display', 0))
        if int(w.par.display.eval()) != disp:
            w.par.display = disp
    except Exception:
        pass
    if _BOOT['t'] is None:
        _BOOT['t'] = time.time()
    if cfg.get('auto_open_window', False) and not _BOOT['opened'] and time.time() - _BOOT['t'] > 8.0:
        _BOOT['opened'] = True
        w.par.winopen.pulse()
        print('gz_exec 已自动打开表演窗口')


BALL_FRAMES = 96                       # 海洋球动画一共多少帧（make_ballseq.py 生成）
BALL_FPS = 30


def _ball_go(st, cfg):
    """开始一次海洋球（从第 0 帧播），并放音效。"""
    st['ball_t0'] = time.time()
    st['ball_idx'] = -1
    try:
        vol = float(cfg.get('ball_sfx_vol', 0.6))
        sfx = os.path.normpath(os.path.join(BRIDGE, '..', 'ballpit', 'ball_sfx.wav'))
        if vol > 0 and os.path.exists(sfx):
            import subprocess
            subprocess.Popen(['afplay', '-v', str(min(1.0, vol)), sfx], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _update_ballsize(st):
    """让城堡底部的海洋球画面自动匹配 Kantan 里"球形状"的长宽比：找纹理是 castle_ball_tf 的形状，读它四个角的坐标算比例。"""
    st['bs_age'] = st.get('bs_age', 99) + 1
    if st['bs_age'] < 30:
        return
    st['bs_age'] = 0
    cfg = _fx_cfg(st)
    if not cfg.get('castle_ball_auto', True):
        return
    f2 = op('castle_ball_fit')
    root = op('kantanMapper/project/allShapes')
    if f2 is None or root is None:
        return
    for c in root.children:
        pr = c.op('parameters')
        if pr is None or not hasattr(pr.par, 'Texture'):
            continue
        v = pr.par.Texture.eval()
        if str(getattr(v, 'path', v)) != '/project1/castle_ball_tf':
            continue
        sc = c.op('script1')
        if sc is None:
            continue
        pts = [(q.x, q.y) for q in sc.points]
        if len(pts) < 4:
            continue
        def _d(a_, b_):
            return ((a_[0] - b_[0]) ** 2 + (a_[1] - b_[1]) ** 2) ** 0.5
        w_ = (_d(pts[0], pts[1]) + _d(pts[3], pts[2])) / 2.0
        h_ = (_d(pts[0], pts[3]) + _d(pts[1], pts[2])) / 2.0
        if w_ < 4 or h_ < 4:
            continue
        asp = w_ / h_
        phys = float(cfg.get('castle_ball_phys_aspect', 0))
        if phys > 0:
            asp = phys                                    # 手动指定：纸箱实物的 宽/高（比如三个并排的方块就是 3）
        if st.get('cb_asp') is not None and abs(asp - st['cb_asp']) / st['cb_asp'] < 0.02:
            return
        st['cb_asp'] = asp
        longside = 1280
        if asp >= 1.0:
            rw, rh = longside, max(64, int(round(longside / asp)))
        else:
            rw, rh = max(64, int(round(longside * asp))), longside
        f2.par.resolutionw = rw
        f2.par.resolutionh = rh
        st['cb_wh'] = (rw, rh)
        print('gz_exec 海洋球画面已按长方形比例调整:', rw, 'x', rh)
        return


def _hands_recent(st, cfg):
    """最近 ball_hand_sec 秒内，摄像头是不是看到过手（空气琴开不开都算）。"""
    now = time.time()
    try:
        for n in _hand_nodes():
            if n is not None and len(list(n.points)) > 20:
                st['hand_t'] = now
                break
    except Exception:
        pass
    return now - st.get('hand_t', -999.0) <= float(cfg.get('ball_hand_sec', 4.0))


def _update_ball(st):
    """海洋球：1) 切换场景时每隔几次（ball_every_switches）在切换中间涌出来，而且要有手在摄像头里才触发；
    2) 可选：诡异声音一起触发(ball_with_flash)、随机触发(ball_auto_min/max)。
    主画面用整屏版动画(seq)，城堡底部长方形用长条版动画(seq_strip)。"""
    cfg = _fx_cfg(st)
    tf = op('ball_tf')
    img = op('ball_img')
    if tf is None or img is None:
        return
    st['ball_age'] = st.get('ball_age', 99) + 1
    if st['ball_age'] >= 6:
        st['ball_age'] = 0
        t_new = None
        try:
            with open(BRIDGE + '/flash.json', encoding='utf-8') as fh:
                t_new = float(json.load(fh).get('t', 0.0))
        except Exception:
            t_new = None
        if st.get('flash_seen') is None:
            st['flash_seen'] = t_new if t_new is not None else 0.0       # 第一次只记下旧事件，不触发
        elif t_new is not None and t_new > st['flash_seen']:
            st['flash_seen'] = t_new
            if cfg.get('ball_on', True) and cfg.get('ball_with_flash', False):
                _ball_go(st, cfg)
        hands = _hands_recent(st, cfg)
        pend = st.get('ball_pending')
        if pend is not None and time.time() >= pend:
            st['ball_pending'] = None
            if cfg.get('ball_on', True) and st.get('ball_t0') is None and (hands or not cfg.get('ball_need_hand', True)):
                _ball_go(st, cfg)
        lo_, hi_ = float(cfg.get('ball_auto_min', 0)), float(cfg.get('ball_auto_max', 0))
        if cfg.get('ball_on', True) and lo_ > 0 and hi_ >= lo_:
            if st.get('ball_next') is None:
                st['ball_next'] = time.time() + random.uniform(lo_, hi_)
            elif time.time() >= st['ball_next'] and st.get('ball_t0') is None:
                st['ball_next'] = time.time() + random.uniform(lo_, hi_)
                if hands or not cfg.get('ball_need_hand', True):
                    _ball_go(st, cfg)
    t0 = st.get('ball_t0')
    show = False
    if t0 is not None and cfg.get('ball_on', True):
        idx = int((time.time() - t0) * BALL_FPS)
        if idx >= BALL_FRAMES:
            st['ball_t0'] = None
        else:
            show = True
            if idx != st.get('ball_idx'):
                fn = 'ball_' + str(idx).zfill(4) + '.png'
                img.par.file = os.path.normpath(os.path.join(BRIDGE, '..', 'ballpit', 'seq', fn))
                img2 = op('castle_ball_img')
                if img2 is not None:
                    img2.par.file = os.path.normpath(os.path.join(BRIDGE, '..', 'ballpit', 'seq_strip', fn))
                st['ball_idx'] = idx
    ty = 0.0 if show else -1.05
    if ty != st.get('ball_ty'):
        tf.par.ty = ty
        st['ball_ty'] = ty
    tf2 = op('castle_ball_tf')
    if tf2 is not None:
        if ty != st.get('ball_ty2'):
            tf2.par.ty = ty
            st['ball_ty2'] = ty
        cw, ch = int(cfg.get('castle_ball_w', 1920)), int(cfg.get('castle_ball_h', 640))
        if (not cfg.get('castle_ball_auto', True)) and (cw, ch) != st.get('cb_wh') and cw >= 64 and ch >= 64:
            f2 = op('castle_ball_fit')
            if f2 is not None:
                f2.par.resolutionw = cw
                f2.par.resolutionh = ch
                st['cb_wh'] = (cw, ch)


_HAND = {'meta': None}


def _hand_meta():
    if _HAND['meta'] is None:
        try:
            with open(os.path.normpath(os.path.join(BRIDGE, '..', '..', 'assets', 'hand', 'hand_sprite.json')), encoding='utf-8') as fh:
                _HAND['meta'] = json.load(fh)
        except Exception:
            _HAND['meta'] = {'w': 1536, 'h': 1024, 'tip_u': 0.791, 'tip_v': 0.9033}
    return _HAND['meta']


def _ease_out(x_):
    return 1.0 - (1.0 - min(1.0, max(0.0, x_))) ** 3


def _ease_in(x_):
    x_ = min(1.0, max(0.0, x_))
    return x_ * x_ * x_


def _ease_io(x_):
    x_ = min(1.0, max(0.0, x_))
    return 3.0 * x_ * x_ - 2.0 * x_ * x_ * x_


def _hand_tip(t, S, Hv, P):
    """手指尖在画布上的位置(像素)随时间的变化：伸进来 -> 悬停(轻轻抖) -> 戳一下 -> 停 -> 缩回去。返回 (x, y, 是否还在动画里)。"""
    T1, T2, T3, T4, T5 = 2.2, 1.3, 0.35, 0.5, 1.8
    if t < T1:
        k = _ease_out(t / T1)
        return S[0] + (Hv[0] - S[0]) * k, S[1] + (Hv[1] - S[1]) * k, True
    t -= T1
    if t < T2:
        return Hv[0] + 7.0 * math.sin(t * 5.0), Hv[1] + 5.0 * math.sin(t * 3.7 + 1.0), True
    t -= T2
    if t < T3:
        k = _ease_io(t / T3)
        return Hv[0] + (P[0] - Hv[0]) * k, Hv[1] + (P[1] - Hv[1]) * k, True
    t -= T3
    if t < T4:
        return P[0] + 2.0 * math.sin(t * 40.0), P[1], True
    t -= T4
    if t < T5:
        k = _ease_in(t / T5)
        return P[0] + (S[0] - P[0]) * k, P[1] + (S[1] - P[1]) * k, True
    return S[0], S[1], False


def _hand_target(cfg):
    """手要戳的位置：从 Kantan 里随机挑一个城堡形状，在它【朝外的边】上随机取一点（画布像素）。找不到就用默认位置。"""
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    root = op('kantanMapper/project/allShapes')
    shapes = []
    allx, ally = [], []
    if root is not None:
        for c in root.children:
            pr = c.op('parameters')
            if pr is None or not hasattr(pr.par, 'Texture'):
                continue
            v = pr.par.Texture.eval()
            if str(getattr(v, 'path', v)) != '/project1/castle_xf':
                continue
            sc = c.op('script1')
            if sc is None:
                continue
            pts = [(Wc / 2.0 + q.x, Hc / 2.0 - q.y) for q in sc.points]
            if len(pts) >= 3:
                shapes.append(pts)
                allx += [q[0] for q in pts]
                ally += [q[1] for q in pts]
    if not shapes:
        return (Wc * 0.5, Hc * 0.6)
    ccx, ccy = (min(allx) + max(allx)) / 2.0, (min(ally) + max(ally)) / 2.0
    edges = []
    for pts in shapes:
        n_ = len(pts)
        for i_ in range(n_):
            a_, b_ = pts[i_], pts[(i_ + 1) %% n_]
            mx, my = (a_[0] + b_[0]) / 2.0, (a_[1] + b_[1]) / 2.0
            if ((a_[0] - b_[0]) ** 2 + (a_[1] - b_[1]) ** 2) ** 0.5 < 20:
                continue
            if a_[1] > max(ally) - 25 and b_[1] > max(ally) - 25:
                continue                                           # 不选城堡最底下的边
            edges.append((((mx - ccx) ** 2 + (my - ccy) ** 2) ** 0.5, a_, b_))
    if not edges:
        return (Wc * 0.5, Hc * 0.6)
    ytop_, ybot_ = min(ally), max(ally)
    ylim = ytop_ + float(cfg.get('hand_target_max_frac', 0.5)) * (ybot_ - ytop_)
    upper = [e_ for e_ in edges if (e_[1][1] + e_[2][1]) / 2.0 <= ylim]        # 只选城堡上半部分的边（手不会从很低的地方伸出来）
    if upper:
        edges = upper
    edges.sort(key=lambda e_: -e_[0])
    pick = random.choice(edges[:max(1, len(edges) // 2)])          # 离城堡中心最远的一半边 = 朝外的边
    t_ = random.uniform(0.25, 0.75)
    return (pick[1][0] + (pick[2][0] - pick[1][0]) * t_, pick[1][1] + (pick[2][1] - pick[1][1]) * t_)


def _update_hand(st):
    """巨大的木头手：从左上角伸进来，悬停，戳一下某个城堡方块，再缩回去。触发：test_hand.py、每隔几次切换场景、或随机。"""
    cfg = _fx_cfg(st)
    tf = op('hand_out')
    if tf is None:
        return
    st['hand_age'] = st.get('hand_age', 99) + 1
    if st['hand_age'] >= 6:
        st['hand_age'] = 0
        t_new = None
        try:
            with open(BRIDGE + '/hand_test.json', encoding='utf-8') as fh:
                t_new = float(json.load(fh).get('t', 0.0))
        except Exception:
            t_new = None
        if st.get('hand_seen') is None:
            st['hand_seen'] = t_new if t_new is not None else 0.0
        elif t_new is not None and t_new > st['hand_seen']:
            st['hand_seen'] = t_new
            st['hand_pending'] = time.time()
        present_ok = (not cfg.get('hand_need_hand', False)) or _hands_recent(st, cfg)       # 要求有人在（摄像头最近看到手）才触发
        pend = st.get('hand_pending')
        if pend is not None and time.time() >= pend:
            st['hand_pending'] = None
            if cfg.get('hand_on', True) and st.get('hand_t0') is None and st.get('pup_t0') is None and present_ok:
                _hand_start(st, cfg)
        lo_, hi_ = float(cfg.get('hand_auto_min', 0)), float(cfg.get('hand_auto_max', 0))
        if cfg.get('hand_on', True) and lo_ > 0 and hi_ >= lo_:
            if st.get('hand_next') is None:
                st['hand_next'] = time.time() + random.uniform(lo_, hi_)
            elif time.time() >= st['hand_next'] and st.get('hand_t0') is None and st.get('pup_t0') is None:
                st['hand_next'] = time.time() + random.uniform(lo_, hi_)
                if present_ok:
                    _hand_start(st, cfg)
    t0 = st.get('hand_t0')
    if t0 is None or not cfg.get('hand_on', True):
        if st.get('hand_vis', True):
            tf.par.sx = 0.0001
            tf.par.sy = 0.0001
            st['hand_vis'] = False
        return
    fps = max(1.0, float(cfg.get('hand_fps', 10)))
    t = math.floor((time.time() - t0) * fps) / fps               # 定格动画：时间按 fps 取整，一顿一顿的
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    m = _hand_meta()
    Wp = float(cfg.get('hand_scale', 0.6)) * Wc
    Hp = Wp * float(m['h']) / float(m['w'])
    tu, tv = float(m['tip_u']), float(m['tip_v'])
    S = (-(1.0 - tu) * Wp - 60.0, -(1.0 - tv) * Hp - 60.0)       # 起点：整只手都在画布左上角之外
    P = st['hand_P']
    Hv = (max(0.12 * Wc, P[0] - 0.14 * Wc), max(0.10 * Hc, P[1] - 0.20 * Hc))
    x, y, alive = _hand_tip(t, S, Hv, P)
    if not alive:
        st['hand_t0'] = None
        return
    cx = x - (tu - 0.5) * Wp
    cy = y - (tv - 0.5) * Hp
    tf.par.sx = Wp / Wc
    tf.par.sy = Hp / Hc
    tf.par.tx = (cx - Wc / 2.0) / Wc
    tf.par.ty = (Hc / 2.0 - cy) / Hc
    tf.par.rotate = 1.5 * math.sin(t * 2.3)
    st['hand_vis'] = True


def _hand_start(st, cfg):
    st['hand_P'] = _hand_target(cfg)
    st['hand_t0'] = time.time()
    st['poke_time'] = st['hand_t0'] + 2.2 + 1.3 + 0.35        # 指尖碰到城堡的时刻（和 _hand_tip 的时间表一致）
    st['poke_P'] = st['hand_P']
    print('gz_exec 木头手出现，目标位置:', int(st['hand_P'][0]), int(st['hand_P'][1]))


_PUP = {'meta': None, 'rmeta': None}


def _puppet_meta():
    if _PUP['meta'] is None:
        try:
            with open(os.path.normpath(os.path.join(BRIDGE, '..', '..', 'assets', 'puppet', 'puppet.json')), encoding='utf-8') as fh:
                _PUP['meta'] = json.load(fh)
        except Exception:
            _PUP['meta'] = {'w': 600, 'h': 900, 'attach': [[0.30, 0.04], [0.70, 0.04], [0.12, 0.52], [0.88, 0.52]]}
        try:
            with open(os.path.normpath(os.path.join(BRIDGE, '..', '..', 'assets', 'hand', 'hand_sprite_R.json')), encoding='utf-8') as fh:
                _PUP['rmeta'] = json.load(fh)
        except Exception:
            _PUP['rmeta'] = {'w': 1536, 'h': 1024, 'tip_u': 0.209, 'tip_v': 0.9033}
    return _PUP['meta'], _PUP['rmeta']


def _castle_box(cfg):
    """所有城堡方块（纹理是 castle_xf 的形状）在画布上的包围盒 (x0, y0, x1, y1) 像素；找不到就给个默认值。"""
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    root = op('kantanMapper/project/allShapes')
    xs, ys = [], []
    if root is not None:
        for c in root.children:
            pr = c.op('parameters')
            if pr is None or not hasattr(pr.par, 'Texture'):
                continue
            v = pr.par.Texture.eval()
            if str(getattr(v, 'path', v)) != '/project1/castle_xf':
                continue
            sc = c.op('script1')
            if sc is None:
                continue
            for q in sc.points:
                xs.append(Wc / 2.0 + q.x)
                ys.append(Hc / 2.0 - q.y)
    if xs:
        return (min(xs), min(ys), max(xs), max(ys))
    return (Wc * 0.2, Hc * 0.1, Wc * 0.8, Hc * 0.95)


def _puppet_geom(cfg, box=None):
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    pm, rm = _puppet_meta()
    lm = _hand_meta()
    x0, y0, x1, y1 = box if box is not None else _castle_box(cfg)
    ph = float(cfg.get('puppet_scale', 0.36)) * Hc
    pw = ph * float(pm['w']) / float(pm['h'])
    hw = float(cfg.get('puppet_hand_scale', 0.38)) * Wc
    hh = hw * float(lm['h']) / float(lm['w'])
    cx = (x0 + x1) / 2.0
    Yc = min(0.80 * Hc, max(0.58 * Hc, y0 + 0.55 * (y1 - y0)))          # 兔子停在城堡高度的中部偏下一点，手才露得出来
    L = float(cfg.get('puppet_string_len', 0.17)) * Hc
    return {'Wc': Wc, 'Hc': Hc, 'cx': cx, 'Yc': Yc, 'pw': pw, 'ph': ph, 'hw': hw, 'hh': hh, 'L': L,
            'attach': pm['attach'], 'tuL': float(lm['tip_u']), 'tvL': float(lm['tip_v']), 'tuR': float(rm['tip_u']), 'tvR': float(rm['tip_v'])}


def _puppet_pose(t, G, S, fps):
    """木偶戏的一帧：t=开始后的秒数。两只手的指尖位置由编排给出；兔子是弹簧-阻尼系统（会摆动）。S 保存兔子的速度等状态。
    返回 dict 或 None（演完了）。"""
    T_in, T_perf, T_out = 2.5, 8.0, 2.5
    if t >= T_in + T_perf + T_out:
        return None
    Wc, Hc = G['Wc'], G['Hc']
    if t < T_in:
        off = -(Hc * 0.9) * (1.0 - _ease_out(t / T_in))                      # 从画面上方降下来
    elif t > T_in + T_perf:
        off = -(Hc * 0.9) * _ease_in((t - T_in - T_perf) / T_out)            # 往上提走
    else:
        off = 0.0
    perf = max(0.0, min(t - T_in, T_perf))
    D = 0.17 * Wc
    tipy0 = G['Yc'] - 0.46 * G['ph'] - G['L']
    sway = 0.05 * Wc * math.sin(perf * 0.9)
    bob = 0.035 * Hc
    hop = 0.0
    if 3.5 < perf < 4.6:
        hop = -0.09 * Hc * math.sin((perf - 3.5) / 1.1 * math.pi)            # 手猛地一提：兔子被甩起来
    tipL = (G['cx'] - D + sway + 0.02 * Wc * math.sin(perf * 2.1), tipy0 + off + bob * math.sin(perf * 2.6) + hop)
    tipR = (G['cx'] + D + sway - 0.02 * Wc * math.sin(perf * 2.1), tipy0 + off + bob * math.sin(perf * 2.6 + 3.14) + hop)
    mid = ((tipL[0] + tipR[0]) / 2.0, (tipL[1] + tipR[1]) / 2.0)
    tgt = (mid[0], mid[1] + G['L'] + 0.46 * G['ph'])
    if S.get('t') is None:
        S.update({'t': t, 'x': tgt[0], 'y': tgt[1], 'vx': 0.0, 'vy': 0.0, 'a': 0.0, 'av': 0.0})
    n = max(1, int(round((t - S['t']) * 60.0)))
    h = (t - S['t']) / n if t > S['t'] else 1.0 / 60.0
    for _ in range(n):
        ax = 28.0 * (tgt[0] - S['x']) - 3.2 * S['vx']
        ay = 40.0 * (tgt[1] - S['y']) - 5.5 * S['vy']
        S['vx'] += ax * h
        S['vy'] += ay * h
        S['x'] += S['vx'] * h
        S['y'] += S['vy'] * h
        a_t = max(-16.0, min(16.0, -S['vx'] * 0.012 + 3.0 * math.sin(perf * 1.7)))   # 横向速度带动倾斜 + 轻轻自己晃
        aa = 38.0 * (a_t - S['a']) - 4.0 * S['av']
        S['av'] += aa * h
        S['a'] += S['av'] * h
    S['t'] = t
    th = math.radians(S['a'])                                                # 逆时针为正（和 TD 的 rotate 一致）
    att = []
    for u_, v_ in G['attach']:
        dx, dy = (u_ - 0.5) * G['pw'], (v_ - 0.5) * G['ph']
        att.append((S['x'] + dx * math.cos(th) + dy * math.sin(th), S['y'] - dx * math.sin(th) + dy * math.cos(th)))
    strings = [(tipL, att[0]), (tipL, att[2]), (tipR, att[1]), (tipR, att[3])]
    return {'tipL': tipL, 'tipR': tipR, 'pup': (S['x'], S['y']), 'ang': S['a'], 'strings': strings}


def _tf_sprite(par, cx, cy, Wp, Hp, Wc, Hc, rot=0.0):
    par.sx = Wp / Wc
    par.sy = Hp / Hc
    par.tx = (cx - Wc / 2.0) / Wc
    par.ty = (Hc / 2.0 - cy) / Hc
    par.rotate = rot


def _tf_string(par, A, B, width, Wc, Hc, sign):
    dx, dy = B[0] - A[0], B[1] - A[1]
    ln = max(1.0, (dx * dx + dy * dy) ** 0.5)
    phi = math.degrees(math.atan2(-dx, -dy)) * sign                          # 竖直的细长条转到沿着 A->B（y 向上坐标里 vx=dx, vy=-dy）
    par.sx = width / Wc
    par.sy = ln / Hc
    par.tx = ((A[0] + B[0]) / 2.0 - Wc / 2.0) / Wc
    par.ty = (Hc / 2.0 - (A[1] + B[1]) / 2.0) / Hc
    par.rotate = phi


def _puppet_hide():
    for nm in ('puppet_tf', 'pL_tf', 'pR_tf', 'pstr1', 'pstr2', 'pstr3', 'pstr4'):
        o = op(nm)
        if o is not None:
            o.par.sx = 0.0001
            o.par.sy = 0.0001


def _puppet_start(st, cfg):
    st['pup_G'] = _puppet_geom(cfg)
    st['pup_S'] = {}
    st['pup_t0'] = time.time()
    st['pup_q'] = -1
    print('gz_exec 木偶戏开始')


def _update_puppet(st):
    """木偶戏：两只木头手从上面降下来，手指拉着线，吊着小兔子在城堡前面摇摆，再提走。触发：test_puppet.py、每隔几次切换场景、随机。"""
    cfg = _fx_cfg(st)
    if op('puppet_tf') is None or op('pL_tf') is None:
        return
    st['pup_age'] = st.get('pup_age', 99) + 1
    if st['pup_age'] >= 6:
        st['pup_age'] = 0
        t_new = None
        try:
            with open(BRIDGE + '/puppet_test.json', encoding='utf-8') as fh:
                t_new = float(json.load(fh).get('t', 0.0))
        except Exception:
            t_new = None
        if st.get('pup_seen') is None:
            st['pup_seen'] = t_new if t_new is not None else 0.0
        elif t_new is not None and t_new > st['pup_seen']:
            st['pup_seen'] = t_new
            st['puppet_pending'] = time.time()
        pend = st.get('puppet_pending')
        busy = st.get('pup_t0') is not None or st.get('hand_t0') is not None
        pup_ok = (not cfg.get('puppet_need_hand', False)) or _hands_recent(st, cfg)   # 要求摄像头最近看到过手
        if pend is not None and time.time() >= pend and not busy:
            st['puppet_pending'] = None
            if cfg.get('puppet_on', True) and pup_ok:
                _puppet_start(st, cfg)
        lo_, hi_ = float(cfg.get('puppet_auto_min', 0)), float(cfg.get('puppet_auto_max', 0))
        if cfg.get('puppet_on', True) and lo_ > 0 and hi_ >= lo_:
            if st.get('pup_next') is None:
                st['pup_next'] = time.time() + random.uniform(lo_, hi_)
            elif time.time() >= st['pup_next'] and not busy:
                st['pup_next'] = time.time() + random.uniform(lo_, hi_)
                if pup_ok:
                    _puppet_start(st, cfg)
    t0 = st.get('pup_t0')
    if t0 is None or not cfg.get('puppet_on', True):
        if st.get('pup_vis', True):
            _puppet_hide()
            st['pup_vis'] = False
        return
    fps = max(1.0, float(cfg.get('hand_fps', 10)))
    q = int(math.floor((time.time() - t0) * fps))
    if q == st.get('pup_q'):
        return                                                              # 定格动画：同一格内不更新
    st['pup_q'] = q
    G = st['pup_G']
    pose = _puppet_pose(q / fps, G, st['pup_S'], fps)
    if pose is None:
        st['pup_t0'] = None
        return
    Wc, Hc = G['Wc'], G['Hc']
    sign = 1.0 if float(cfg.get('puppet_rot_sign', 1)) >= 0 else -1.0
    _tf_sprite(op('puppet_tf').par, pose['pup'][0], pose['pup'][1], G['pw'], G['ph'], Wc, Hc, sign * pose['ang'])
    tL, tR = pose['tipL'], pose['tipR']
    _tf_sprite(op('pL_tf').par, tL[0] - (G['tuL'] - 0.5) * G['hw'], tL[1] - (G['tvL'] - 0.5) * G['hh'], G['hw'], G['hh'], Wc, Hc)
    _tf_sprite(op('pR_tf').par, tR[0] - (G['tuR'] - 0.5) * G['hw'], tR[1] - (G['tvR'] - 0.5) * G['hh'], G['hw'], G['hh'], Wc, Hc)
    for i_, (A, B) in enumerate(pose['strings']):
        o = op('pstr' + str(i_ + 1))
        if o is not None:
            _tf_string(o.par, A, B, 4.0, Wc, Hc, sign)
    st['pup_vis'] = True


def _update_poke_fx(st):
    """手指碰到城堡的瞬间，从戳点荡开水波+故障（GLSL 着色器 poke_fx）。每帧把 戳点、戳了多少秒、强度 写给着色器。"""
    fx = op('poke_fx')
    if fx is None:
        return
    cfg = _fx_cfg(st)
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    pt = st.get('poke_time')
    amp = 0.0
    age = -1.0
    if pt is not None and cfg.get('poke_fx_on', True):
        age = time.time() - pt
        if -0.05 <= age <= 2.8:
            amp = float(cfg.get('poke_fx_amp', 1.0))
            age = max(0.0, age)
    key = (round(age, 3), amp)
    if key == st.get('fx_key'):
        return
    st['fx_key'] = key
    P_ = st.get('poke_P') or (Wc * 0.5, Hc * 0.5)
    fx.par.vec0valuex = P_[0] / Wc
    fx.par.vec0valuey = 1.0 - P_[1] / Hc
    fx.par.vec0valuez = age if amp > 0 else -1.0
    fx.par.vec0valuew = amp


_ANG = {'meta': None}


def _angel_meta():
    if _ANG['meta'] is None:
        try:
            with open(os.path.normpath(os.path.join(BRIDGE, '..', '..', 'assets', 'angel', 'angel.json')), encoding='utf-8') as fh:
                _ANG['meta'] = json.load(fh)['pixel']
        except Exception:
            _ANG['meta'] = {'w': 1254, 'h': 1254, 'eye_cx': 626.5, 'eye_cy': 547.0, 'pupil_r': 55.2, 'pupil_w': 128, 'pupil_h': 128, 'range_deg_step': 15, 'range': [25.0] * 24}
    return _ANG['meta']


def _angel_range(m, deg):
    """瞳孔朝 deg 度方向最远能走多少像素（原图像素）；在 15 度一档的表里线性插值。"""
    step = float(m.get('range_deg_step', 15))
    r = m['range']
    d = deg %% 360.0
    i = int(d // step)
    f = (d - i * step) / step
    return r[i %% len(r)] * (1.0 - f) + r[(i + 1) %% len(r)] * f


def _angel_target(st, cfg, E, t):
    """瞳孔想看的方向：有手就朝手在画布上的位置，没手就慢慢飘着张望。返回 (角度deg, 力度0~1)。"""
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    if cfg.get('angel_follow_hand', True):
        try:
            for n in _hand_nodes():
                if n is None:
                    continue
                pts = list(n.points)
                if len(pts) > 9:
                    x_, y_ = pts[9].x, pts[9].y
                    if cfg.get('air_flip_x', AIR_FLIP_X):
                        x_ = 1.0 - x_
                    dx = x_ * Wc - E[0]
                    dy = (1.0 - y_) * Hc - E[1]
                    dist = (dx * dx + dy * dy) ** 0.5
                    deg = math.degrees(math.atan2(-dy, dx))                    # 屏幕向上为正
                    return deg, min(1.0, dist / (0.35 * Wc)), True
        except Exception:
            pass
    deg = (t * 25.0 + 40.0 * math.sin(t * 0.6)) %% 360.0
    return deg, 0.55 + 0.35 * math.sin(t * 0.7), False


def _angel_hide():
    for nm in ('angel_body_tf', 'angel_pupil_tf'):
        o = op(nm)
        if o is not None:
            o.par.sx = 0.0001
            o.par.sy = 0.0001
    f = op('angel_fade')
    if f is not None:
        f.par.cross = 0.0


def _update_angel(st):
    """随机出现的大眼睛天使：慢慢淡入 -> 停一会儿（瞳孔跟着观众的手转，没手就到处张望）-> 淡出。触发：test_angel.py 或随机间隔。"""
    cfg = _fx_cfg(st)
    body, pupil, fade = op('angel_body_tf'), op('angel_pupil_tf'), op('angel_fade')
    if body is None or pupil is None or fade is None:
        return
    st['ang_age'] = st.get('ang_age', 99) + 1
    if st['ang_age'] >= 6:
        st['ang_age'] = 0
        t_new = None
        try:
            with open(BRIDGE + '/angel_test.json', encoding='utf-8') as fh:
                t_new = float(json.load(fh).get('t', 0.0))
        except Exception:
            t_new = None
        if st.get('ang_seen') is None:
            st['ang_seen'] = t_new if t_new is not None else 0.0
        elif t_new is not None and t_new > st['ang_seen']:
            st['ang_seen'] = t_new
            st['ang_pending'] = True
        lo_, hi_ = float(cfg.get('angel_auto_min', 0)), float(cfg.get('angel_auto_max', 0))
        if cfg.get('angel_on', True) and lo_ > 0 and hi_ >= lo_:
            if st.get('ang_next') is None:
                st['ang_next'] = time.time() + random.uniform(lo_, hi_)
            elif time.time() >= st['ang_next'] and st.get('ang_t0') is None:
                st['ang_next'] = time.time() + random.uniform(lo_, hi_)
                st['ang_pending'] = True
        if st.pop('ang_pending', False) and cfg.get('angel_on', True) and st.get('ang_t0') is None:
            st['ang_t0'] = time.time()
            st['ang_off'] = [0.0, 0.0]
            print('gz_exec 天使出现')
    t0 = st.get('ang_t0')
    idle = max(0.0, min(1.0, float(cfg.get('angel_idle_level', 0.0))))     # 常驻在背景里的亮度（0 = 平时看不见，只在"出现"时露面）
    env = 0.0
    if t0 is not None and cfg.get('angel_on', True):
        t = time.time() - t0
        T_in, T_hold, T_out = 2.5, float(cfg.get('angel_hold', 9.0)), 2.5
        if t >= T_in + T_hold + T_out:
            st['ang_t0'] = None
        elif t < T_in:
            env = _ease_io(t / T_in)
        elif t < T_in + T_hold:
            env = 1.0
        else:
            env = 1.0 - _ease_io((t - T_in - T_hold) / T_out)
    if st.get('ang_base') is None:
        st['ang_base'] = time.time()
    t = time.time() - (st['ang_t0'] if st.get('ang_t0') is not None else st['ang_base'])
    fd = idle + (1.0 - idle) * env
    if not cfg.get('angel_on', True) or fd <= 0.001:
        if st.get('ang_vis', True):
            _angel_hide()
            st['ang_vis'] = False
        return
    m = _angel_meta()
    Wc, Hc = float(cfg.get('hand_canvas_w', 1920)), float(cfg.get('hand_canvas_h', 1080))
    Wp = float(cfg.get('angel_scale', 0.5)) * Wc * (1.0 + 0.015 * math.sin(t * 1.3))        # 轻轻呼吸
    Hp = Wp * float(m['h']) / float(m['w'])
    k = Wp / float(m['w'])                                                                  # 原图像素 -> 画布像素
    ex, ey = float(cfg.get('angel_x', 0.78)) * Wc, float(cfg.get('angel_y', 0.33)) * Hc + 4.0 * math.sin(t * 0.9)
    u, v = float(m['eye_cx']) / float(m['w']), float(m['eye_cy']) / float(m['h'])
    cx, cy = ex - (u - 0.5) * Wp, ey - (v - 0.5) * Hp
    body.par.sx = Wp / Wc
    body.par.sy = Hp / Hc
    body.par.tx = (cx - Wc / 2.0) / Wc
    body.par.ty = (Hc / 2.0 - cy) / Hc
    deg, frac, tracking = _angel_target(st, cfg, (ex, ey), t)
    rmax = _angel_range(m, deg) * max(0.0, min(1.0, frac))
    tx_off, ty_off = math.cos(math.radians(deg)) * rmax, -math.sin(math.radians(deg)) * rmax
    o_ = st.setdefault('ang_off', [0.0, 0.0])
    sm = 0.18 if tracking else 0.04                                                        # 跟手快一点，张望慢一点
    o_[0] += (tx_off - o_[0]) * sm
    o_[1] += (ty_off - o_[1]) * sm
    pw, ph = float(m['pupil_w']) * k, float(m['pupil_h']) * k
    pupil.par.sx = pw / Wc
    pupil.par.sy = ph / Hc
    pupil.par.tx = (ex + o_[0] * k - Wc / 2.0) / Wc
    pupil.par.ty = (Hc / 2.0 - (ey + o_[1] * k)) / Hc
    fade.par.cross = fd
    st['ang_vis'] = True


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
        _update_angel(st)
    except Exception as e:
        if not st.get('angel_err'):
            st['angel_err'] = 1
            print('gz_exec 天使出错（只打印一次）:', repr(e))
    try:
        _update_puppet(st)
    except Exception as e:
        if not st.get('puppet_err'):
            st['puppet_err'] = 1
            print('gz_exec 木偶戏出错（只打印一次）:', repr(e))
    try:
        _update_poke_fx(st)
    except Exception as e:
        if not st.get('pokefx_err'):
            st['pokefx_err'] = 1
            print('gz_exec 水波特效出错（只打印一次）:', repr(e))
    try:
        _update_hand(st)
    except Exception as e:
        if not st.get('hand_err'):
            st['hand_err'] = 1
            print('gz_exec 木头手出错（只打印一次）:', repr(e))
    try:
        _update_ballsize(st)
    except Exception as e:
        if not st.get('ballsize_err'):
            st['ballsize_err'] = 1
            print('gz_exec 球比例出错（只打印一次）:', repr(e))
    try:
        _update_ball(st)
    except Exception as e:
        if not st.get('ball_err'):
            st['ball_err'] = 1
            print('gz_exec 海洋球出错（只打印一次）:', repr(e))
    try:
        _update_output(st)
    except Exception as e:
        if not st.get('output_err'):
            st['output_err'] = 1
            print('gz_exec 输出切换出错（只打印一次）:', repr(e))
    try:
        _update_screen(st)
    except Exception as e:
        if not st.get('screen_err'):
            st['screen_err'] = 1
            print('gz_exec 屏幕适应出错（只打印一次）:', repr(e))
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
try:
    tile.par.outputresolution = 'custom'
    tile.par.resolutionw = W
    tile.par.resolutionh = H
except Exception as e:
    print('gz_tile 分辨率设置失败:', e)
sw.nodeX, sw.nodeY = 250, -800
fit.nodeX, fit.nodeY = 500, -800
ball_img = p.op('ball_img') or p.create(moviefileinTOP, 'ball_img')
import os as _os
ball_img.par.file = _os.path.normpath(_os.path.join(BRIDGE, '..', 'ballpit', 'seq', 'ball_0000.png'))
ball_fit = p.op('ball_fit') or p.create(fitTOP, 'ball_fit')
ball_fit.inputConnectors[0].connect(ball_img)
ball_tf = p.op('ball_tf') or p.create(transformTOP, 'ball_tf')
ball_tf.inputConnectors[0].connect(ball_fit)
try:
    ball_fit.par.outputresolution = 'custom'
    ball_fit.par.resolutionw = W
    ball_fit.par.resolutionh = H
    ball_fit.par.fit = 'fill'
    ball_tf.par.extend = 'zero'
    ball_tf.par.ty = -1.05
except Exception as e:
    print('海洋球节点设置失败:', e)
castle_ball_img = p.op('castle_ball_img') or p.create(moviefileinTOP, 'castle_ball_img')
castle_ball_img.par.file = _os.path.normpath(_os.path.join(BRIDGE, '..', 'ballpit', 'seq_strip', 'ball_0000.png'))
castle_ball_img.nodeX, castle_ball_img.nodeY = 750, -1450
castle_ball_fit = p.op('castle_ball_fit') or p.create(fitTOP, 'castle_ball_fit')
castle_ball_fit.inputConnectors[0].connect(castle_ball_img)
castle_ball_tf = p.op('castle_ball_tf') or p.create(transformTOP, 'castle_ball_tf')
castle_ball_tf.inputConnectors[0].connect(castle_ball_fit)
try:
    castle_ball_fit.par.outputresolution = 'custom'
    castle_ball_fit.par.resolutionw = 1280
    castle_ball_fit.par.resolutionh = 427
    castle_ball_fit.par.fit = 'fill'
    _jv = [m_ for m_ in castle_ball_fit.par.justifyv.menuNames if 'bottom' in m_.lower()]
    if _jv:
        castle_ball_fit.par.justifyv = _jv[0]        # 球从底部喷出，裁剪时保住底部
    castle_ball_tf.par.extend = 'zero'
    castle_ball_tf.par.ty = -1.05
except Exception as e:
    print('castle_ball 节点设置失败:', e)
castle_ball_fit.nodeX, castle_ball_fit.nodeY = 900, -1250
castle_ball_tf.nodeX, castle_ball_tf.nodeY = 1050, -1250
print('castle_ball_tf 就绪：城堡底部长方形专用的海洋球（比例在 audio_fx.json 的 castle_ball_w / castle_ball_h 里改）')
gz_over = p.op('gz_over') or p.create(overTOP, 'gz_over')
gz_over.inputConnectors[0].connect(ball_tf)       # 球在上面
gz_over.inputConnectors[1].connect(fit)           # 画面在下面
ball_img.nodeX, ball_img.nodeY = 750, -1100
ball_fit.nodeX, ball_fit.nodeY = 900, -1100
ball_tf.nodeX, ball_tf.nodeY = 1050, -1100
gz_over.nodeX, gz_over.nodeY = 750, -800
_km = p.op('kantanMapper')
if _km is not None and _km.op('out1') is not None:
    map_sel = p.op('map_sel') or p.create(selectTOP, 'map_sel')
    map_fit = p.op('map_fit') or p.create(fitTOP, 'map_fit')
    try:
        map_sel.par.top = _km.op('out1').path          # Kantan 对准后的输出
        map_fit.inputConnectors[0].connect(map_sel)
        map_fit.par.outputresolution = 'custom'
        map_fit.par.resolutionw = W
        map_fit.par.resolutionh = H
        _fm = [m_ for m_ in map_fit.par.fit.menuNames]
        _best = [m_ for m_ in _fm if 'best' in m_.lower()]
        if _best:
            map_fit.par.fit = _best[0]                  # 不拉伸，按比例放进屏幕（不够的地方留黑边）
        print('map_fit 已建立（Kantan 输出会自动按屏幕大小缩放），fit 选项:', _fm)
    except Exception as e:
        print('map_fit 设置失败:', e)
    map_sel.nodeX, map_sel.nodeY = 1200, -1100
    # 水波+故障特效：Kantan 输出 -> poke_fx(GLSL) -> map_fit。着色器代码在 code/poke_fx_shader.glsl
    try:
        poke_fx = p.op('poke_fx') or p.create(glslTOP, 'poke_fx')
        poke_fx.inputConnectors[0].connect(map_sel)
        _px = p.op('poke_fx_pixel')
        if _px is not None:
            with open(_os.path.normpath(_os.path.join(BRIDGE, '..', '..', 'code', 'poke_fx_shader.glsl')), encoding='utf-8') as _fh:
                _px.text = _fh.read()
        poke_fx.par.vec0name = 'uPoke'
        poke_fx.par.vec0valuex = 0.5
        poke_fx.par.vec0valuey = 0.5
        poke_fx.par.vec0valuez = -1.0
        poke_fx.par.vec0valuew = 0.0
        map_fit.inputConnectors[0].connect(poke_fx)
        poke_fx.nodeX, poke_fx.nodeY = 1275, -1100
        print('poke_fx 就绪（戳城堡的水波+故障特效）；着色器有错时程序会自动绕开，不会黑屏')
    except Exception as e:
        print('poke_fx 建立失败（不影响其他功能）:', e)
    map_fit.nodeX, map_fit.nodeY = 1350, -1100
else:
    print('没找到 kantanMapper/out1，跳过映射输出节点')
hand_img = p.op('hand_img') or p.create(moviefileinTOP, 'hand_img')
hand_img.par.file = _os.path.normpath(_os.path.join(BRIDGE, '..', '..', 'assets', 'hand', 'hand_sprite.png'))
hand_out = p.op('hand_out') or p.create(transformTOP, 'hand_out')       # 木头手：整张 1920x1080 画布，透明背景，Kantan 里用一个盖满画布的长方形来映射它
hand_out.inputConnectors[0].connect(hand_img)
try:
    hand_out.par.extend = 'zero'
    hand_out.par.outputresolution = 'custom'
    hand_out.par.resolutionw = 1920
    hand_out.par.resolutionh = 1080
    hand_out.par.sx = 0.0001
    hand_out.par.sy = 0.0001
except Exception as e:
    print('hand_out 设置失败:', e)
hand_fit = p.op('hand_fit') or p.create(fitTOP, 'hand_fit')              # 不开映射时，手叠在整屏画面上预览
hand_fit.inputConnectors[0].connect(hand_out)
try:
    hand_fit.par.outputresolution = 'custom'
    hand_fit.par.resolutionw = W
    hand_fit.par.resolutionh = H
    _hf = [m_ for m_ in hand_fit.par.fit.menuNames if 'best' in m_.lower()]
    if _hf:
        hand_fit.par.fit = _hf[0]
except Exception as e:
    print('hand_fit 设置失败:', e)
gz_final = p.op('gz_final') or p.create(overTOP, 'gz_final')
gz_final.inputConnectors[0].connect(hand_fit)      # 手在最上面
gz_final.inputConnectors[1].connect(gz_over)       # 画面 + 海洋球在下面
hand_img.nodeX, hand_img.nodeY = 1600, -1100
hand_out.nodeX, hand_out.nodeY = 1750, -1100
hand_fit.nodeX, hand_fit.nodeY = 1900, -1100
gz_final.nodeX, gz_final.nodeY = 2050, -1100
print('木头手就绪（hand_out 是给 Kantan 用的，gz_final 是画面+海洋球+手）')

# --- 木偶戏：两只手 + 四根线 + 兔子，全部画在 1920x1080 的透明画布上，叠在"木头手"那一层之上，合成 scene_out ---
def _mk_img(name, rel, x, y):
    n_ = p.op(name) or p.create(moviefileinTOP, name)
    n_.par.file = _os.path.normpath(_os.path.join(BRIDGE, '..', '..', 'assets', *rel))
    n_.nodeX, n_.nodeY = x, y
    return n_


def _mk_tf(name, src, x, y):
    t_ = p.op(name) or p.create(transformTOP, name)
    t_.inputConnectors[0].connect(src)
    try:
        t_.par.extend = 'zero'
        t_.par.outputresolution = 'custom'
        t_.par.resolutionw = 1920
        t_.par.resolutionh = 1080
        t_.par.sx = 0.0001
        t_.par.sy = 0.0001
    except Exception as e_:
        print(name, '设置失败:', e_)
    t_.nodeX, t_.nodeY = x, y
    return t_


puppet_img = _mk_img('puppet_img', ('puppet', 'puppet.png'), 1600, -1300)
hand_img_r = _mk_img('hand_img_r', ('hand', 'hand_sprite_R.png'), 1600, -1450)
string_img = _mk_img('string_img', ('puppet', 'string.png'), 1600, -1600)
puppet_tf = _mk_tf('puppet_tf', puppet_img, 1750, -1300)
pL_tf = _mk_tf('pL_tf', hand_img, 1750, -1100)
pR_tf = _mk_tf('pR_tf', hand_img_r, 1750, -1450)
_pstr = [_mk_tf('pstr' + str(i_ + 1), string_img, 1750, -1600 - 100 * i_) for i_ in range(4)]
_prev = hand_out
for i_, node_ in enumerate(_pstr + [puppet_tf, pL_tf, pR_tf]):
    nm_ = 'pc' + str(i_ + 1) if i_ < 6 else 'scene_out'
    ov_ = p.op(nm_) or p.create(overTOP, nm_)
    ov_.inputConnectors[0].connect(node_)       # 这一层在上面
    ov_.inputConnectors[1].connect(_prev)       # 下面是前面所有层
    ov_.nodeX, ov_.nodeY = 2000 + 150 * i_, -1100
    _prev = ov_
scene_out = _prev
hand_fit.inputConnectors[0].connect(scene_out)  # 整屏预览里，手/木偶也叠在画面上
print('木偶戏就绪：scene_out = 木头手 + 木偶戏（Kantan 里手的形状请用 scene_out 当纹理）')

# --- 大眼睛天使：翅膀(带眼白的底图) + 瞳孔(单独一张，会动) -> 淡入淡出 -> 叠在 scene_out 之上，合成 scene_all ---
angel_body_img = _mk_img('angel_body_img', ('angel', 'wings_pixel_base.png'), 1600, -1800)
angel_pupil_img = _mk_img('angel_pupil_img', ('angel', 'pupil_pixel.png'), 1600, -1950)
blank_img = _mk_img('blank_img', ('angel', 'blank.png'), 1600, -2100)
angel_body_tf = _mk_tf('angel_body_tf', angel_body_img, 1750, -1800)
angel_pupil_tf = _mk_tf('angel_pupil_tf', angel_pupil_img, 1750, -1950)
angel_comp = p.op('angel_comp') or p.create(overTOP, 'angel_comp')
angel_comp.inputConnectors[0].connect(angel_pupil_tf)      # 瞳孔在上
angel_comp.inputConnectors[1].connect(angel_body_tf)       # 翅膀和眼睛在下
angel_fade = p.op('angel_fade') or p.create(crossTOP, 'angel_fade')
angel_fade.inputConnectors[0].connect(blank_img)           # 0 = 全透明
angel_fade.inputConnectors[1].connect(angel_comp)          # 1 = 天使完全出现
try:
    angel_fade.par.cross = 0.0
except Exception as e:
    print('angel_fade 的 cross 设置失败:', e)
scene_all = p.op('scene_all') or p.create(overTOP, 'scene_all')
scene_all.inputConnectors[0].connect(angel_fade)           # 天使在最上面
scene_all.inputConnectors[1].connect(scene_out)
hand_fit.inputConnectors[0].connect(scene_all)             # 整屏预览也叠上天使
angel_comp.nodeX, angel_comp.nodeY = 1900, -1850
angel_fade.nodeX, angel_fade.nodeY = 2050, -1850
scene_all.nodeX, scene_all.nodeY = 2200, -1850
print('天使就绪：scene_all = 木头手 + 木偶戏 + 天使（Kantan 里手/天使的形状请用 scene_all 当纹理）')
win = p.op('gz_win')
if win is not None:
    win.par.winop = gz_over.path
    print('gz_win 已改成读取 gz_over（画面 + 海洋球）')
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
    _xf.par.cross = 0.0
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
castle_tile = p.op('castle_tile') or p.create(transformTOP, 'castle_tile')     # 城堡用的方形万花筒（脸镜像平铺）
castle_tile.inputConnectors[0].connect(sw)
try:
    castle_tile.par.extend = 'mirror'
    castle_tile.par.outputresolution = 'custom'
    castle_tile.par.resolutionw = 1024
    castle_tile.par.resolutionh = 1024
except Exception as e:
    print('castle_tile 设置失败:', e)
castle_mix = p.op('castle_mix') or p.create(crossTOP, 'castle_mix')              # 万花筒 <-> 纯人脸
castle_mix.inputConnectors[0].connect(castle_tile)
castle_mix.inputConnectors[1].connect(sw)
try:
    castle_mix.par.cross = 0.0
except Exception as e:
    print('castle_mix 的 cross 设置失败:', e)
castle_tile.nodeX, castle_tile.nodeY = 750, -1250
castle_mix.nodeX, castle_mix.nodeY = 900, -1350
castle_xf = p.op('castle_xf') or p.create(crossTOP, 'castle_xf')
castle_xf.inputConnectors[0].connect(castle_mix)       # 万花筒/纯人脸（给纸箱每个面用）
castle_xf.inputConnectors[1].connect(_at)      # 黑白 AI 注意力图（方形）
try:
    castle_xf.par.cross = 0.0
except Exception as e:
    print('castle_xf 的 cross 设置失败:', e)
castle_xf.nodeX, castle_xf.nodeY = 950, -1250
print('castle_xf 就绪：纸箱/城堡用的方形画面（脸 <-> 黑白注意力图，随场景切换）')
_xf.nodeX, _xf.nodeY = 700, -1100
_gm.nodeX, _gm.nodeY = 700, -950
print('脸群像就绪：audio_fx.json 里 visual_mode 可切换 crowd / mirror')
