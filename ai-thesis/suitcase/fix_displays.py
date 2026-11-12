# 在 TD 的 Textport 里运行：按分辨率自动认屏幕。1920x1080 的投影仪 = 盒盖（win_display），1920x1200 的投影仪 = 被子（bed_display）（实测原来认反了，已对调），不管插线顺序。
import re
J = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/audio_fx.json'
mons = [(i, m.width, m.height, m.left, m.top) for i, m in enumerate(monitors)]
print('TD 看到的屏幕：', mons)
lid = [i for i, w, h, l, t in mons if sorted((w, h)) == [1080, 1920]]
bed = [i for i, w, h, l, t in mons if sorted((w, h)) == [1200, 1920]]
if len(mons) < 3 or len(lid) != 1 or len(bed) != 1:
    print('认不出来：需要 3 块屏，其中一块 1920x1080（盒盖）、一块 1920x1200（被子）。请重新插线、确认系统设置里都是"扩展"，再运行。')
else:
    nl, nb = lid[0], bed[0]
    txt = open(J, encoding='utf-8').read()
    for k, v in (('win_display', nl), ('bed_display', nb)):
        txt = re.sub(r'("%s"\s*:\s*)\d+' % k, lambda m, v=v: m.group(1) + str(v), txt)
    open(J, 'w', encoding='utf-8').write(txt)
    ge = op('/project1/sc_game_exec')
    cfg = dict(ge.fetch('cfg', None) or {})
    cfg.pop('bed_display', None)
    ge.store('cfg', cfg)
    ge.store('bd_t', 0.0)
    w, g = op('/project1/sc_win2'), op('/project1/gz_win')
    w.par.winclose.pulse()
    g.par.winclose.pulse()
    w.par.display = nb
    for _w in (w, g):
        _w.par.alwaysontop = True          # 置顶：投影仪上盖过 Mac 菜单栏
    for _w, _i in ((w, nb), (g, nl)):                   # 窗口大小 = 对应投影仪的实际分辨率（不再是固定的 1920x1200）
        _w.par.winoffsetx = _w.par.winoffsety = 0
        _w.par.winw, _w.par.winh = monitors[_i].width, monitors[_i].height
    g.par.display = nl
    run("op('/project1/sc_win2').par.winopen.pulse(); op('/project1/gz_win').par.winopen.pulse()", delayFrames=10)
    print('OK：盒盖 = 屏幕', nl, '| 被子 = 屏幕', nb)
