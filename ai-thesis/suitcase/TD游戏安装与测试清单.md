# TD 游戏：安装与测试清单

游戏 = 盖子上一个"乱的"房间（7 天 7 张），手 = 手电筒，找到光点后拍手收紧，再按琴键讲出 1~4 句话（白键 = 屋子里的声音，黑键 = 她的声音）。

## 装之前
1. 确认 TD 里这些都在：`MediaPipe`（手识别）、`gz_exec`（琴键信号）、`clap_in`（麦克风）、`sc_sub_txt` 和 `sc_sub`（右墙字幕）。
2. 在 Kantan 的空白处点一下，取消所有形状的选中。
3. 想先备份就 Cmd+S 存一下 TD 工程。

## 安装（Textport，Option+T）
```
exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase/game_td_setup.py', encoding='utf-8').read())
```
正常打印：`OK: 盖子 item5 宽高比 1.88 已换成游戏画面 sc_gamelid；右墙字幕改由游戏写`
出现"着色器有错"或红字：把那行发给 Claude。

## 先不用手测试
- 假装手在盖子中间：`op('/project1/sc_game_exec').store('hand',(0.5,0.5))`
- 让光点一直显出来：`op('/project1/sc_game_exec').store('show_dot',True)`
- 直接找到当天光点：`op('/project1/sc_game_exec').store('find',True)`
- 假装拍手：`op('/project1/sc_game_exec').store('clap',True)`
- 假装按白键（0~35）：`op('/project1/sc_game_exec').store('key',5)`
- 假装按黑键（'b0'~'b24'）：`op('/project1/sc_game_exec').store('key','b3')`
- 看当前状态：`op('/project1/sc_game_exec').store('status',True)`

## 用真的手
- 手方向反了：`op('/project1/sc_game_exec').store('cfg', {'flip_x': True})`（上下反了用 `'flip_y': True`，可以一起写）
- 手电筒大小：`{'flash_r': 0.3}`；房间有多乱：`{'glitch': 0.8}`；手的移动范围：`{'hand_x': (0.2, 0.8), 'hand_y': (0.2, 0.8)}`
- 拍手不灵：先在安静的房间拍一下；不灵告诉 Claude 房间里拍手大概多响。

## 退出
```
exec(open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase/game_td_undo.py', encoding='utf-8').read())
```
盖子换回原来的卧室，字幕引擎恢复（从头开始）。

## 更新句子后
改了 `game_exec_code.py`（或 `琴键对应的句子.md` 对应的内容）后，**重新运行一次 game_td_setup.py** 即可，只更新代码，不重复建节点。

## 已知限制
- 右墙句子是一整块文字，老句子不会变暗。
- 房间换天时直接换，没有渐变。
- 钢琴声来自 GarageBand；游戏只加了 found / bell / bell_stuck 三个小音效。
- 手的上下方向我是按原来空气钢琴的代码推断的，未在真机验证。
