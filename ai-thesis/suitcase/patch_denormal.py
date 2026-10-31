# 在 TD 的 Textport 里运行：给正在运行的 sc_exec 打补丁（不用重装）。原因：inv 等数字衰减到 1e-323 这种极小值，写进参数后 TD 变成 1.8e308，左面具被冲成白色、拉扯条变成纯绿。
p = op('/project1')
ex = p.op('sc_exec')
old = "    s['last'] = now\n    force = me.fetch('force', None)\n"
new = "    s['last'] = now\n    for k_ in ('inv', 'snd', 'wl', 'wbl'):\n        if abs(s.get(k_, 0.0)) < 0.0005:\n            s[k_] = 0.0\n    force = me.fetch('force', None)\n"
if ex is None:
    print('找不到 sc_exec')
elif "for k_ in ('inv', 'snd', 'wl', 'wbl')" in ex.text:
    print('已经打过补丁了')
elif old not in ex.text:
    print('sc_exec 的代码和预期不一样，没有改动')
else:
    ex.text = ex.text.replace(old, new, 1)
    s = ex.fetch('s', None)
    if s:
        for k_ in ('inv', 'snd', 'wl', 'wbl'):
            if abs(s.get(k_, 0.0)) < 0.0005:
                s[k_] = 0.0
        ex.store('s', s)
    print('OK: sc_exec 已打补丁，左面具和拉扯条应该恢复正常')
