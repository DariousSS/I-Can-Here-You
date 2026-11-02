# 在 TD 的 Textport 里运行：把"被子投影仪"和"盒盖投影仪"的屏幕号对调（重新插线后发现投反了就用它），并把两个窗口重开。
# 两个号都存在 audio_fx.json 里（win_display = 盒盖表演窗口，bed_display = 被子窗口），重开 TD 也不会丢。
import re
J = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/audio_fx.json'
txt = open(J, encoding='utf-8').read()
mw = re.search(r'("win_display"\s*:\s*)(\d+)', txt)
mb = re.search(r'("bed_display"\s*:\s*)(\d+)', txt)
if mw is None or mb is None:
    print('audio_fx.json 里找不到 win_display / bed_display，没有改动')
else:
    lid, bed = int(mw.group(2)), int(mb.group(2))
    if lid == bed:
        bed = 2 if lid == 1 else 1                      # 两个号一样说明配置乱了：把被子放到另一块
        new_lid, new_bed = lid, bed
    else:
        new_lid, new_bed = bed, lid                     # 对调
    t2 = txt[:mb.start(2)] + str(new_bed) + txt[mb.end(2):]
    mw2 = re.search(r'("win_display"\s*:\s*)(\d+)', t2)
    t2 = t2[:mw2.start(2)] + str(new_lid) + t2[mw2.end(2):]
    open(J, 'w', encoding='utf-8').write(t2)
    ge = op('/project1/sc_game_exec')
    cfg = dict(ge.fetch('cfg', None) or {})
    cfg.pop('bed_display', None)                        # 以后只认配置文件里的 bed_display
    ge.store('cfg', cfg)
    ge.store('bd_t', 0.0)
    w, g = op('/project1/sc_win2'), op('/project1/gz_win')
    w.par.winclose.pulse()
    g.par.winclose.pulse()
    w.par.display = new_bed
    g.par.display = new_lid
    run("op('/project1/sc_win2').par.winopen.pulse(); op('/project1/gz_win').par.winopen.pulse()", delayFrames=10)
    print('现在：被子 = 屏幕', new_bed, '| 盒盖 = 屏幕', new_lid, '（再跑一次这个脚本就对调回来）')
