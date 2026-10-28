# 在 TD 的 Textport 里运行：检查云朵为什么没出现（只读，并把明显的开关打开：item4 显示、纹理 sc_blob）
p = op('/project1')
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name == 'item4' and c.op('parameters') is not None:
        pr = c.op('parameters').par
        v = pr.Texture.eval()
        print('item4 纹理:', '' if v is None else str(getattr(v, 'path', v)), '| 显示(render):', bool(c.par.render.eval()), '| Showtexture:', bool(pr.Showtexture.eval()))
        if bool(c.par.render.eval()) is False:
            c.par.render = True
            print('  -> item4 之前是隐藏的，已打开')
        if str(getattr(v, 'path', v)) != '/project1/sc_blob':
            pr.Texture = '/project1/sc_blob'
            print('  -> item4 纹理不对，已改成 sc_blob')
b = p.op('sc_blob')
if b is None:
    print('没有 sc_blob 节点：请运行 suitcase_all.py')
else:
    print('sc_blob uB =', [round(getattr(b.par, 'vec0value' + a).eval(), 3) for a in 'xyzw'], '(最后一个数字是入侵程度，入侵时应该接近 1)')
    print('sc_blob uC =', [round(getattr(b.par, 'vec1value' + a).eval(), 3) for a in 'xyzw'])
    print('sc_blob 着色器错误:', repr(b.errors()), '| 警告:', repr(b.warnings()), '| 着色器文字长度:', len(p.op('sc_blob_pixel').text))
ex = p.op('sc_exec')
s = ex.fetch('s', None) if ex is not None else None
print('sc_exec 状态:', {k: (round(v, 2) if isinstance(v, float) else v) for k, v in (s or {}).items() if k in ('phase', 'inv', 'snd')}, '| 自动随机切换:', ex.fetch('auto', False) if ex is not None else None)
print('提示：入侵时再运行一次本脚本，看 sc_blob uB 的最后一个数字是不是接近 1')
