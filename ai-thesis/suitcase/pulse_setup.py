# 毕设版：在 TD 的 Textport 里运行，接上耳夹（Arduino 串口），得到心率 bpm / 心跳时间 beat_t / 有无信号 present（arr_pulse）。
# 和黑客松那个一样，只是自动找串口，并且不再把分数交给 lp_setup。
# 前提：Arduino 已经上传了 MODE 2 的程序（每次心跳发 B,间隔,心率,幅度；每秒发 S,心率,幅度），串口监视器已关闭。
# 新建节点（都在 /project1 里）：
#   pulse_serial  Serial DAT：读 Arduino 串口
#   pulse_cb      Text DAT：处理每一行数据，算心率和"同步分数"
#   arr_pulse     Constant CHOP：bpm, ibi, amp, present, coherence, score, beat_t, nbeats
#   pulse_watch   Execute DAT：没数据 3 秒就算"没信号"；有信号就把分数交给 lp_setup 的分数（lp_score）
# 打开/关闭"用耳夹分数控制画面"：   op('/project1').store('use_pulse', True / False)
# 换串口：  op('/project1/pulse_serial').par.port = '/dev/cu.usbmodemXXXX'
import glob as _glob
_ports = sorted(_glob.glob('/dev/cu.usbmodem*') + _glob.glob('/dev/cu.usbserial*'))
PORT = _ports[0] if _ports else '/dev/cu.usbmodem64E8336998642'     # 自动找 Arduino 的串口；找不到就用上次的
print('串口候选：', _ports or '（没找到，请确认 Arduino 已插上）')
BAUD = 9600
p = op('/project1')

def mk(t, name, x, y):
    n = p.op(name) or p.create(t, name)
    n.nodeX, n.nodeY = x, y
    return n

c = mk(constantCHOP, 'arr_pulse', -400, -1500)
for i, (n, v) in enumerate((('bpm', 0), ('ibi', 0), ('amp', 0), ('present', 0), ('coherence', 0), ('score', 0), ('beat_t', -99), ('nbeats', 0), ('beat_t1', -99), ('beat_t2', -99))):
    setattr(c.par, 'const%dname' % i, n)
    setattr(c.par, 'const%dvalue' % i, v)

CB = r'''import math
INH, HOLD, EXH, REST = 4.0, 1.5, 6.0, 1.0
CYC = INH + HOLD + EXH + REST
def _ease(k):
    k = max(0.0, min(1.0, k))
    return 0.5 - 0.5 * math.cos(math.pi * k)
def _pacer(t, bt0):
    tc = (t - bt0) % CYC
    if tc < INH: return _ease(tc / INH)
    if tc < INH + HOLD: return 1.0
    if tc < INH + HOLD + EXH: return 1.0 - _ease((tc - INH - HOLD) / EXH)
    return 0.0
def _score(hist, now, bt0):
    pts = [(t, b) for t, b in hist if now - t <= 24.0]
    if len(pts) < 12 or pts[-1][0] - pts[0][0] < 15.0:
        return 0.0, 0.0
    ys = [b for _, b in pts]
    my = sum(ys) / len(ys)
    sd = math.sqrt(sum((y - my) ** 2 for y in ys) / len(ys))
    if sd < 0.3:
        return 0.0, 0.0
    best = -1.0
    for lag in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        xs = [_pacer(t - lag, bt0) for t, _ in pts]
        mx = sum(xs) / len(xs)
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / len(xs))
        if sx < 1e-6: continue
        c_ = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) * sx * sd)
        best = max(best, c_)
    coh = max(0.0, best)
    ampf = max(0.0, min(1.0, sd / 3.0))
    return coh * (0.5 + 0.5 * ampf), coh
def _beat(st, now, ibi, bpm, amp):
    host = parent()
    w = op('/project1/arr_pulse')
    st['hist'].append((now, 60000.0 / ibi))
    st['hist'] = [(t, b) for t, b in st['hist'] if 0.0 <= now - t <= 30.0]      # 时间倒退的旧心跳丢掉
    st['n'] += 1
    bt0 = host.fetch('bt0', None)
    if bt0 is None:
        bt0 = now
    s, coh = _score(st['hist'], now, bt0)
    st['score'] += (s - st['score']) * 0.2
    st['coh'] = coh
    w.par.const0value = bpm
    w.par.const1value = ibi
    w.par.const2value = amp
    w.par.const4value = coh
    w.par.const5value = st['score']
    w.par.const9value = w.par.const8value.eval()   # 前前一次心跳的时间
    w.par.const8value = w.par.const6value.eval()   # 前一次心跳的时间
    w.par.const6value = now
    w.par.const7value = st['n']
def _handle(line):
    import re
    host = parent()
    w = op('/project1/arr_pulse')
    now = absTime.seconds
    st = host.fetch('pulse', None) or {'hist': [], 'score': 0.0, 'coh': 0.0, 'n': 0, 'last_rx': -99.0, 'amp': 300.0, 'last_beat_rx': None}
    st.setdefault('amp', 300.0); st.setdefault('last_beat_rx', None)
    try:
        parts = line.strip().split(',')
        if parts[0] == 'B' and len(parts) >= 4:                      # MODE 2：B,间隔毫秒,心率,幅度
            st['amp'] = float(parts[3])
            _beat(st, now, float(parts[1]), float(parts[2]), st['amp'])
        elif parts[0] == 'S' and len(parts) >= 3:                    # MODE 2：S,心率,幅度
            w.par.const0value = float(parts[1])
            w.par.const2value = float(parts[2])
            st['amp'] = float(parts[2])
        elif '心跳' in line:                                         # MODE 1 文字：♥ 心跳！当前心率 83 次/分
            m = re.search(r'心率\s*(\d+)', line)
            if m:
                bpm = float(m.group(1))
                last = st['last_beat_rx']
                st['last_beat_rx'] = now
                if last is not None:
                    ibi = (now - last) * 1000.0                     # 用收到的时间差当心跳间隔（有一点点误差，演示够用）
                    if 300 <= ibi <= 1500:
                        _beat(st, now, ibi, bpm, st['amp'])
        elif '信号幅度' in line:                                     # MODE 1 状态行
            m = re.search(r'信号幅度\s*(\d+)', line)
            if m:
                st['amp'] = float(m.group(1))
                w.par.const2value = st['amp']
            m2 = re.search(r'心率\s*(\d+)', line)
            if m2:
                w.par.const0value = float(m2.group(1))
    except Exception as e:
        print('pulse_cb 解析出错：', repr(e)[:80], '| 行：', line[:60])
        return
    st['last_rx'] = now
    host.store('pulse', st)
def onReceive(dat, rowIndex, message, bytes):
    host = parent()
    buf = host.fetch('pulse_buf', '') + (message if isinstance(message, str) else bytes.decode('utf-8', 'ignore'))
    lines = buf.split(chr(10))
    host.store('pulse_buf', lines[-1])
    for ln in lines[:-1]:
        if ln.strip():
            _handle(ln)
    return
'''
cb = mk(textDAT, 'pulse_cb', -200, -1500)
cb.text = CB

