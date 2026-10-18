# 在 TD 的 Textport 里运行（只读）：列出所有显示器 + gz_win 的全部设置 -> td_live/win_probe.txt
lines = []
try:
    for i, m in enumerate(monitors):
        d = {}
        for a in ('width', 'height', 'scaledWidth', 'scaledHeight', 'x', 'y', 'primary', 'isPrimary', 'name', 'index', 'left', 'top', 'right', 'bottom'):
            if hasattr(m, a):
                d[a] = getattr(m, a)
        lines.append('monitor ' + str(i) + ': ' + str(d))
    lines.append('num monitors: ' + str(len(monitors)))
except Exception as e:
    lines.append('monitors error ' + repr(e)[:100])
w = op('/project1/gz_win')
if w is None:
    lines.append('gz_win NOT FOUND')
else:
    for par in w.pars():
        try:
            lines.append('gz_win.' + par.name + ' = ' + str(par.eval()))
        except Exception:
            pass
open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/win_probe.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('win probe written')
