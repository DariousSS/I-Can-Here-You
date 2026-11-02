# 还原 ang_scale_patch.py（没出问题别运行）
ex = op('/project1/sc_exec')
lines = [ln for ln in ex.text.split('\n') if 'ang_scale_patch' not in ln]
ex.text = '\n'.join(lines)
print('已还原 sc_exec')
