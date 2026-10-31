# 在 TD 的 Textport 里运行：给装置的 gz_exec 加两行——"有舞台 sc_perfstage 时，gz_win 显示舞台"。
# 原因：gz_exec 每约 1 秒会把 gz_win 改回 map_fit，我的舞台被覆盖。
# 撤销：运行 perf_patch_gzexec_undo.py
d = op('/project1/gz_exec')
MARK = "    if op('sc_perfstage') is not None:"
OLD = "    if str(w.par.winop.eval()) != want:\n        w.par.winop = want\n"
NEW = MARK + "\n        want = '/project1/sc_perfstage'\n" + OLD
t = d.text
if MARK in t:
    print('已经补过了，不用再补')
elif OLD not in t:
    print('gz_exec 里没找到要改的那段，没改任何东西（你的 gz_exec 代码和我看到的不一样）')
else:
    d.text = t.replace(OLD, NEW, 1)
    print('OK: gz_exec 已补丁。约 1 秒后 gz_win 会显示', '/project1/sc_perfstage', '| 当前：', op('/project1/gz_win').par.winop.eval())
