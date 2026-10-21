# 在 TD 的 Textport 里运行：触发一次手，并在手戳到城堡的那一刻（约 4 秒后）自动量每一层有没有东西 -> td_live/hand_live_probe.txt
# 运行后请【不要动】，等 5 秒，看到 "hand live probe written" 再告诉我。
import json, time

BR = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'
OUT = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/hand_live_probe.txt'


def snap(tag):
    L = []
    p = op('/project1')

    def mean(path):
        try:
            a = op(path).numpyArray()
            return [round(float(a[:, :, i].mean()), 4) for i in range(4)]
        except Exception as e:
            return 'err ' + repr(e)[:50]
    for path in ('/project1/hand_out', '/project1/scene_out', '/project1/scene_all', '/project1/kantanMapper/out1', '/project1/poke_fx', '/project1/map_fit'):
        L.append(tag + ' ' + path.split('/')[-1] + ' mean rgba=' + str(mean(path)))
    try:
        h = p.op('hand_out').par
        L.append(tag + ' hand_out sx,sy,tx,ty=' + str([round(h.sx.eval(), 4), round(h.sy.eval(), 4), round(h.tx.eval(), 3), round(h.ty.eval(), 3)]))
        f = p.op('poke_fx').par
        L.append(tag + ' uPoke=' + str((round(f.vec0valuex.eval(), 3), round(f.vec0valuey.eval(), 3), round(f.vec0valuez.eval(), 3), f.vec0valuew.eval())))
        st = p.op('gz_exec').fetch('st', {})
        pt = st.get('poke_time')
        L.append(tag + ' hand_t0=' + str(st.get('hand_t0')) + ' poke_time_in(s)=' + (str(round(pt - time.time(), 2)) if pt else 'None') + ' hand_err=' + str(st.get('hand_err')) + ' scene=' + str(st.get('scene')) + ' std=' + str(bool(st.get('std'))))
    except Exception as e:
        L.append(tag + ' par error ' + repr(e)[:100])
    return L


lines = []
lines += snap('[触发前]')
try:
    with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/hand_test.json', 'w', encoding='utf-8') as f_:
        json.dump({'t': time.time()}, f_)
    lines.append('已写入 hand_test.json（触发一次手）')
except Exception as e:
    lines.append('触发失败 ' + repr(e)[:80])
lines.append('config: ' + open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/audio_fx.json', encoding='utf-8').read().count('"mapping_on": true').__str__() + ' (1 表示映射开着)')
# 形状信息
try:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        pr = c.op('parameters')
        if pr is None or not hasattr(pr.par, 'Texture'):
            continue
        v = pr.par.Texture.eval()
        sc = c.op('script1')
        bb = None
        if sc is not None:
            pts = [(q.x, q.y) for q in sc.points]
            if pts:
                bb = (round(min(a[0] for a in pts)), round(min(a[1] for a in pts)), round(max(a[0] for a in pts)), round(max(a[1] for a in pts)))
        lines.append('shape ' + str(pr.par.Name.eval()) + ' tex=' + str(getattr(v, 'path', v)).split('/')[-1] + ' show=' + str(pr.par.Showtexture.eval()) + ' bbox=' + str(bb))
except Exception as e:
    lines.append('shapes error ' + repr(e)[:80])
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
LATER = r'''
import time
lines = []
def mean(path):
    try:
        a = op(path).numpyArray()
        return [round(float(a[:, :, i].mean()), 4) for i in range(4)]
    except Exception as e:
        return 'err ' + repr(e)[:50]
for path in ('/project1/hand_out', '/project1/scene_out', '/project1/scene_all', '/project1/kantanMapper/out1', '/project1/poke_fx', '/project1/map_fit'):
    lines.append('[手戳到时] ' + path.split('/')[-1] + ' mean rgba=' + str(mean(path)))
p = op('/project1')
h = p.op('hand_out').par
lines.append('[手戳到时] hand_out sx,sy,tx,ty=' + str([round(h.sx.eval(), 4), round(h.sy.eval(), 4), round(h.tx.eval(), 3), round(h.ty.eval(), 3)]))
f = p.op('poke_fx').par
lines.append('[手戳到时] uPoke=' + str((round(f.vec0valuex.eval(), 3), round(f.vec0valuey.eval(), 3), round(f.vec0valuez.eval(), 3), f.vec0valuew.eval())))
st = p.op('gz_exec').fetch('st', {})
lines.append('[手戳到时] hand_t0=' + str(st.get('hand_t0')) + ' hand_err=' + str(st.get('hand_err')) + ' scene=' + str(st.get('scene')) + ' hand_vis=' + str(st.get('hand_vis')))
with open(OUT, 'a', encoding='utf-8') as fh:
    fh.write('\\n' + '\\n'.join(lines))
print('hand live probe written')
'''
run('OUT = ' + repr(OUT) + '\n' + LATER, delayMilliSeconds=4000)
print('已触发手。请不要动，等 5 秒，看到 hand live probe written。')
