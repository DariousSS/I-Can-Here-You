# 在 TD 的 Textport 里运行（只读）：把 Kantan Mapper 的程序文字复制到 td_live/kantan_src.txt
k = op('/project1/kantanMapper')
txt = ''
for nm in ('Projecter', 'docsHelper', 'projectJson'):
    o = k.op(nm)
    if o is None:
        continue
    try:
        body = o.text if hasattr(o, 'text') else ''
    except Exception as e:
        body = 'error ' + repr(e)[:80]
    txt += '\n\n##### ' + nm + ' (' + str(o.type) + ') #####\n' + str(body)
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/kantan_src.txt', 'w', encoding='utf-8') as f:
    f.write(txt)
print('kantan src written, chars:', len(txt))
