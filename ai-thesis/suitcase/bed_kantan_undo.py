# 回退 bed_kantan_setup.py：被子窗口重新显示 sc_bedscene，并删掉 sc_bedkantan（会连同你在里面画的形状一起删掉，没出问题别运行）
p = op('/project1')
sv, bs = p.op('sc_viewswitch'), p.op('sc_bedscene')
if sv is not None and bs is not None:
    sv.inputConnectors[0].connect(bs)
k = p.op('sc_bedkantan')
if k is not None:
    k.destroy()
ge = op('/project1/sc_game_exec')
cfg = dict(ge.fetch('cfg', {}) or {})
cfg.pop('bed_flip', None)              # 恢复成默认（转 180 度）
ge.store('cfg', cfg)
for n in ('sc_bedkantan_rot', 'sc_bed_face', 'sc_bed_dot'):
    if p.op(n) is not None:
        p.op(n).destroy()
sl = p.op('sc_bedkantan_sel')
if sl is not None:
    sl.destroy()
print('已回退：被子窗口 = sc_bedscene，sc_bedkantan 已删除')
