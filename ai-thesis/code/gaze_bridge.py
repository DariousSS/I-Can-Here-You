"""
目光 -> 隐藏层 桥接（文件版）。

  TD 不停地写   td_live/gaze_bridge/params.json
      {"gaze": {"x": 0.4, "y": 0.3, "on": 1},   目光在脸的哪里（0-1，左上角是 0,0），on=0 表示没在看
       "new_face": 3,                          这个数字每加 1，就换一张新脸（以后可以由声音触发）
       "reset": 0}                             这个数字每加 1，就把累积清零
  本程序维护"累积图"（看得越久越亮，移开慢慢退），用它去改隐藏层，画出脸，写成
      td_live/gaze_bridge/out.png    脸
      td_live/gaze_bridge/heat.png   累积图（人的注意力热图，可以叠在脸上）
      td_live/gaze_bridge/status.json

为了不烫：累积图没怎么变就不重画。Lucy 每次重画约 1 秒（10 步），所以是"慢慢变"的手感。

运行（在 ai-thesis/code 目录）：
  python gaze_bridge.py                       # Lucy，默认参数
  python gaze_bridge.py --model gan --layer 3 --channel 408 --fmax 49 --size 256   # 用 GAN（快很多）
  python gaze_bridge.py --fmax 80 --rise 4 --decay 12 --sigma 0.1
关掉：ctrl+c
"""
import argparse
import json
import os
import glob
import math
import random
import re
import subprocess
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gaze_core import GazeFace   # noqa: E402
import style_kid as SK   # noqa: E402

DIR = "/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge"
ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=DIR)
ap.add_argument("--model", default="lucy", choices=["lucy", "gan"])
ap.add_argument("--layer", default="U3", help="Lucy: D0-D4/MID/U0-U4；GAN: 0-6")
ap.add_argument("--channel", type=int, default=102)
ap.add_argument("--fmax", type=float, default=100.0, help="累积满了时调多大（Lucy 约 60-140；GAN 约 20-50）")
ap.add_argument("--steps", type=int, default=10, help="Lucy 的擦雾步数（5 更快更糊，10 折中，20 最好）")
ap.add_argument("--rise", type=float, default=3.0, help="一直盯着，大约几秒累积满")
ap.add_argument("--decay", type=float, default=10.0, help="移开目光后，大约几秒退掉")
ap.add_argument("--sigma", type=float, default=0.12, help="一次凝视影响多大一圈（占脸宽的比例）")
ap.add_argument("--t0", type=float, default=0.0, help="Lucy：从擦雾的哪一段开始改（0=从头，0.5=只改后半段，更含蓄）")
ap.add_argument("--size", type=int, default=512)
ap.add_argument("--eps", type=float, default=0.04, help="累积图变化超过多少才重画")
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--palette", default=None, help="琴键乐器清单（默认 <dir>/palette_lucy.json）")
ap.add_argument("--no-attn", action="store_true", help="不记录 AI 注意力（不生成 ai_heat.png）")
ap.add_argument("--no-piano", action="store_true", help="不读琴键")
ap.add_argument("--keep-dwell", action="store_true", help="换新脸时不清零累积")
args = ap.parse_args()

os.makedirs(args.dir, exist_ok=True)
P, OUT, HEAT, ST = (os.path.join(args.dir, n) for n in ("params.json", "out.png", "heat.png", "status.json"))
AI_HEAT = os.path.join(args.dir, "ai_heat.png")
AI_ATTN = os.path.join(args.dir, "ai_attn.png")
print(f"加载 {args.model} …")
layer = args.layer
g = GazeFace(model=args.model, layer=layer, channel=args.channel, fmax=args.fmax, steps=args.steps,
             rise=args.rise, decay=args.decay, sigma=args.sigma, size=args.size, t0=args.t0)


PAL = args.palette or os.path.join(args.dir, "palette_lucy.json")
_pal = {"mtime": 0, "data": {"instruments": [], "new_face_notes": [], "new_face_pedal": True, "attack_sec": 0.6, "release_sec": 3.0}}
levels, prev_val, seen_names = {}, {}, set()
_NOTE = re.compile(r"ch(\d+)n(\d+)$")
_PEDAL = re.compile(r"ch(\d+)c(?:trl)?64$")


