# 在 TD 的 Textport 里运行（只读）：看左面具的 opacity 和拉扯的强度到底是被谁、设成了什么
p = op('/project1')
for nm, pn in (('sc_maskL', 'opacity'), ('sc_maskR', 'opacity'), ('sc_pull', 'vec1valuez'), ('sc_pull', 'vec1valuew')):
    t = p.op(nm)
    if t is None:
        print(nm, '没有这个节点')
        continue
    q = getattr(t.par, pn)
    print(nm, pn, '| 模式', q.mode, '| 值 val', q.val, '| 表达式', repr(q.expr), '| 绑定', repr(getattr(q, 'bindExpr', '')), '| eval', q.eval())
for nm in ('sc_exec', 'sc_sub_exec', 'sc_game_exec'):
    t = p.op(nm)
    print(nm, '| 开着' if (t is not None and t.par.active) else '| 关着/没有', '| 上次出错', None if t is None else t.fetch('last_err', ''))
print('maskL 现在的故事数据 inv =', (p.op('sc_exec').fetch('s', {}) or {}).get('inv'))
