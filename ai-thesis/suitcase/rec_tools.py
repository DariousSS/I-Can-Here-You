# 录音小工具（给 TD 里的 sc_rec_exec 用，也可以在 Terminal 单独运行）。
# 思路：不"录"喇叭/耳机，而是把"弹了哪些音符""游戏放了哪些声音"记成数据，停止时再重新合成成音频文件。
# 所以不管你戴不戴耳机、音量开多大、有没有风声，导出来的声音都是干净的。
import os, struct, wave, json, subprocess, tempfile, math

SR = 44100
PPQ = 480                  # MIDI：每拍 480 tick
TEMPO_US = 500000          # 每拍 0.5 秒 = 120 BPM  -> 1 秒 = 960 tick（GarageBand 工程速度请保持 120）


def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def write_midi(notes, path):
    """notes: [(t_on 秒, t_off 秒, 音符号 0-127, 力度 1-127), ...] -> 标准 MIDI 文件（单轨，120 BPM）"""
    ev = []
    for t_on, t_off, n, v in notes:
        a = int(round(t_on * 960))
        b = max(a + 10, int(round(t_off * 960)))
        n = max(0, min(127, int(n)))
        v = max(1, min(127, int(v)))
        ev.append((a, 1, bytes([0x90, n, v])))      # 同一时刻先关后开：关=0，开=1，所以关排前面
        ev.append((b, 0, bytes([0x80, n, 0])))
    ev.sort(key=lambda e: (e[0], e[1]))
    trk = b'\x00\xff\x51\x03' + struct.pack('>I', TEMPO_US)[1:]
    trk += b'\x00\xff\x03' + bytes([len('air piano')]) + b'air piano'
    last = 0
    for tick, _, data in ev:
        trk += _vlq(tick - last) + data
        last = tick
    trk += b'\x00\xff\x2f\x00'
    with open(path, 'wb') as f:
        f.write(b'MThd' + struct.pack('>IHHH', 6, 0, 1, PPQ))
        f.write(b'MTrk' + struct.pack('>I', len(trk)) + trk)


def _read_wav(path, np):
    with wave.open(path) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw != 2:
        raise ValueError('只支持 16 位 wav：' + path)
    x = np.frombuffer(raw, '<i2').astype(np.float64).reshape(-1, ch) / 32768.0
    x = x.mean(axis=1)
    if sr != SR:
        n = int(round(len(x) * SR / sr))
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    return x


def _say_wav(voice, rate, text, np):
    d = tempfile.mkdtemp()
    aiff, wav = os.path.join(d, 's.aiff'), os.path.join(d, 's.wav')
    subprocess.run(['say', '-v', voice, '-r', str(rate), '-o', aiff, text], check=True, timeout=60)
    subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@%d' % SR, '-c', '1', aiff, wav], check=True, timeout=60)
    return _read_wav(wav, np)


def _put(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0 or i >= len(buf):
        return
    seg = x[: len(buf) - i] * gain
    buf[i:i + len(seg)] += seg


def _piano(note, vel, dur, np):
    "很简单的合成钢琴（只是预览用；正式的声音请把 .mid 拖进 GarageBand 用你自己的音色导出）"
    f = 440.0 * 2 ** ((note - 69) / 12.0)
    n = int(SR * max(0.3, dur) + SR * 1.2)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k in range(1, 7):
        if f * k > 8000:
            break
        y += (1.0 / k ** 1.2) * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (0.9 + 0.6 * k) / (1 + (note - 40) / 60.0))
    a = int(0.004 * SR)
    y[:a] *= np.linspace(0, 1, a)
    r = int(0.25 * SR)
    if dur * SR < n - r:
        e = int(dur * SR)
        y[e:e + r] *= np.linspace(1, 0.2, r)
        y[e + r:] *= 0.2 * np.exp(-np.arange(n - e - r) / (0.4 * SR))
    return y * (vel / 127.0) * 0.35


def render(folder, voice_dir, notes, events, total_sec):
    """在 folder 里写出：air_piano.mid、game_sfx.wav（游戏里的声音）、mix_preview.wav（简易钢琴 + 游戏声音）、events.json"""
    import numpy as np
    os.makedirs(folder, exist_ok=True)
    write_midi(notes, os.path.join(folder, 'air_piano.mid'))
    with open(os.path.join(folder, 'events.json'), 'w', encoding='utf-8') as f:
        json.dump({'notes': notes, 'events': events, 'total_sec': total_sec}, f, ensure_ascii=False, indent=1)
    n = int((total_sec + 4.0) * SR)
    sfx = np.zeros(n)
    msgs = []
    for e in events:
        try:
            if e.get('k') == 'play':
                _put(sfx, _read_wav(os.path.join(voice_dir, e['name'] + '.wav'), np), e['t'], float(e.get('vol', 0.3)))
            elif e.get('k') == 'say':
                _put(sfx, _say_wav(e['voice'], e['rate'], e['text'], np), e['t'], 0.7)
        except Exception as ex:
            msgs.append('跳过一个声音事件 %r：%r' % (e, ex))
    pia = np.zeros(n)
    for t_on, t_off, nt, v in notes:
        _put(pia, _piano(nt, v, max(0.2, t_off - t_on), np), t_on)

    def save(name, x):
        pk = float(np.max(np.abs(x))) if len(x) else 0.0
        if pk > 0.95:
            x = x * (0.95 / pk)
        pcm = (np.stack([x, x], 1) * 32767).astype('<i2')
        with wave.open(os.path.join(folder, name), 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        try:                                     # 同时存一份 .m4a（小很多，剪辑软件/手机/网页都能直接用）
            wavp = os.path.join(folder, name)
            subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '192000', wavp, wavp[:-4] + '.m4a'], check=True, timeout=120)
        except Exception as ex_:
            msgs.append('转 m4a 失败（wav 还在）：%r' % (ex_,))
    save('game_sfx.wav', sfx)
    save('mix_preview.wav', sfx + pia)
    # 用 Mac 自带的真钢琴音色把 air_piano.mid 渲染成声音（比上面的简易钢琴好听）
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mid2wav')
    if os.path.exists(tool):
        try:
            tmp = os.path.join(folder, '_apple.wav')
            subprocess.run([tool, os.path.join(folder, 'air_piano.mid'), tmp, str(total_sec + 3.0)], check=True, timeout=120, capture_output=True)
            with wave.open(tmp) as w:
                ap = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64).reshape(-1, w.getnchannels()).mean(axis=1) / 32768.0
            os.remove(tmp)
            pk = float(np.max(np.abs(ap))) if len(ap) else 0.0
            if pk > 0:
                ap = ap * (0.7 / pk)                  # 渲染出来的声音偏小，放大
            full = np.zeros(n)
            full[:min(n, len(ap))] = ap[:n]
            save('air_piano_apple.wav', full)
            save('mix_apple.wav', full + sfx)
        except Exception as ex_:
            msgs.append('真钢琴渲染失败（其它文件正常）：%r' % (ex_,))
    return msgs


if __name__ == '__main__':
    # 自测：python3 rec_tools.py 输出文件夹
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '_rec_test')
    notes = [(0.5, 1.5, 60, 90), (1.0, 2.2, 64, 80), (2.0, 3.0, 67, 100), (3.5, 5.0, 72, 70)]
    events = [{'k': 'play', 'name': 'found', 't': 1.0, 'vol': 0.3}, {'k': 'play', 'name': 'bell', 't': 4.0, 'vol': 0.3}]
    print(render(out, os.path.join(here, 'voice'), notes, events, 6.0))
    print('OK ->', out)
