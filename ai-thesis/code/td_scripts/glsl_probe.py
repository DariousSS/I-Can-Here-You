# 在 TD 的 Textport 里运行（只读，会临时建一个小节点，量完自动删除）：看 GLSL 节点的参数叫什么 -> td_live/glsl_probe.txt
lines = []
p = op('/project1')
tmp = p.create(glslTOP, '__probe_glsl')
try:
    names = [par.name for par in tmp.pars()]
    lines.append('num pars: ' + str(len(names)))
    keep = [n for n in names if any(k in n.lower() for k in ('vec', 'pixel', 'uniform', 'const', 'array', 'format', 'input', 'resolution', 'output', 'mode', 'glsl', 'compute', 'shader', 'dat'))]
    lines.append('relevant pars: ' + str(keep))
    for n in ('vec0name', 'vec0valuex', 'vec0valuey', 'vec0valuez', 'vec0valuew', 'pixeldat', 'computedat', 'mode'):
        try:
            lines.append(n + ' = ' + str(getattr(tmp.par, n).eval()))
        except Exception as e:
            lines.append(n + ' : (没有这个参数)')
    lines.append('children: ' + str([c.name for c in tmp.children]))
    lines.append('project1 nodes starting with __probe_glsl: ' + str([(o.name, o.OPType) for o in p.children if o.name.startswith('__probe_glsl')]))
    try:
        d = tmp.par.pixeldat.eval()
        lines.append('pixeldat op: ' + (d.path + ' | text length ' + str(len(d.text)) if d is not None else 'None'))
        if d is not None:
            lines.append('--- default pixel shader ---')
            lines.append(d.text[:900])
    except Exception as e:
        lines.append('pixeldat read error ' + repr(e)[:100])
except Exception as e:
    lines.append('probe error ' + repr(e)[:200])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/glsl_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
try:
    tmp.destroy()
except Exception as e:
    print('临时节点删除时的提示（可忽略）:', repr(e)[:80])
for o in list(p.children):
    try:
        if o.name.startswith('__probe_glsl'):
            o.destroy()
    except Exception:
        pass
print('glsl probe written')
