# 在 TD 的 Textport 里运行（只读）：木头手相关节点的现状 -> td_live/hand_probe2.txt
lines = []
p = op('/project1')
for n in ('hand_img', 'hand_out', 'hand_fit', 'gz_over', 'gz_final', 'gz_win'):
    o = p.op(n)
    if o is None:
        lines.append(n + ': NOT FOUND')
        continue
    s = n + ': type=' + str(o.type)
    try:
        s += ' size=' + str(o.width) + 'x' + str(o.height)
    except Exception:
        pass
    try:
        s += ' inputs=' + str([(i.name if i is not None else None) for i in o.inputs])
    except Exception:
        pass
    lines.append(s)
try:
    lines.append('hand_img.file=' + str(p.op('hand_img').par.file.eval()))
    for nm in ('sx', 'sy', 'tx', 'ty', 'rotate', 'extend', 'resolutionw', 'resolutionh'):
        lines.append('hand_out.' + nm + '=' + str(getattr(p.op('hand_out').par, nm).eval()))
    lines.append('gz_win.winop=' + str(p.op('gz_win').par.winop.eval()))
except Exception as e:
    lines.append('par error ' + repr(e)[:120])
for n in ('hand_img', 'hand_out', 'hand_fit', 'gz_over', 'gz_final'):
    try:
        a = p.op(n).numpyArray()
        lines.append(n + ' mean rgba=' + str([round(float(a[:, :, i].mean()), 3) for i in range(4)]))
    except Exception as e:
        lines.append(n + ' numpy error ' + repr(e)[:100])
try:
    st = p.op('gz_exec').fetch('st', {})
    lines.append('hand_seen=' + str(st.get('hand_seen')) + ' hand_t0=' + str(st.get('hand_t0')) + ' hand_P=' + str(st.get('hand_P')) + ' hand_vis=' + str(st.get('hand_vis')) + ' hand_err=' + str(st.get('hand_err')))
    lines.append('exec has _update_hand: ' + str('_update_hand' in p.op('gz_exec').text))
    lines.append('cfg hand_on=' + str((st.get('fx_cfg') or {}).get('hand_on')))
except Exception as e:
    lines.append('gz_exec read error ' + repr(e)[:100])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/hand_probe2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('hand probe written')
