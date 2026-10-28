# 在 TD 的 Textport 里运行：把"标准脸"那套旧形状的纹理换成全透明的 sc_black（不删除，可用 show_old_shapes.py 还原）
# 只留盖子 item5、左面具 item18、右边的脸（不在这个名单里的都不动）
OLD = ['item10', 'item11', 'item14', 'item15', 'item16', 'item17', 'item20', 'item21', 'item22']
p = op('/project1')
blk = p.op('sc_black') or p.create(constantTOP, 'sc_black')
try:
    blk.par.colorr = 0.0
    blk.par.colorg = 0.0
    blk.par.colorb = 0.0
    blk.par.alpha = 0.0
except Exception as e:
    print('sc_black 的颜色参数设置失败，请把这行发给我:', e, [x.name for x in blk.pars()][:20])
blk.nodeX, blk.nodeY = 1500, -2400
saved = p.fetch('sc_hidden', {})
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name in OLD and c.op('parameters') is not None:
        par = c.op('parameters').par
        cur = par.Texture.eval()
        cur = str(getattr(cur, 'path', cur))
        if cur != '/project1/sc_black':
            saved[c.name] = cur
        par.Texture = '/project1/sc_black'
        print(c.name, ':', cur, '-> sc_black')
p.store('sc_hidden', saved)
print('完成。右边的眼睛、多出来的万花筒应该消失了')
