# 在 TD 的 Textport 里运行：触发一次面具，4 秒后（面具正亮着）量三角形有没有淡出、谁画在上面。结果打印在 Textport。
import json, time
BR = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'
with open(BR + '/mask_test.json', 'w', encoding='utf-8') as f_:
    json.dump({'t': time.time()}, f_)
LATER = r'''
p = op('/project1')
st = p.op('gz_exec').fetch('st', {})
M = st.get('mask', {})
print('[面具亮着时] 阶段=' + str(M.get('phase')) + ' 亮度=' + str(round(M.get('lv', 0), 2)) + ' 场景=' + str(st.get('scene')))
for n in ('mask_L', 'mask_R', 'castle_tri'):
    o = p.op(n)
    try:
        a = o.numpyArray()
        print('[面具亮着时]', n, 'cross=' + str(round(o.par.cross.eval(), 2)), '平均 rgba=' + str([round(float(a[:, :, i].mean()), 3) for i in range(4)]))
    except Exception as e:
        print(n, 'err', repr(e)[:60])
order = []
for i, c in enumerate(op('/project1/kantanMapper/project/allShapes').children):
    pr = c.op('parameters')
    if pr is not None and hasattr(pr.par, 'Name'):
        v = pr.par.Texture.eval()
        order.append(str(i) + ':' + str(pr.par.Name.eval()) + '(' + str(getattr(v, 'path', v)).split('/')[-1] + ')')
print('[形状顺序，后面的画在上面?]', ' | '.join(order))
'''
run(LATER, delayMilliSeconds=4000)
print('已触发面具，请不要动，4 秒后会打印结果（需要当前在万花筒场景）')
