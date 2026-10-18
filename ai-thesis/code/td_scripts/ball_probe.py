# 在 TD 的 Textport 里运行（只读）：
#   exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/code/td_scripts/ball_probe.py', encoding='utf-8').read())
# 结果写进 td_live/ball_probe.txt（只含英文/数字）
lines = []
p = op('/project1')
for n in ('ball_img', 'ball_fit', 'ball_tf', 'gz_over', 'gz_fit', 'gz_win', 'gz_exec'):
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
    lines.append('ball_img.file = ' + str(p.op('ball_img').par.file.eval()))
    a = p.op('ball_img').numpyArray()
    lines.append('ball_img alpha max=' + str(float(a[:, :, 3].max())) + ' mean=' + str(float(a[:, :, 3].mean())))
except Exception as e:
    lines.append('ball_img read error ' + repr(e)[:120])
try:
    lines.append('ball_tf.ty = ' + str(p.op('ball_tf').par.ty.eval()) + ' extend=' + str(p.op('ball_tf').par.extend.eval()))
except Exception as e:
    lines.append('ball_tf par error ' + repr(e)[:120])
try:
    lines.append('gz_win.winop = ' + str(p.op('gz_win').par.winop.eval()))
except Exception as e:
    lines.append('gz_win par error ' + repr(e)[:120])
try:
    st = p.op('gz_exec').fetch('st', {})
    lines.append('flash_seen=' + str(st.get('flash_seen')) + ' ball_t0=' + str(st.get('ball_t0')) + ' ball_ty=' + str(st.get('ball_ty')) + ' ball_err=' + str(st.get('ball_err')) + ' screen_err=' + str(st.get('screen_err')))
    lines.append('has _update_ball in exec code: ' + str('_update_ball' in p.op('gz_exec').text))
except Exception as e:
    lines.append('gz_exec read error ' + repr(e)[:120])
open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/ball_probe.txt', 'w').write('\n'.join(lines))
print('ball probe written')
