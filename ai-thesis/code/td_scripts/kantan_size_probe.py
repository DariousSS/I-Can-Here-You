# 在 TD 的 Textport 里运行（只读）：看 Kantan 每个形状的大小存在哪里 -> td_live/kantan_size_probe.txt
lines = []
root = op('/project1/kantanMapper/project/allShapes')
for c in root.children:
    p = c.op('parameters')
    if p is None or not hasattr(p.par, 'Texture'):
        continue
    nm = str(p.par.Name.eval()) if hasattr(p.par, 'Name') else '?'
    lines.append('=== SHAPE ' + c.path + ' name=' + nm)
    d = {}
    for par in p.customPars:
        try:
            v = par.eval()
            d[par.name] = (round(v, 3) if isinstance(v, float) else (str(v)[:80]))
        except Exception:
            pass
    lines.append('params: ' + str(d))
    lines.append('children: ' + str([(k.name, k.OPType) for k in c.children]))
    for k in c.children:
        try:
            if k.OPType in ('tableDAT', 'textDAT') and k.numRows < 12 and len(k.text) < 900:
                lines.append('  ' + k.name + ' = ' + k.text.replace('\n', ' | ')[:700])
            elif k.OPType == 'scriptSOP' or k.family == 'SOP':
                pts = [(round(pt.x, 1), round(pt.y, 1)) for pt in k.points][:8]
                lines.append('  SOP ' + k.name + ' points=' + str(pts))
        except Exception:
            pass
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/kantan_size_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('kantan size probe written, shapes:', sum(1 for l in lines if l.startswith('=== SHAPE')))
