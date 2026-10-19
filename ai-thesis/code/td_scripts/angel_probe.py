# 在 TD 的 Textport 里运行（只读）：天使有没有建出来、现在是什么状态 -> td_live/angel_probe.txt
lines = []
p = op('/project1')
for n in ('angel_body_img', 'angel_pupil_img', 'blank_img', 'angel_body_tf', 'angel_pupil_tf', 'angel_comp', 'angel_fade', 'scene_all', 'scene_out', 'hand_fit', 'gz_final'):
    o = p.op(n)
    if o is None:
        lines.append(n + ': NOT FOUND')
        continue
    s = n + ': ' + str(o.type)
    try:
        s += ' size=' + str(o.width) + 'x' + str(o.height) + ' inputs=' + str([(i.name if i is not None else None) for i in o.inputs])
    except Exception:
        pass
    lines.append(s)
try:
    lines.append('angel_body_img.file=' + str(p.op('angel_body_img').par.file.eval()))
    lines.append('angel_fade.cross=' + str(p.op('angel_fade').par.cross.eval()))
    b = p.op('angel_body_tf').par
    lines.append('body sx,sy,tx,ty=' + str([round(b.sx.eval(), 3), round(b.sy.eval(), 3), round(b.tx.eval(), 3), round(b.ty.eval(), 3)]))
except Exception as e:
    lines.append('par error ' + repr(e)[:100])
for n in ('angel_fade', 'scene_all'):
    try:
        a = p.op(n).numpyArray()
        lines.append(n + ' mean rgba=' + str([round(float(a[:, :, i].mean()), 4) for i in range(4)]))
    except Exception as e:
        lines.append(n + ' numpy error ' + repr(e)[:80])
try:
    st = p.op('gz_exec').fetch('st', {})
    lines.append('ang_t0=' + str(st.get('ang_t0')) + ' ang_vis=' + str(st.get('ang_vis')) + ' angel_err=' + str(st.get('angel_err')) + ' ang_seen=' + str(st.get('ang_seen')))
    lines.append('exec has _update_angel: ' + str('_update_angel' in p.op('gz_exec').text) + ' | has angel_idle_level: ' + str('angel_idle_level' in p.op('gz_exec').text))
    lines.append('cfg angel_idle_level=' + str((st.get('fx_cfg') or {}).get('angel_idle_level')) + ' angel_on=' + str((st.get('fx_cfg') or {}).get('angel_on')))
except Exception as e:
    lines.append('gz_exec read error ' + repr(e)[:100])
try:
    k = op('/project1/kantanMapper/project/allShapes')
    sh = []
    for c in k.children:
        pr = c.op('parameters')
        if pr is not None and hasattr(pr.par, 'Texture'):
            v = pr.par.Texture.eval()
            sh.append((str(pr.par.Name.eval()), str(getattr(v, 'path', v))))
    lines.append('kantan shapes (name, texture): ' + str(sh))
except Exception as e:
    lines.append('kantan read error ' + repr(e)[:80])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/angel_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('angel probe written')
