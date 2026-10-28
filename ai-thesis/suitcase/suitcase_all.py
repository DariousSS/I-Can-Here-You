# 在 TD 的 Textport 里运行：一键恢复/安装整套（云朵 + 盖子故障 + 面具），可以重复运行
BASE_ = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase/'
for f_ in ('blob_setup.py', 'pull_setup.py', 'suitcase_setup.py'):
    exec(open(BASE_ + f_, encoding='utf-8').read())
for c_ in op('/project1/kantanMapper/project/allShapes').children:
    if c_.name in ('item4', 'item5', 'item18', 'item19'):
        c_.par.render = True
print('全部装好。现在按 Cmd+S 保存！然后试：op(\'/project1/sc_exec\').store(\'force\',\'invade\')')
