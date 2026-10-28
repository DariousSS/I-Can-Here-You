# 在 TD 的 Textport 里运行：右边墙上的字幕（一句一句打出来）。读 subtitles_v6_en.txt；平静时打 CALM 的句子，入侵时打 INVADE 的句子
# SUB 留空 = 自动找"没有纹理的那个新长方形"（你刚在墙上画的）；找不到或找到多个时，把形状名填在这里，例如 SUB = 'item23'
SUB = ''
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
CODE = '''
import time, textwrap, json, hashlib, subprocess, re
FILE = '__FILE__'
VOICE_DIR = '__VOICE__'
SFX_VOL = 0.3                # 拍照声的音量（0~1，想更小就改小）
VOL = {}                     # 不再用苹果的朗读声音（想恢复就写回 {'MAIN': 1.0, 'BOTH': 1.0, 'PHONE': 0.55, 'CHORUS': 0.8}）
SPEED, HOLD, GAP, FADE_IN, FADE_OUT, END_PAUSE = 22.0, 2.0, 0.6, 0.3, 0.6, 8.0
FONT = 56   # 所有人的字号统一（想大想小只改这个数）
STY = {k: (1.0, 1.0, 1.0, FONT) for k in ('MAIN', 'ADULT', 'PHONE', 'BOTH', 'CHORUS')}   # 全部同色同字号，谁在说话让观众自己想象
ALPHA = {'A': 1.0, 'B': 0.6, 'C': 0.82}

def _load():
    L = []
    try:
        with open(FILE, encoding='utf-8') as fh:
            for ln in fh:
                ln = ln.rstrip()
                if not ln.strip() or ln.lstrip().startswith('#'):
                    continue
                parts = [x.strip() for x in ln.split('|', 3)]
                if len(parts) == 4 and parts[0] in ('CALM', 'INVADE'):
                    tx_ = parts[3].split('#')[0].strip()
                    mm_ = re.search(r'[{]([A-Za-z0-9_]+)[}][ ]*$', tx_)
                    sfx_ = mm_.group(1) if mm_ else None
                    if mm_:
                        tx_ = tx_[:mm_.start()].strip()
                    L.append((parts[0].lower(), parts[1], parts[2], tx_, sfx_))
    except Exception as e:
        print('字幕文件读取失败:', repr(e)[:80])
    return L

def onFrameEnd(frame):
    p = op('/project1')
    txt, lv = p.op('sc_sub_txt'), p.op('sc_sub')
    if txt is None or lv is None:
        return
    now = time.time()
    S = me.fetch('S', None)
    if S is None:
        try:
            with open(VOICE_DIR + '/index.json', encoding='utf-8') as fh_:
                idx = json.load(fh_)
        except Exception:
            idx = {}
        S = {'L': _load(), 'i': 0, 'cur': None, 'next': now + 1.0, 'asked': None, 'idx': idx}
    ex = p.op('sc_exec')
    sx = (ex.fetch('s', None) if ex is not None else None) or {}
    phase, inv = sx.get('phase', 'calm'), sx.get('inv', 0.0)
    cur = S['cur']
    if cur is None and now >= S['next'] and S['L']:
        voice_when, voice, typ, full, sfx = S['L'][S['i']]
        ready = (phase == voice_when) and (voice_when == 'calm' or inv > 0.5)
        if not ready:
            if phase != voice_when and S['asked'] != voice_when and ex is not None:
                ex.store('force', voice_when)
                S['asked'] = voice_when
            if voice_when == 'calm' and phase == 'calm':
                ready = True
        if ready:
            S['asked'] = None
            if voice == 'SFX':
                try:
                    subprocess.Popen(['afplay', '-v', str(SFX_VOL), VOICE_DIR + '/' + full + '.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
                S['i'] += 1
                S['next'] = now + 0.6
                if S['i'] >= len(S['L']):
                    S['i'] = 0
                    S['next'] = now + END_PAUSE
            else:
                if sfx:
                    try:
                        subprocess.Popen(['afplay', '-v', str(SFX_VOL), VOICE_DIR + '/' + sfx + '.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        pass
                col = STY.get(voice, STY['MAIN'])
                width = max(8, int(780.0 / (0.72 * col[3])))
                wrapped = chr(10).join(textwrap.wrap(full, width))
                txt.par.fontcolorr, txt.par.fontcolorg, txt.par.fontcolorb = col[0], col[1], col[2]
                txt.par.fontsizex = col[3]
                spd = SPEED
                info = S['idx'].get(hashlib.md5(full.encode('utf-8')).hexdigest()[:10])
                if info and voice in VOL:
                    try:
                        subprocess.Popen(['afplay', '-v', str(VOL[voice]), VOICE_DIR + '/' + info['f']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        spd = max(10.0, min(40.0, len(wrapped) / max(0.5, info['dur'] * 0.95)))
                    except Exception:
                        pass
                cur = S['cur'] = {'wrapped': wrapped, 'alpha': ALPHA.get(typ, 0.8), 't0': now, 'shown': None, 'spd': spd}
    op_ = 0.0
    if cur is not None:
        n = min(len(cur['wrapped']), int((now - cur['t0']) * cur['spd']) + 1)
        shown = cur['wrapped'][:n]
        if shown != cur['shown']:
            cur['shown'] = shown
            txt.par.text = shown
        te = cur['t0'] + len(cur['wrapped']) / cur['spd'] + HOLD
        fin = min(1.0, (now - cur['t0']) / FADE_IN)
        fout = max(0.0, min(1.0, (te + FADE_OUT - now) / FADE_OUT))
        op_ = fin * fout * cur['alpha']
        if now > te + FADE_OUT:
            S['cur'] = None
            txt.par.text = ''
            S['i'] += 1
            S['next'] = now + GAP
            if S['i'] >= len(S['L']):
                S['i'] = 0
                S['next'] = now + END_PAUSE
    lv.par.opacity = op_
    me.store('S', S)
'''
_ex0 = op('/project1/sc_sub_exec')
if _ex0 is not None:
    _ex0.text = CODE.replace('__FILE__', BASE + '/subtitles_v6_en.txt').replace('__VOICE__', BASE + '/voice') % ()
    _ex0.store('S', None)
    print('OK: 字幕代码已更新（形状和节点不变）')
