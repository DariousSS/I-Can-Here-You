# 在 TD 的 Textport 里运行：把"按黑键 / V 键出现热力图"恢复回来。
p = op('/project1')
ex = p.op('gz_exec')
NEW = "    idx = 0                                   # 已去掉热力图\n"
OLD = "    idx = 2 if held else (1 if st.get('view', 0) else 0)\n"
if ex is not None and NEW in ex.text:
    ex.text = ex.text.replace(NEW, OLD)
    print('OK：热力图恢复了。')
else:
    print('没有需要恢复的（gz_exec 里没有被改过的那一行）。')