ser = mk(serialDAT, 'pulse_serial', -400, -1650)
ser.par.active = False
try:
    ser.par.port = PORT
except Exception as e:
    print('串口参数没设成功：', repr(e)[:80], '→ 请手动在 pulse_serial 的参数里选串口')
try:
    ser.par.baudrate = BAUD
except Exception as e:
    print('波特率没设成功：', repr(e)[:80], '→ 请手动在 pulse_serial 的参数里选 9600')
for k in ('callbacks', 'callbackdat', 'callbackDAT'):
    if hasattr(ser.par, k):
        try:
            setattr(ser.par, k, '')                  # 不用回调，改成 pulse_watch 每帧主动去读新来的行（更稳）
        except Exception:
            pass
        break
try:
    ser.par.maxlines = 2000
except Exception:
    pass
ser.par.active = True

WATCH = '''def onFrameEnd(frame):
    host = parent()
    s = op('/project1/pulse_serial')
    if s is not None and s.numRows > 1:
        mod = op('/project1/pulse_cb').module
        n = s.numRows
        start = host.fetch('pulse_row_idx', 1)
        if start > n:
            start = 1
        for r in range(start, n):                      # 只处理还没读过的新行
            try:
                mod._handle(s[r, 0].val)
            except Exception as e:
                print('pulse_watch 处理出错：', repr(e)[:80])
        try:
            s.par.clear.pulse()                        # 用串口节点自己的 Clear 按钮清空（脚本里不能直接改它的表）
            host.store('pulse_row_idx', 1)
        except Exception:
            host.store('pulse_row_idx', n)             # 清不掉也没关系，记住读到哪了，不会重复处理
    w = op('/project1/arr_pulse')
    st = host.fetch('pulse', None)
    now = absTime.seconds
    if st is not None and st['last_rx'] > now:          # 重新打开工程后计时从 0 开始，旧状态作废
        host.store('pulse', None)
        st = None
    if st is None or now - st['last_rx'] > 3.0:
        w.par.const3value = 0
        return
    present = 1 if w['bpm'].eval() > 0 else 0
    w.par.const3value = present
    return
'''
wt = mk(executeDAT, 'pulse_watch', -200, -1650)
wt.par.framestart = False
wt.par.frameend = True
wt.par.active = True
wt.text = WATCH
if p.fetch('use_pulse', None) is None:
    p.store('use_pulse', True)
print('OK：耳夹已接上。串口 =', PORT)
print('看数据：  print([round(op("/project1/arr_pulse")[i].eval(), 2) for i in range(8)])   （依次：心率、间隔、幅度、有信号、同步度、分数、上次心跳时间、心跳数）')
