d = op('/project1/gz_exec')
d.text = d.text.replace("    if op('sc_perfstage') is not None:\n        want = '/project1/sc_perfstage'\n", '', 1)
print('OK: gz_exec 已恢复原样')
