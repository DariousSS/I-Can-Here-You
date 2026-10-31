# 在 TD 的 Textport 里运行：把每个 Kantan 形状的纹理对回去（按内部编号），并自动检查、必要时再改一遍。
# 运行前：先在 Kantan 画布的空白处点一下，取消所有形状的选中状态（Kantan 里选中多个形状时，改一个会同步改到所有选中的）。
WANT = {
    'item4':  'sc_left',    # 左边：天使叠在云朵上（没装天使就改回 sc_blob）
    'item5':  'sc_lid',     # 盖子（卧室）
    'item15': 'sc_pull',    # 整屏：入侵时的电视机故障拉扯
    'item18': 'sc_maskL',   # 左面具（入侵时出现脸）
    'item19': 'sc_maskR',   # 右脸（一直说话）
    'item23': 'sc_sub',     # 墙上的字幕
}
_g = op('/project1/sc_game_exec')
if _g is not None and _g.par.active:      # 游戏开着时，盖子用游戏画面
    WANT['item5'] = 'sc_gamelid'
BLACK = ['item10', 'item11', 'item14', 'item16', 'item17', 'item20', 'item21', 'item22']   # 旧形状 + 你命名为"床头柜"的 item14：全透明
SHOW = ['item4', 'item5', 'item15', 'item18', 'item19', 'item23']
for k_ in BLACK:
    WANT[k_] = 'sc_black'
p = op('/project1')
shapes = {}
for c_ in op('/project1/kantanMapper/project/allShapes').children:     # 「光点数」牌子：游戏开着时显示 sc_count，不要被改回透明
    if c_.op('parameters') is not None and hasattr(c_.op('parameters').par, 'Name') and str(c_.op('parameters').par.Name.eval()).strip() == '光点数' and p.op('sc_count') is not None:
        WANT[c_.name] = 'sc_count'
    if c_.op('parameters') is not None and hasattr(c_.op('parameters').par, 'Name') and str(c_.op('parameters').par.Name.eval()).strip() == '日历' and p.op('sc_cal') is not None:
        WANT[c_.name] = 'sc_cal'
    if c_.op('parameters') is not None and hasattr(c_.op('parameters').par, 'Name') and str(c_.op('parameters').par.Name.eval()).strip() == '封面' and p.op('sc_intro') is not None:
        WANT[c_.name] = 'sc_intro'
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.op('parameters') is not None and hasattr(c.op('parameters').par, 'Texture'):
        shapes[c.name] = c

def cur_tex(c):
    v = c.op('parameters').par.Texture.eval()
    return '' if v is None else str(getattr(v, 'path', v))

for rnd in range(4):
    bad = []
    for nm, tex in WANT.items():
        c = shapes.get(nm)
        if c is None:
            continue
        if cur_tex(c) != '/project1/' + tex:
            c.op('parameters').par.Texture = '/project1/' + tex
            bad.append(nm)
    if not bad:
        break
    print('第', rnd + 1, '轮改了:', bad)
for nm in SHOW:
    c = shapes.get(nm)
    if c is not None:
        c.op('parameters').par.Showtexture = True
        c.par.render = True
wrong = [nm for nm, tex in WANT.items() if nm in shapes and cur_tex(shapes[nm]) != '/project1/' + tex]
print('最后检查：', '全部正确' if not wrong else '还有不对的（可能是选中了多个形状，请先取消选中再运行一次）: ' + str(wrong))
# 刷新几个按形状位置算的参数：云朵的宽高比、拉扯的起止位置
def box(nm):
    pts = [(q.x, q.y) for q in shapes[nm].op('script1').points]
    x0, x1 = 960.0 + min(q[0] for q in pts), 960.0 + max(q[0] for q in pts)
    y0, y1 = 540.0 - max(q[1] for q in pts), 540.0 - min(q[1] for q in pts)
    return x0, y0, x1, y1
try:
    x0, y0, x1, y1 = box('item4')
    p.op('sc_blob').par.vec0valuez = (x1 - x0) / (y1 - y0)
    a = box('item19')
    b = box('item18')
    pl = p.op('sc_pull')
    pl.par.vec0valuex, pl.par.vec0valuey = (a[0] + a[2]) / 2.0 / 1920.0, 1.0 - (a[1] + a[3]) / 2.0 / 1080.0
    pl.par.vec0valuez, pl.par.vec0valuew = (b[0] + b[2]) / 2.0 / 1920.0, 1.0 - (b[1] + b[3]) / 2.0 / 1080.0
    pl.par.vec1valuex, pl.par.vec1valuey = (a[3] - a[1]) / 2.0 / 1080.0, (b[3] - b[1]) / 2.0 / 1080.0
    print('已刷新：云朵宽高比 %.2f，拉扯的起止位置' % ((x1 - x0) / (y1 - y0)))
except Exception as e:
    print('刷新云朵/拉扯参数失败（不影响纹理）:', repr(e)[:80])
