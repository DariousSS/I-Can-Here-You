# 在 TD 的 Textport 里运行（只读）：
#   exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/code/td_scripts/kantan_probe.py', encoding='utf-8').read())
# 结果写进 td_live/kantan_probe.txt（只含英文/数字）
lines = []
k = op('/project1/kantanMapper')
if k is None:
    lines.append('kantanMapper NOT FOUND in /project1')
else:
    lines.append('type=' + str(k.type) + ' family=' + str(k.family))
    try:
        lines.append('inputs=' + str([(i.name if i is not None else None) for i in k.inputs]) + ' numInputs=' + str(len(k.inputConnectors)))
    except Exception as e:
        lines.append('inputs error ' + repr(e)[:80])
    try:
        lines.append('outputs=' + str(len(k.outputConnectors)))
    except Exception as e:
        lines.append('outputs error ' + repr(e)[:80])
    try:
        for pg in k.customPages:
            lines.append('PAGE ' + pg.name + ': ' + str([pp.name for pp in pg.pars]))
    except Exception as e:
        lines.append('pages error ' + repr(e)[:80])
    try:
        lines.append('children: ' + str([(c.name, c.OPType) for c in k.children][:60]))
    except Exception as e:
        lines.append('children error ' + repr(e)[:80])
    for nm in ('in1', 'in2', 'out1', 'Source', 'source', 'null1'):
        o = k.op(nm)
        if o is not None:
            lines.append('has ' + nm + ' type=' + str(o.type))
    try:
        lines.append('par Size from window: ' + str([pp.name for pp in k.pars() if 'size' in pp.name.lower() or 'width' in pp.name.lower() or 'height' in pp.name.lower()]))
    except Exception:
        pass
open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/kantan_probe.txt', 'w').write('\n'.join(lines))
print('kantan probe written')
