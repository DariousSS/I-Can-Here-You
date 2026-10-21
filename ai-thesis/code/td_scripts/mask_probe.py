# 在 TD 的 Textport 里运行：检查面具为什么没出现（只读，不改任何东西）
p = op('/project1')
print('--- 1. 节点装好了吗 ---')
for n in ('mask_L', 'mask_R', 'castle_tri', 'mask_rand_oval'):
    o = p.op(n)
    print(n, '存在' if o else '【缺！请重装 gaze_setup.py】', ('cross=' + str(round(o.par.cross.eval(), 2))) if o and hasattr(o.par, 'cross') else '')
print('--- 2. Kantan 里每个形状用的纹理 ---')
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        continue
    v = pr.par.Texture.eval()
    print(str(pr.par.Name.eval()), '->', str(getattr(v, 'path', v)).split('/')[-1], '显示=' + str(pr.par.Showtexture.eval()))
print('（应该有两个形状指向 mask_L、mask_R，两个小三角指向 castle_tri）')
print('--- 3. 面具调度状态 ---')
import time
st = p.op('gz_exec').fetch('st', {})
M = st.get('mask')
print('当前场景 =', st.get('scene'), '| 标准脸序列中 =', bool(st.get('std')))
if M:
    print('面具阶段 =', M.get('phase'), '| 亮度 =', round(M.get('lv', 0), 2), '| 下次出现还有', (round(M['next'] - time.time()) if M.get('next') else '?'), '秒')
else:
    print('面具调度还没有运行（gz_exec 里没有 mask 状态）：请重装 gaze_setup.py')
