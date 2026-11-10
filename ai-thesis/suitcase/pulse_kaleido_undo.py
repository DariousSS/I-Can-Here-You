# 在 TD 的 Textport 里运行：撤销 pulse_kaleido_setup.py —— 把节点接回原来的 gz_tile / castle_tile，删掉新建的节点。
p = op('/project1')
done = p.fetch('pk_rewired', []) or []
for path, i, src_path in done:
    n, src = op(path), op(src_path)
    if n is not None and src is not None:
        try:
            n.inputConnectors[i].connect(src)
        except Exception as e:
            print('接回失败：', path, i, repr(e)[:80])
for nm in ('pk_exec', 'pk_warp_full', 'pk_warp_castle', 'arr_pk'):
    o = p.op(nm)
    if o is not None:
        o.destroy()
for key in ('pk_rewired', 'pk_st', 'pk_fake', 'pk_on', 'pk_gain', 'pk_base_secs'):
    try:
        p.unstore(key)
    except Exception:
        pass
print('已撤销：万花筒接回原来的节点。')
