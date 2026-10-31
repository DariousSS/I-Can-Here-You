"""合成游戏用的三个小声音，存到 voice/：bell.wav（门铃一声）、bell_stuck.wav（门铃一直乱响然后停）、found.wav（找到光点的轻轻一声）
用法（Mac 终端）: python3 make_game_sfx.py"""
import os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 22050
rng = np.random.default_rng(11)
def ding(freq, dur=0.9, gain=1.0):
    t = np.arange(int(SR * dur)) / SR
    return gain * (np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.22) + 0.35 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t / 0.12) + 0.12 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.08))
def put(out, snd, at):
    i = int(SR * at); out[i:i + len(snd)] += snd[:max(0, len(out) - i)]
def save(name, out):
    out = out / (np.max(np.abs(out)) or 1.0) * 0.8
    os.makedirs(os.path.join(HERE, 'voice'), exist_ok=True)
    with wave.open(os.path.join(HERE, 'voice', name + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    print('saved', name)
o = np.zeros(int(SR * 1.3), dtype=np.float32); put(o, ding(1318), 0.0); save('bell', o)
o = np.zeros(int(SR * 6.0), dtype=np.float32); t = 0.0
while t < 4.4:
    put(o, ding(1318 * rng.choice([1.0, 1.0, 1.01, 0.99]), 0.5, rng.uniform(0.6, 1.0)), t); t += rng.uniform(0.11, 0.30)
save('bell_stuck', o)
o = np.zeros(int(SR * 1.6), dtype=np.float32); put(o, ding(880, 1.0, 0.8), 0.0); put(o, ding(1320, 1.2, 0.6), 0.16); save('found', o)