def load_pal():
    try:
        mt = os.path.getmtime(PAL)
        if mt != _pal["mtime"]:
            _pal["data"] = json.load(open(PAL, encoding="utf-8"))
            _pal["mtime"] = mt
            n = len(_pal["data"].get("instruments", []))
            print(f"读入琴键乐器清单：{n} 个")
    except Exception as e:
        if not _pal["mtime"]:
            print("[读不到 palette_lucy.json，琴键暂不起作用]", repr(e)[:120])
            _pal["mtime"] = -1
    return _pal["data"]


def piano_step(midi, dt):
    """返回 (extra_edits, new_face_trigger)。midi 是 TD 传来的 {通道名: 数值 0-1}。"""
    pal = load_pal()
    notes = {}
    pedal = 0.0
    for name, val in midi.items():
        if name not in seen_names:
            seen_names.add(name)
            print(f"[新控件] {name} = {val}")
        m = _NOTE.match(name)
        if m:
            notes[int(m.group(2))] = max(notes.get(int(m.group(2)), 0.0), float(val))
        elif _PEDAL.match(name):
            pedal = max(pedal, float(val))
    off = int(pal.get("note_offset", 0))
    extra, ins_list = {}, pal.get("instruments", [])
    for i, ins in enumerate(ins_list):
        tgt = notes.get(int(ins["note"]) + off, 0.0)
        if tgt > 0:
            fl = float(pal.get("velocity_floor", 0.0))
            tgt = fl + (1.0 - fl) * tgt      # 轻按也至少到 floor（0=不处理）
        cur = levels.get(i, 0.0)
        tau = pal.get("attack_sec", 0.6) if tgt > cur else pal.get("release_sec", 3.0)
        cur += (tgt - cur) * (1 - math.exp(-dt / max(0.05, tau)))
        if cur < 0.01 and tgt == 0:
            cur = 0.0
        levels[i] = cur
        if cur > 0.02:
            f = float(ins["fmax"]) * cur
            e = {"channel": int(ins["channel"]), "factor": f, "mode": ins.get("mode", "even"),
                 "t0": float(ins.get("t0", 0.0)), "t1": float(ins.get("t1", 1.0))}
            L = ins["layer"]
            if L not in extra or extra[L]["factor"] < f:
                extra[L] = e
    trig = False
    for n in pal.get("new_face_notes", []):
        k = int(n) + off
        v = notes.get(k, 0.0)
        if v > 0 and prev_val.get(("n", k), 0.0) == 0:
            trig = True
        prev_val[("n", k)] = v
    for cname in pal.get("new_face_controls", []):
        raw = float(midi.get(cname, 0.0))
        v = raw / 127.0 if "ctrl" in cname else raw        # 控制器 0-127 -> 0-1
        if v > 0.5 and prev_val.get(cname, 0.0) <= 0.5:
            trig = True
        prev_val[cname] = v
    return extra, trig

rec = None
if args.model == "lucy" and not args.no_attn:
    import lucy_attention as AT
    rec = AT.install({})
    print("已装上 AI 注意力记录层（生成时顺手记录，不改变脸）")


def save_atomic(im, path):
    tmp = path + ".tmp.png"
    im.save(tmp)
    os.replace(tmp, path)


WHISPER_DIR = os.path.join(os.path.dirname(os.path.abspath(args.dir)), "whispers")
WHISPER_CFG = os.path.join(args.dir, "whisper.json")
_wh = {"proc": None, "last": None, "t_last": 0.0, "cfg": {"on": True, "vol": 0.35, "ambient_sec": 0, "min_gap_sec": 2.0}, "t_cfg": 0.0, "t_amb": time.time()}


def _wh_cfg():
    if time.time() - _wh["t_cfg"] > 2.0:
        _wh["t_cfg"] = time.time()
        try:
            with open(WHISPER_CFG, encoding="utf-8") as fh:
                j = json.load(fh)
            _wh["cfg"].update({k: j[k] for k in ("on", "vol", "ambient_sec", "min_gap_sec") if k in j})
        except Exception:
            pass
    return _wh["cfg"]


