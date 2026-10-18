# 在 TD 的 Textport 里运行（只读）：把 Kantan 的键盘快捷键程序复制到 td_live/kantan_keys.txt
k = op('/project1/kantanMapper')
txt = ''
for path in ('ui/renderpick/Keyboard', 'project/Selector', 'ui/renderpick/keyboardin1_callbacks'):
    o = k.op(path)
    if o is None:
        txt += '\n##### ' + path + ' NOT FOUND #####\n'
        continue
    try:
        body = o.text
    except Exception as e:
        body = 'error ' + repr(e)[:80]
    txt += '\n\n##### ' + path + ' #####\n' + str(body)
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/kantan_keys.txt', 'w', encoding='utf-8') as f:
    f.write(txt)
print('kantan keys written, chars:', len(txt))
