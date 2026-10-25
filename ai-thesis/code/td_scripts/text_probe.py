# 在 TD 的 Textport 里运行：查"偏离度数字"那个 Text TOP 有哪些参数，帮我对一下参数名（只读）
t = op('/project1/dev_txt_L')
if t is None:
    print('找不到 dev_txt_L，请先重新运行 gaze_setup.py 安装')
else:
    names = [q.name for q in t.pars() if any(k in q.name.lower() for k in ('font', 'align', 'bg', 'text', 'res'))]
    print('Text TOP 参数:', names)
    l = op('/project1/dev_L')
    print('Level TOP 参数里带 opacity 的:', [q.name for q in l.pars() if 'opac' in q.name.lower()] if l else '没有 dev_L')
