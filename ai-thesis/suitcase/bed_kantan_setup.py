# 在 TD 的 Textport 里运行：给被子那台投影仪新建一份"空白"的 Kantan Mapper（sc_bedkantan），和盒盖那份（kantanMapper）互不影响。
# 做的事：
#   1. 从 TD 自带的原版 kantanMapper.tox 载入一份新的，命名 sc_bedkantan（不碰原来的 kantanMapper）
#   2. 被子窗口（sc_win2）的画面改为显示 sc_bedkantan 的输出（sc_viewswitch 的第 0 路）
#   3. 打印它的输出大小；你在里面画被子/床/杂物的形状，每个形状的 Texture 选想投的画面
# 回退：运行 bed_kantan_undo.py。
TOX = '/Applications/TouchDesigner.app/Contents/Resources/tfs/Samples/Palette/Mapping/kantanMapper.tox'
p = op('/project1')
if p.op('sc_bedkantan') is not None:
    print('sc_bedkantan 已经存在，没有重复创建')
else:
    k = p.loadTox(TOX)
    k.name = 'sc_bedkantan'
    k.nodeX, k.nodeY = 2600, -4300
    print('OK: 已新建 /project1/' + k.name)
k = p.op('sc_bedkantan')
if k is not None:
    out = k.op('out1')
    sv = p.op('sc_viewswitch')
    if out is not None and sv is not None:
        sv.inputConnectors[0].connect(out)
        print('OK: 被子窗口现在显示 sc_bedkantan 的输出（你在里面画的东西会出现在被子投影仪上）')
    if out is not None:
        print('sc_bedkantan 输出大小：', out.width, 'x', out.height, '（被子投影仪是 1920x1200）')
    print('下一步：k = op("/project1/sc_bedkantan"); k.par.Open.pulse()  # 打开编辑窗口')