def whisper(reason=""):
    """随机念一个低语词（afplay 播放 whispers/ 里的文件）。上一个还没念完、或离上次太近就跳过。"""
    cfg = _wh_cfg()
    if not cfg.get("on", True):
        return
    now = time.time()
    if now - _wh["t_last"] < float(cfg.get("min_gap_sec", 2.0)):
        return
    p = _wh["proc"]
    if p is not None and p.poll() is None:
        return
    files = sorted(glob.glob(os.path.join(WHISPER_DIR, "*.aiff")))
    if not files:
        return
    pool = [f for f in files if f != _wh["last"]] or files
    f = random.choice(pool)
    vol = min(1.0, max(0.0, float(cfg.get("vol", 0.35))))
    try:
        _wh["proc"] = subprocess.Popen(["afplay", "-v", str(vol), f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _wh["last"], _wh["t_last"] = f, now
        print("低语：", os.path.basename(f), reason)
    except Exception as e:
        print("[低语出错]", repr(e)[:80])


def style_preset():
    """童核滤镜：读 style.json 的 preset（off/candy/crayon/dream），每次画脸时读一次。读不到就是 off。"""
    try:
        with open(os.path.join(args.dir, "style.json"), encoding="utf-8") as f:
            return json.load(f).get("preset", "off")
    except Exception:
        return "off"


def render_and_save():
    """画一张脸，存 out.png；若装了记录层，再存"AI 注意力叠图" ai_heat.png。"""
    if rec is not None:
        rec.clear()
    im = g.face(seed, extra if not args.no_piano else None)
    sp = style_preset()
    save_atomic(SK.stylize(im, sp), OUT)
    if rec is not None:
        try:
            ov = AT.ai_overlay(rec, im, size=im.size[0])
            if ov is not None:
                save_atomic(SK.stylize(ov, sp), AI_HEAT)
            bw = AT.ai_bw(rec, size=im.size[0])            # 纯黑白注意力图（没有脸）
            if bw is not None:
                save_atomic(SK.stylize_bw(bw, sp), AI_ATTN)
        except Exception as e:
            print("[AI 注意力叠图出错，已跳过]", repr(e)[:120])


def read_params(old):
    try:
        with open(P, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return old


seed = args.seed
params = read_params({})
last_new, last_reset = params.get("new_face", 0), params.get("reset", 0)
new_event = False
last_D = None
last_levels = {}
extra = {}
force = True
renders, t_rep = 0, time.time()
last_t = time.time()
print("\n已就绪。TD 写 params.json，这里就会画。关掉：ctrl+c\n")
try:
    while True:
        now = time.time()
        dt = min(0.5, now - last_t)
        last_t = now
        params = read_params(params)
        _c = _wh_cfg()
        if float(_c.get("ambient_sec", 0)) > 0 and time.time() - _wh["t_amb"] > float(_c["ambient_sec"]):
            _wh["t_amb"] = time.time()
            whisper("(随机)")
        if params.get("new_face", 0) != last_new:
            last_new = params.get("new_face", 0)
            seed = random.randint(1, 10 ** 6)
            if not args.keep_dwell:
                g.reset()
            force = True
            new_event = True
            print(f"换新脸：种子 {seed}")
            whisper("(换脸)")
        if params.get("reset", 0) != last_reset:
            last_reset = params.get("reset", 0)
            g.reset()
            force = True
        if not args.no_piano:
            extra, key_new = piano_step(params.get("midi") or {}, dt)
            if key_new:
                seed = random.randint(1, 10 ** 6)
                if not args.keep_dwell:
                    g.reset()
                force = True
                new_event = True
                print(f"琴键/踏板换新脸：种子 {seed}")
                whisper("(琴键换脸)")
        gz = params.get("gaze") or {}
        gaze = (gz.get("x", 0.5), gz.get("y", 0.5)) if gz.get("on", 0) else None
        g.update(gaze, dt)
        changed = last_D is None or (g.D - last_D).abs().max().item() > args.eps
        if not args.no_piano and any(abs(levels.get(i, 0.0) - last_levels.get(i, 0.0)) > 0.06 for i in set(levels) | set(last_levels)):
            changed = True
        if force or changed:
            t1 = time.time()
            try:
                if new_event and g.model == "lucy" and g.steps > 5:
                    s0, g.steps = g.steps, 5                       # 先画一张 5 步草稿，马上显示
                    try:
                        render_and_save()
                    finally:
                        g.steps = s0
                new_event = False
                render_and_save()
                save_atomic(g.heat(256), HEAT)
                last_D = g.D.clone()
                last_levels = dict(levels)
                force = False
                renders += 1
                json.dump({"seed": seed, "dwell_max": round(float(g.D.max()), 3), "render_sec": round(time.time() - t1, 2)},
                          open(ST, "w"))
            except Exception as e:
                print("[画图出错，已跳过]", repr(e)[:160])
                force = False
        if time.time() - t_rep > 10:
            print(f"最近 10 秒画了 {renders} 张（累积最大 {float(g.D.max()):.2f}）")
            renders, t_rep = 0, time.time()
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\n已退出。")
