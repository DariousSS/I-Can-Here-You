# 在 TD 的 Textport 里运行：给 Kantan 列表里的每个形状起一个看得懂的名字（只改显示用的 Name 参数，不影响画面）
# 之前列表里全显示 Freeform19，是因为每个形状的 Name 参数被刷成了同一个名字；这里把它们改回各不相同的名字
ROLE = {'item4': '万花筒半圆', 'item5': '盖子(卧室)', 'item18': '左面具(入侵时出现脸)', 'item19': '右脸(一直说话)'}
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Name'):
        continue
    n = pr.par.Name
    new = ROLE.get(c.name, c.name)
    print(c.name, '| 原名', n.eval(), '| 模式', n.mode, '| 表达式', n.expr)
    try:
        n.val = new
        n.mode = ParMode.CONSTANT
    except Exception as e:
        print('   改名失败:', e)
    print('   现在 ->', n.eval())
print('改完后在 Kantan 里随便点一下别的形状，列表就会刷新')