else:
    p = op('/project1')
    cand = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        pr = c.op('parameters')
        if pr is None or not hasattr(pr.par, 'Texture'):
            continue
        cur_ = pr.par.Texture.eval()
        cur_ = '' if cur_ is None else str(getattr(cur_, 'path', cur_))
        if (SUB and c.name == SUB) or (not SUB and cur_ == ''):
            cand.append(c)
    if len(cand) != 1:
        print('找到', len(cand), '个候选形状：', [c.name for c in cand], '。请用 shape_probe.py 看墙上那个长方形叫什么，填到本脚本的 SUB = 里')
    else:
        c = cand[0]
        pts = [(q.x, q.y) for q in c.op('script1').points]
        w_ = max(q[0] for q in pts) - min(q[0] for q in pts)
        h_ = max(q[1] for q in pts) - min(q[1] for q in pts)
        asp = w_ / h_ if h_ > 0 else 1.0
        tx = p.op('sc_sub_txt') or p.create(textTOP, 'sc_sub_txt')
        for k_, v_ in (('outputresolution', 'custom'), ('resolutionw', 1000), ('resolutionh', int(1000 / asp)), ('text', ''), ('fontsizex', 74), ('alignx', 'center'), ('aligny', 'center'),
                       ('fontcolorr', 1.0), ('fontcolorg', 1.0), ('fontcolorb', 1.0), ('bgcolorr', 0.0), ('bgcolorg', 0.0), ('bgcolorb', 0.0), ('bgalpha', 0.0)):
            try:
                setattr(tx.par, k_, v_)
            except Exception as e:
                print('sc_sub_txt', k_, '设置失败:', repr(e)[:60])
        lv = p.op('sc_sub') or p.create(levelTOP, 'sc_sub')
        lv.inputConnectors[0].connect(tx)
        lv.par.opacity = 0.0
        ex = p.op('sc_sub_exec') or p.create(executeDAT, 'sc_sub_exec')
        ex.text = CODE.replace('__FILE__', BASE + '/subtitles_v6_en.txt').replace('__VOICE__', BASE + '/voice') % ()
        ex.par.frameend = True
        ex.par.active = True
        ex.store('S', None)
        tx.nodeX, tx.nodeY = 1900, -3000
        lv.nodeX, lv.nodeY = 2100, -3000
        ex.nodeX, ex.nodeY = 2300, -3000
        c.op('parameters').par.Texture = '/project1/sc_sub'
        c.op('parameters').par.Showtexture = True
        c.par.render = True
        print('OK: 字幕已接到形状', c.name, '宽高比', round(asp, 2))
        print('平静时会打 CALM 的句子；想马上看入侵时的句子：op(\'/project1/sc_exec\').store(\'force\',\'invade\')')
