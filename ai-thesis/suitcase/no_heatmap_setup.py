# 在 TD 的 Textport 里运行：去掉"按钢琴黑键 / V 键时出现的热力图"，万花筒里一直是脸。
# 做的事：改 gz_exec 里的 _update_view（原来：按住黑键 -> AI 注意力叠图，V 键 -> 目光热图；现在：一律是脸），并立刻把 gz_switch 切回脸。
# 万花筒、castle_xf、Kantan 里对应的形状都读同一条线，所以它们的纹理会一起变，不用再改别的。
# 撤销：运行 no_heatmap_undo.py
p = op('/project1')
ex = p.op('gz_exec')
if ex is None:
    raise Exception('找不到 gz_exec，请先运行 reinstall_all.py')
OLD = "    idx = 2 if held else (1 if st.get('view', 0) else 0)\n"
NEW = "    idx = 0                                   # 已去掉热力图\n"
t = ex.text
if NEW in t:
    print('已经去掉过了。')
elif OLD in t:
    ex.text = t.replace(OLD, NEW)
    print('OK：gz_exec 已改，按黑键 / V 键不再出现热力图。')
else:
    print('没找到要改的那一行（gz_exec 可能是别的版本）。请把下面这段发给我：')
    i = t.find('def _update_view')
    print(t[i:i + 600])
sw = p.op('gz_switch')
if sw is not None:
    sw.par.index = 0
    print('gz_switch 已切回脸（index = 0）。')
