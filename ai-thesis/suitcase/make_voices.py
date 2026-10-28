"""把字幕文件里的每一句提前读成声音（macOS 自带的 say，不用任何模型，几秒钟就好），存到 voice/ 文件夹，并记下每句多长。
  MAIN / BOTH = 英文童声 Junior；PHONE = 隔着墙的电话（只读"……"之间没被挖掉的部分，声音闷）；CHORUS = 好几个声音叠在一起（人数让观众猜）；ADULT = 不出声
用法（Mac 终端）: nice -n 15 python3 make_voices.py"""
import os, json, hashlib, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'subtitles_v6_en.txt')
OUT = os.path.join(HERE, 'voice')
SR = 22050
os.makedirs(OUT, exist_ok=True)

def say_np(text, voice, rate=170):
    tmp = os.path.join(OUT, '_t')
    subprocess.run(['say', '-v', voice, '-r', str(rate), '-o', tmp + '.aiff', text], check=True)
    subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@%d' % SR, '-c', '1', tmp + '.aiff', tmp + '.wav'], check=True)
    with wave.open(tmp + '.wav') as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    os.remove(tmp + '.aiff'); os.remove(tmp + '.wav')
    return a

def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)

def muffle(a, n=14):
    return np.convolve(a, np.ones(n, dtype=np.float32) / n, mode='same')

def save(a, path):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

def segs(text):
    return [x.strip(' ,') for x in text.split('…') if x.strip(' ,')]

def render(voice, text):
    if voice in ('MAIN', 'BOTH'):
        return say_np(text.replace('…', ','), 'Junior', 165)
    if voice == 'PHONE':
        parts = []
        for sg in segs(text):
            parts += [say_np(sg, 'Kathy', 180), silence(0.4)]
        return muffle(np.concatenate([silence(0.15)] + parts), 14) * 0.9
    if voice == 'CHORUS':
        ss = segs(text) or [text]
        base = []
        for k, (vn, off) in enumerate((('Kathy', 0.0), ('Fred', 0.13), ('Samantha', 0.27))):
            pieces = []
            for sg in ss:
                pieces += [say_np(sg, vn, 165 + 6 * k), silence(0.35)]
            base.append(np.concatenate([silence(off)] + pieces))
        n = max(len(b) for b in base)
        mix = sum(np.pad(b, (0, n - len(b))) for b in base) / 2.0
        return muffle(mix, 8)
    return None

index = {}
try:
    index = json.load(open(os.path.join(OUT, 'index.json'), encoding='utf-8'))      # 已经做好的句子不再重做
except Exception:
    index = {}
for ln in open(SRC, encoding='utf-8'):
    ln = ln.rstrip()
    if not ln.strip() or ln.lstrip().startswith('#'):
        continue
    parts = [x.strip() for x in ln.split('|', 3)]
    if len(parts) != 4 or parts[0] not in ('CALM', 'INVADE'):
        continue
    voice, text = parts[1], parts[3].split('#')[0].strip()
    key = hashlib.md5(text.encode('utf-8')).hexdigest()[:10]
    if voice == 'ADULT' or key in index:
        continue
    a = render(voice, text)
    if a is None or len(a) == 0:
        continue
    peak = float(np.max(np.abs(a))) or 1.0
    a = a / peak * 0.85
    fn = key + '.wav'
    save(a, os.path.join(OUT, fn))
    index[key] = {'f': fn, 'dur': round(len(a) / SR, 2), 'voice': voice, 'text': text}
    print(voice, '%.1fs' % (len(a) / SR), '|', text[:60])
json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('完成：', len(index), '句，在', OUT)
