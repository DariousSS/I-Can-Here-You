# 在 TD 的 Textport 里运行：把城堡三块箱子的纹理，分别指给"巨大拼脸"的三块（顶上小方块 / 中间宽长方形 / 下面大方块）
# 默认按名字：顶 Rectangle14、中 Rectangle4、下 Rectangle5（和 audio_fx.json 里的 giant_names 一致）。名字不对就改下面的 NAMES 再运行。
import json
NAMES = None
try:
    cfg_names = json.load(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/audio_fx.json', encoding='utf-8')).get('giant_names')
except Exception:
    cfg_names = None
names = NAMES or cfg_names or ['Rectangle14', 'Rectangle4', 'Rectangle5']
keys = ('top', 'mid', 'bot')
if op('/project1/castle_pc_top') is None:
    print('找不到 castle_pc_top，请先重新运行 gaze_setup.py 安装')
else:
    done = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is None or not hasattr(p.par, 'Texture'):
            continue
        nm = str(p.par.Name.eval())
        if nm in names:
            k = keys[names.index(nm)]
            p.par.Texture = '/project1/castle_pc_' + k
            p.par.Showtexture = True
            done.append(nm + ' -> castle_pc_' + k)
    print('已指派:', done)
    if len(done) != 3:
        print('没有找到全部 3 个形状，名字应为', names, '；请在 Kantan 里确认名字，或改本脚本里的 NAMES')
