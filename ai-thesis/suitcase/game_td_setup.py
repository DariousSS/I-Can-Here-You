# 在 TD 的 Textport 里运行：把"找光点 + 按琴键讲秘密"的游戏装到盖子上和右墙上。
# 只做三件事：①新建 sc_room / sc_gamelid / sc_game_exec（都是 sc_ 开头的新节点）；②把 Kantan 里盖子形状（item5）的纹理换成 sc_gamelid（旧纹理会记下来，game_td_undo.py 可还原）；③暂停原来的字幕引擎 sc_sub_exec，让游戏自己写右墙的字。
# 先在 Kantan 的空白处点一下，取消所有形状的选中。
LID = 'item5'
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
import os
p = op('/project1')
shp = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name == LID and c.op('parameters') is not None and hasattr(c.op('parameters').par, 'Texture'):
        shp = c
if shp is None:
    print('找不到盖子形状', LID)
elif p.op('sc_sub_txt') is None or p.op('sc_sub') is None:
    print('找不到右墙字幕的节点 sc_sub_txt / sc_sub：请先把字幕装好（subtitle_setup.py）')
else:
    pts = [(q.x, q.y) for q in shp.op('script1').points]
    asp = (max(q[0] for q in pts) - min(q[0] for q in pts)) / max(1.0, max(q[1] for q in pts) - min(q[1] for q in pts))
    room = p.op('sc_room') or p.create(moviefileinTOP, 'sc_room')
    room.par.file = BASE + '/game/room_day1.png'
    room.nodeX, room.nodeY = 1500, -3700
    gl = p.op('sc_gamelid') or p.create(glslTOP, 'sc_gamelid')
    gl.inputConnectors[0].connect(room)
    gl.par.outputresolution = 'custom'
    gl.par.resolutionw = 1024
    gl.par.resolutionh = 544
    try:
        gl.seq.vec.numBlocks = 3
    except Exception as e_:
        print('sc_gamelid 的 vec 序列设置失败：', repr(e_)[:80])
    gl.par.vec0name = 'uS'
    gl.par.vec1name = 'uF'
    gl.par.vec2name = 'uD'
    px = p.op('sc_gamelid_pixel')
    if px is not None:
        px.text = open(BASE + '/lid_game_shader.glsl', encoding='utf-8').read()
    gl.nodeX, gl.nodeY = 1700, -3700
    code = open(BASE + '/game_exec_code.py', encoding='utf-8').read().replace('__BASE__', BASE).replace('__ASPECT__', repr(round(asp, 4)))
    ex = p.op('sc_game_exec') or p.create(executeDAT, 'sc_game_exec')
    ex.text = code
    ex.store('G', None)
    ex.par.frameend = True
    ex.par.active = True
    try:
        ex.par.start = True          # 每次打开工程时运行 onStart（关掉多余的 MediaPipe 检测、回到封面）
    except Exception as e_:
        print('没设置成功「打开工程时运行」：', repr(e_)[:60])
    ex.nodeX, ex.nodeY = 1900, -3700
    old = p.op('sc_sub_exec')
    if old is not None:
        old.par.active = False
    par = shp.op('parameters').par
    cur = par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if cur != '/project1/sc_gamelid':
        p.store('sc_prev_game_lid', (shp.name, cur))
    par.Texture = '/project1/sc_gamelid'
    par.Showtexture = True
    shp.par.render = True
    er = str(gl.errors() or '').strip()
    print('OK: 盖子', LID, '宽高比', round(asp, 2), '已换成游戏画面 sc_gamelid；右墙字幕改由游戏写')
    if er:
        print('但盖子着色器有错：', er[:300])
    print('测试：op(\'/project1/sc_game_exec\').store(\'hand\',(0.5,0.5))  # 假装手在盖子正中间')
    # --- 光点数小牌子：Kantan 里名字叫 光点数 的那个形状，换成一个会显示"收集了几个"的文字 ---
    cs = None
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.op('parameters') is not None and hasattr(c.op('parameters').par, 'Name') and str(c.op('parameters').par.Name.eval()).strip() == '光点数':
            cs = c
    if cs is None:
        print('没找到名字叫「光点数」的形状，数字牌子没装（盖子和右墙不受影响）')
    else:
        ct = p.op('sc_count') or p.create(textTOP, 'sc_count')
        try:
            ct.par.outputresolution = 'custom'
            ct.par.resolutionw = 300
            ct.par.resolutionh = 400
            ct.par.fontsizex = 46
            ct.par.alignx = 'center'
            ct.par.aligny = 'center'
            ct.par.fontcolorr = 1.0
            ct.par.fontcolorg = 1.0
            ct.par.fontcolorb = 1.0
            ct.par.bgcolorr = 0.0
            ct.par.bgcolorg = 0.0
            ct.par.bgcolorb = 0.0
            ct.par.bgalpha = 0.0
        except Exception as e_:
            print('sc_count 的外观参数有的没设成功（不影响显示数字）：', repr(e_)[:100])
        ct.par.text = '0 / 7' + chr(10) + '. . . . . . .'
        ct.nodeX, ct.nodeY = 1500, -3900
        cp = cs.op('parameters').par
        cur_c = cp.Texture.eval()
        cur_c = str(getattr(cur_c, 'path', cur_c))
        if cur_c != '/project1/sc_count':
            p.store('sc_prev_count', (cs.name, cur_c))
        cp.Texture = '/project1/sc_count'
        cp.Showtexture = True
        cs.par.render = True
        print('OK: 「光点数」形状（', cs.name, '）现在显示 sc_count（收集了几个光点）')
    # --- 日历牌子：Kantan 里名字叫 日历 的形状，显示 MO TU WE.. 每周一行一天，和字幕分开 ---
    cc = None
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.op('parameters') is not None and hasattr(c.op('parameters').par, 'Name') and str(c.op('parameters').par.Name.eval()).strip() == '日历':
            cc = c
    if cc is None:
        print('没找到名字叫「日历」的形状，日历牌子没装（右墙字幕里不再有日历行）')
    else:
        cl = p.op('sc_cal') or p.create(textTOP, 'sc_cal')
        try:
            cl.par.outputresolution = 'custom'
            cl.par.resolutionw = 300
            cl.par.resolutionh = 400
            cl.par.fontsizex = 34
            cl.par.alignx = 'center'
            cl.par.aligny = 'center'
            cl.par.fontcolorr = 1.0
            cl.par.fontcolorg = 1.0
            cl.par.fontcolorb = 1.0
            cl.par.bgcolorr = 0.0
            cl.par.bgcolorg = 0.0
            cl.par.bgcolorb = 0.0
            cl.par.bgalpha = 0.0
        except Exception as e_:
            print('sc_cal 的外观参数有的没设成功：', repr(e_)[:100])
        cl.par.text = chr(10).join(['[MO]', '..', '..', '..', '..', '..', '..'])
        cl.nodeX, cl.nodeY = 1700, -3900
        cq = cc.op('parameters').par
        cur_k = cq.Texture.eval()
        cur_k = str(getattr(cur_k, 'path', cur_k))
        if cur_k != '/project1/sc_cal':
            p.store('sc_prev_cal', (cc.name, cur_k))
        cq.Texture = '/project1/sc_cal'
        cq.Showtexture = True
        cc.par.render = True
        print('OK: 「日历」形状（', cc.name, '）现在显示 sc_cal')
    # --- 封面牌子：Kantan 里名字叫 封面 的形状，开场介绍一直挂着，观众按一下琴键游戏才开始 ---
    cv_ = None
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.op('parameters') is not None and hasattr(c.op('parameters').par, 'Name') and str(c.op('parameters').par.Name.eval()).strip() == '封面':
            cv_ = c
    if cv_ is None:
        print('没找到名字叫「封面」的形状：开场介绍先显示在右墙。画好正方形后把它的 Name 改成 封面，再运行一次本脚本')
    else:
        ci = p.op('sc_intro') or p.create(textTOP, 'sc_intro')
        try:
            ci.par.outputresolution = 'custom'
            ci.par.resolutionw = 800
            ci.par.resolutionh = 800
            ci.par.fontsizex = 32
            ci.par.alignx = 'center'
            ci.par.aligny = 'center'
            ci.par.fontcolorr = 1.0
            ci.par.fontcolorg = 1.0
            ci.par.fontcolorb = 1.0
            ci.par.bgcolorr = 0.0
            ci.par.bgcolorg = 0.0
            ci.par.bgcolorb = 0.0
            ci.par.bgalpha = 0.0
        except Exception as e_:
            print('sc_intro 的外观参数有的没设成功：', repr(e_)[:100])
        ci.par.text = ' '
        ci.nodeX, ci.nodeY = 1900, -4100
        cz = cv_.op('parameters').par
        cur_z = cz.Texture.eval()
        cur_z = str(getattr(cur_z, 'path', cur_z))
        if cur_z != '/project1/sc_intro':
            p.store('sc_prev_intro', (cv_.name, cur_z))
        cz.Texture = '/project1/sc_intro'
        cz.Showtexture = True
        cv_.par.render = True
        print('OK: 「封面」形状（', cv_.name, '）现在显示开场介绍 sc_intro；观众按一下琴键游戏才开始')
