# 在 TD 的 Textport 里运行（只读，不改任何设置）：
#   exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/code/td_scripts/screen_probe.py', encoding='utf-8').read())
# 作用：把 显示器信息 + gz_win(窗口) + gz_fit 的设置 写进 td_live/screen_probe.txt（只含英文/数字）。
lines = []
try:
    for i, m in enumerate(monitors):
        lines.append('monitor %d: w=%s h=%s scaledW=%s scaledH=%s x=%s y=%s isPrimary=%s' % (
            i, m.width, m.height, m.scaledWidth, m.scaledHeight,
            getattr(m, 'x', None), getattr(m, 'y', None), getattr(m, 'isPrimary', None)))
except Exception as e:
    lines.append('monitors error ' + repr(e)[:100])
p = op('/project1')
lines.append('num monitors: ' + str(len(monitors)))
for n in ('crowd_bg', 'cf0', 'crowd_comp', 'gz_mode', 'gz_xfade', 'gz_xfade2', 'gz_tile', 'gz_switch'):
    o = p.op(n)
    lines.append('size ' + n + ': ' + (str(o.width) + 'x' + str(o.height) if o is not None else 'NOT FOUND'))
for n in ('gz_fit', 'gz_win', 'gz_tile', 'gz_mode', 'gz_xfade'):
    o = p.op(n)
    if o is None:
        lines.append(n + ': NOT FOUND')
        continue
    lines.append(n + ': type=' + str(o.type) + ' w=' + str(o.width if hasattr(o, 'width') else None) + ' h=' + str(o.height if hasattr(o, 'height') else None))
    for par in o.pars():
        try:
            nm = par.name.lower()
            if any(k in nm for k in ('res', 'fit', 'size', 'monitor', 'winop', 'borders', 'justify', 'offset', 'pos', 'aspect', 'fill', 'width', 'height', 'screen', 'open', 'win', 'part')):
                lines.append('   ' + o.name + '.' + par.name + ' = ' + str(par.eval()))
        except Exception:
            pass
open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/screen_probe.txt', 'w').write('\n'.join(lines))
print('screen probe written')
