# 回退 book_setup.py：「翻页书」的纹理换回原来的，删掉 sc_book（没出问题别运行）
p = op('/project1')
prev = p.fetch('sc_prev_book', None)
if prev:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == prev[0]:
            c.op('parameters').par.Texture = prev[1]
for n in ('sc_book',):
    if p.op(n) is not None:
        p.op(n).destroy()
print('已回退')
