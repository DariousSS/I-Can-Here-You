# 在 TD 的 Textport 里运行：撤销 scribble_setup.py（删掉 sk_ 开头的节点，Kantan 里「线条区域」的纹理不会自动清，需要的话自己在 Kantan 里清掉）。
p = op('/project1')
for nm in ('sk_exec', 'sk_out', 'sk_bg', 'sk_fb', 'sk_draw', 'sk_init'):
    o = p.op(nm)
    if o is not None:
        o.destroy()
for key in ('sk_st', 'sk_on', 'sk_half', 'sk_width', 'sk_flipx', 'sk_flipy', 'sk_demo'):
    try:
        p.unstore(key)
    except Exception:
        pass
print('已撤销：线条效果已删除。')
