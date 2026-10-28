"""合成"拍照声"（快门咔嚓两下），不用下载任何东西，存成 voice/shutter.wav
用法（Mac 终端）: python3 make_sfx.py"""
import os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 22050
rng = np.random.default_rng(7)

def click(dur, gain, hp=True):
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    if hp:
        noise = noise - np.convolve(noise, np.ones(6, dtype=np.float32) / 6, mode='same')
    env = np.exp(-t / (dur / 5.0))
    thump = np.sin(2 * np.pi * 180 * t) * np.exp(-t / (dur / 3.0)) * 0.6
    return (noise * env * 0.8 + thump) * gain

def make(name, shots, total):
    out = np.zeros(int(SR * total), dtype=np.float32)
    for start in shots:
        for off, dur, g in ((0.00, 0.045, 1.0), (0.085, 0.060, 0.8)):
            c = click(dur, g)
            i = int(SR * (start + off))
            out[i:i + len(c)] += c
    out = out / (np.max(np.abs(out)) or 1.0) * 0.85
    os.makedirs(os.path.join(HERE, 'voice'), exist_ok=True)
    with wave.open(os.path.join(HERE, 'voice', name + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    print('ok: voice/' + name + '.wav')

make('shutter', [0.0], 0.5)
make('shutter3', [0.0, 0.42, 0.78], 1.2)
