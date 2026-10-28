# 在 TD 的 Textport 里运行：看棋盘为什么没出现（只读）
p = op('/project1')
for n in ('board_tex', 'board_screen', 'board_view', 'table_out', 'board_std1', 'board_std2'):
    print(n, '存在' if p.op(n) else '【缺！请重装 gaze_setup.py，并看有没有"棋盘没建成"】')
st = p.op('gz_exec').fetch('st', {})
print('当前场景 =', st.get('scene'), '| 棋盘混合 bd_mix =', st.get('bd_mix'), '| 棋盘错误 bd_err =', st.get('bd_err'), '/', st.get('bd_err2'))
w = p.op('gz_win')
print('输出窗口读的是:', w.par.winop.eval() if w else '找不到 gz_win', '（应该是 /project1/board_view）')
bt = p.op('board_tex')
if bt is not None:
    print('board_tex 着色器报错:', str(bt.errors() or '').strip()[:400] or '（没有）')
    try:
        print('board_tex 分辨率:', bt.width, 'x', bt.height, '| 第一格 vec1:', [round(bt.par['vec1value' + c].eval(), 2) for c in 'xyzw'])
    except Exception as e:
        print('读 vec1 失败:', repr(e)[:80])
bv = p.op('board_view')
if bv is not None:
    print('board_view cross =', round(bv.par.cross.eval(), 2), '（棋盘场景里应该接近 1）')
