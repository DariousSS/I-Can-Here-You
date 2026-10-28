# 在 TD 的 Textport 里运行：一键修云朵（对纹理 -> 确认云朵节点和着色器 -> 触发入侵 -> 2.5 秒后打印云朵有没有真的画出来）
# 运行前先在 Kantan 画布空白处点一下，取消所有形状的选中
BASE_ = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase/'
exec(open(BASE_ + 'fix_textures.py', encoding='utf-8').read())
_p = op('/project1')
if _p.op('sc_blob') is None:
    print('没有 sc_blob，先安装一次…')
    exec(open(BASE_ + 'blob_setup.py', encoding='utf-8').read())
_px = _p.op('sc_blob_pixel')
if _px is not None:
    _px.text = open(BASE_ + 'blob_shader.glsl', encoding='utf-8').read()
_b = _p.op('sc_blob')
if _b.par.vec1valuez.eval() < 0.01:
    _b.par.vec1valuex, _b.par.vec1valuey, _b.par.vec1valuez = 0.4, 0.4, 1.6
_ex = _p.op('sc_exec')
if _ex is None:
    print('没有 sc_exec：请先运行 suitcase_all.py')
else:
    _ex.store('force', 'invade')
    run("""
_p = op('/project1')
_b = _p.op('sc_blob')
_s = (_p.op('sc_exec').fetch('s', None) or {})
_cx, _cy = _b.par.vec1valuex.eval(), _b.par.vec1valuey.eval()
print('--- 云朵检查（入侵约 2.5 秒后）---')
print('sc_exec: 阶段', _s.get('phase'), '入侵程度', round(_s.get('inv', 0), 2), '(应该接近 1)')
print('sc_blob uB =', [round(getattr(_b.par, 'vec0value' + a).eval(), 3) for a in 'xyzw'], '(最后一个数字应该接近 1)')
print('云朵中心点的画面 (r,g,b,a) =', [round(v, 2) for v in _b.sample(x=int(_cx * 1920), y=int(_cy * 1080))], '(最后一个 a 大于 0.3 就说明着色器画出云朵了)')
print('着色器错误:', repr(_b.errors()), repr(_b.warnings()))
for _c in op('/project1/kantanMapper/project/allShapes').children:
    if _c.name == 'item4':
        _v = _c.op('parameters').par.Texture.eval()
        print('item4 纹理:', str(getattr(_v, 'path', _v)), '| 显示:', bool(_c.par.render.eval()))
""", delayFrames=150)
