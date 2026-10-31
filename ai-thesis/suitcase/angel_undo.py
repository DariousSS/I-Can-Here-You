# 在 TD 的 Textport 里运行：撤销天使，把 item4 的纹理改回云朵 sc_blob
c = None
for c_ in op('/project1/kantanMapper/project/allShapes').children:
    if c_.name == 'item4':
        c = c_
if c is not None:
    c.op('parameters').par.Texture = '/project1/sc_blob'
    print('OK: item4 已改回 sc_blob（节点 sc_left / sc_angel 留着不影响，不想要可在 TD 里删掉）')
