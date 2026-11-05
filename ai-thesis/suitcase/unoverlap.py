# 在 TD 的 Textport 里运行：只把互相叠在一起的节点（包括名字叠在一起的）推开，别的不动。
# 只改节点位置，不改连线、参数、颜色、功能。没有重叠的节点一动不动。
# 运行前建议先 Cmd+S 保存一次（TD 会存成新版本，旧版本还在）。
p = op('/project1')
PAD = 24                 # 节点之间至少留的空隙
CHAR_W = 9.0             # 一个字母大约占多宽（名字比节点宽时，按名字算）

nodes = []
for o in p.children:
    try:
        if getattr(o, 'dock', None) is not None:        # 贴在别的节点下面的（比如 xxx_pixel）会跟着主人走，不管
            continue
        w = max(o.nodeWidth, CHAR_W * len(o.name) + 16)
        h = o.nodeHeight + 24                            # 名字在节点下方，多算一点高度
        nodes.append([o, o.nodeCenterX, o.nodeCenterY, w, h])
    except Exception:
        pass


def hit(a, b):
    return abs(a[1] - b[1]) < (a[3] + b[3]) / 2 + PAD and abs(a[2] - b[2]) < (a[4] + b[4]) / 2 + PAD


nodes.sort(key=lambda n: (-n[2], n[1]))                  # 从上到下、从左到右依次放
placed, moved = [], 0
for n in nodes:
    x0, y0 = n[1], n[2]
    tries = 0
    while tries < 200 and any(hit(n, q) for q in placed):
        # 先向右推一格，推了 12 格还不行就换到下一行再来
        n[1] += n[3] / 2 + PAD
        if tries % 12 == 11:
            n[1] = x0
            n[2] -= n[4] + PAD
        tries += 1
    if (n[1], n[2]) != (x0, y0):
        try:
            n[0].nodeCenterX, n[0].nodeCenterY = n[1], n[2]
            moved += 1
        except Exception as e:
            print('移动失败:', n[0].name, repr(e)[:60])
    placed.append(n)
print('检查了', len(nodes), '个节点，推开了', moved, '个。在网络窗口里点空白处，按 H 键看全貌。')
