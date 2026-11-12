# 在 TD 的 Textport 里运行：装一个"录声音"的功能（按 = 键开始 / 再按一次停止）。
# 它不是用麦克风或系统录音，所以【戴耳机、音量关小都不影响】，也不会有风声：
#   ① 记下空气钢琴（和真钢琴）弹的每一个音符 -> air_piano.mid（拖进 GarageBand，用你自己的音色导出，就是干净的钢琴声）
#   ② 记下游戏里放的声音（找到光点的叮声、铃声、讲话、结尾的机器人声）-> game_sfx.wav（重新合成，跟耳机无关）
#   ③ 另外给一个 mix_preview.wav：简易钢琴 + 游戏声音，马上能听、能放进视频当临时配乐
# 文件都放在 ai-thesis/recordings/rec_时间/ 里。
# 想拆掉：op('/project1/sc_rec_exec').destroy(); op('/project1/sc_rec_mod').destroy(); op('/project1/sc_rec_kb').destroy(); op('/project1/sc_rec_kbcb').destroy()
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
OUTDIR = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/recordings'
p = op('/project1')

MOD = r'''
import time, re, os, sys, datetime
BASE = '__BASE__'
OUTDIR = '__OUT__'
if BASE not in sys.path:
    sys.path.insert(0, BASE)
SRC = ('/project1/air_note', '/project1/midiin1')      # 空气钢琴 + 真钢琴（有哪个就记哪个）
NOTE_RE = re.compile(r'^ch(\d+)n(\d+)$')
EPS = 0.001
_ST = {'on': False, 't0': 0.0, 'prev': {}, 'open': {}, 'notes': []}

def _vel(v):
    return max(1, min(127, int(round(v * 127)))) if v <= 1.0 else max(1, min(127, int(round(v))))

def scan():
    if not _ST['on']:
        return
    now = time.time() - _ST['t0']
    for path in SRC:
        o = op(path)
        if o is None:
            continue
        for c in o.chans():
            m = NOTE_RE.match(c.name)
            if not m:
                continue
            key = (path, int(m.group(2)))
            v = float(c.eval())
            was = _ST['prev'].get(key, 0.0)
            if v > EPS and was <= EPS:
                _ST['open'][key] = (now, _vel(v))
            elif v <= EPS and was > EPS:
                o_ = _ST['open'].pop(key, None)
                if o_:
                    _ST['notes'].append((round(o_[0], 3), round(now, 3), key[1], o_[1]))
            _ST['prev'][key] = v

def start():
    _ST.update({'on': True, 't0': time.time(), 'prev': {}, 'open': {}, 'notes': []})
    g = op('/project1/sc_game_exec')
    if g is not None:
        g.store('rec_events', [])
        g.store('rec_t0', _ST['t0'])
    print('●●● 开始录音：现在弹的音符和游戏里的声音都会被记下来（再按一次 = 键停止）')
    try:
        ui.status = '● REC 录音中（按 = 停止）'
    except Exception:
        pass

def stop():
    if not _ST['on']:
        return
    now = time.time() - _ST['t0']
    _ST['on'] = False
    for key, (t_on, vel) in list(_ST['open'].items()):
        _ST['notes'].append((round(t_on, 3), round(now, 3), key[1], vel))
    _ST['open'] = {}
    g = op('/project1/sc_game_exec')
    events = []
    if g is not None:
        events = list(g.fetch('rec_events', None) or [])
        g.store('rec_events', None)
        g.store('rec_t0', None)
    folder = os.path.join(OUTDIR, 'rec_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    try:
        ui.status = '正在保存录音…'
    except Exception:
        pass
    try:
        import importlib, rec_tools
        importlib.reload(rec_tools)
        notes = sorted(_ST['notes'])
        msgs = rec_tools.render(folder, BASE + '/voice', notes, events, round(now, 2))
        for m_ in msgs:
            print('  提示：', m_)
        print('■■■ 录音已保存（%.1f 秒，%d 个音符，%d 个游戏声音）：' % (now, len(notes), len(events)))
        print('    ' + folder)
        if not notes:
            print('    注意：一个音符都没记到。空气钢琴要先用 A 键打开，并确认 air_note / midiin1 有数。')
    except Exception as e:
        print('保存出错：', repr(e))
    try:
        ui.status = ''
    except Exception:
        pass

def toggle():
    if _ST['on']:
        stop()
    else:
        start()
'''.replace('__BASE__', BASE).replace('__OUT__', OUTDIR)

mod = p.op('sc_rec_mod') or p.create(textDAT, 'sc_rec_mod')
mod.text = MOD
mod.nodeX, mod.nodeY = 2500, -3900

ex = p.op('sc_rec_exec') or p.create(executeDAT, 'sc_rec_exec')
ex.text = "def onFrameEnd(frame):\n    try:\n        op('/project1/sc_rec_mod').module.scan()\n    except Exception as e:\n        pass\n    return\n"
ex.nodeX, ex.nodeY = 2500, -4050
if hasattr(ex.par, 'frameend'):
    ex.par.frameend = True
if hasattr(ex.par, 'active'):
    ex.par.active = True

cb = p.op('sc_rec_kbcb') or p.create(textDAT, 'sc_rec_kbcb')
cb.text = (
    "def onKey(dat, key, character, *a):\n"
    "    try:\n"
    "        st = a[9] if len(a) > 9 else True\n"
    "        if st and character == '=':\n"
    "            op('/project1/sc_rec_mod').module.toggle()\n"
    "    except Exception as e:\n"
    "        print('sc_rec_kbcb 出错：', repr(e)[:100])\n"
    "    return\n"
)
cb.nodeX, cb.nodeY = 2300, -4200
kb = p.op('sc_rec_kb') or p.create(keyboardinDAT, 'sc_rec_kb')
kb.nodeX, kb.nodeY = 2100, -4200
ok = False
for nm in ('callbacks', 'callbackdat', 'callbackDAT'):
    if hasattr(kb.par, nm):
        setattr(kb.par, nm, cb)
        ok = True
        break
if hasattr(kb.par, 'active'):
    kb.par.active = True

if ok:
    print('OK：录音功能装好了。先点一下 TD 窗口，按 = 键开始录，再按一次 = 键停止并保存。')
    print('文件夹：', OUTDIR)
else:
    print('没找到键盘回调参数，请把下面这行发给我：', [x.name for x in kb.pars()][:40])
