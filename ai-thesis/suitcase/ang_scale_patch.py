# 在 TD 的 Textport 里运行：给 sc_exec 里"天使大小"那一行后面加一行，乘以放大倍数 ang_scale（存在 sc_game_exec 里，默认 1.6）。
# 调大小：op('/project1/sc_game_exec').store('ang_scale', 2.0)    还原：ang_scale_undo.py
ex = op('/project1/sc_exec')
old = "ag.par.vec1valuez = sw_ * (1.0 - a0_) + ANG_SIZE * (1.0 + 0.2 * a0_) * a0_"
add = "ag.par.vec1valuez = ag.par.vec1valuez.eval() * float(op('/project1/sc_game_exec').fetch('ang_scale', 1.6))   # ang_scale_patch"
if ex is None:
    print('找不到 sc_exec')
elif 'ang_scale_patch' in ex.text:
    print('已经打过补丁，没有重复')
elif old not in ex.text:
    print('在 sc_exec 里没找到天使大小那一行，没有改动。请把 sc_exec 里含 ag.par.vec1valuez 的那几行贴给我')
else:
    ex.text = ex.text.replace(old, old + '\n        ' + add)
    print('OK: 天使大小已乘以 ang_scale（默认 1.6）。调：op("/project1/sc_game_exec").store("ang_scale", 2.0)')
