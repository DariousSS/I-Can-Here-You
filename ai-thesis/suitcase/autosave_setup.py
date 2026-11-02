# 在 TD 的 Textport 里运行：建一个 Execute DAT（sc_autosave），每隔几分钟自动把工程存一次。
# 手在摄像头前时不存（存盘会让画面顿一下）；想关掉：op('/project1/sc_autosave').par.active = False
p = op('/project1')
ex = p.op('sc_autosave') or p.create(executeDAT, 'sc_autosave')
ex.nodeX, ex.nodeY = 2200, -4300
ex.text = '''import time

EVERY = 300.0          # 每隔多少秒存一次

def onFrameEnd(frame):
    now = time.time()
    last = me.fetch('last', None)
    if last is None:
        me.store('last', now)
        return
    if now - last < EVERY:
        return
    g = op('/project1/sc_game_exec').fetch('G', None) if op('/project1/sc_game_exec') is not None else None
    if g is not None and now - g.get('last_seen', 0.0) < 3.0:
        return                       # 手刚出现过，晚点再存
    me.store('last', now)
    try:
        project.save()
        print('sc_autosave：已自动保存', time.strftime('%H:%M:%S'))
    except Exception as e:
        print('sc_autosave：保存失败', repr(e)[:100])
'''
ex.par.framestart = False
ex.par.frameend = True
ex.par.active = True
print('OK: sc_autosave 已建好，每 5 分钟自动保存一次')
