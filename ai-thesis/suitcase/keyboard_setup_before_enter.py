# 在 TD 的 Textport 里运行：用电脑键盘临时代替钢琴。
# 白键（36 个）：数字 1234567890，然后字母 qwertyuiopasdfghjklzxcvbnm（小写，按顺序 = 钢琴从左到右的白键）
# 黑键（25 个）：按住 Shift 再按字母 Q W E R T Y U I O P A S D F G H J K L Z X C V B N（按顺序 = 钢琴从左到右的黑键）
# 空格键 = 开始（待机/封面时按空格，游戏规则出现）；空格不会当琴键用。
# 注意：要先点一下 TD 的窗口（让它在最前面）键盘才有用。
KEYS = '1234567890qwertyuiopasdfghjklzxcvbnm'
BKEYS = 'QWERTYUIOPASDFGHJKLZXCVBN'
p = op('/project1')
cb = p.op('sc_kb_cb') or p.create(textDAT, 'sc_kb_cb')
cb.text = (
    "KEYS = '" + KEYS + "'\n"
    "BKEYS = '" + BKEYS + "'\n"
    "def onKey(dat, key, character, *a):\n"
    "    try:\n"
    "        st = a[9] if len(a) > 9 else True\n"
    "        if not st:\n"
    "            return\n"
    "        if op('/project1/sc_game_exec') is not None and op('/project1/sc_game_exec').fetch('kbdebug', False):\n"
    "            print('键盘：key=%r character=%r' % (key, character))\n"
    "        if character == '\\\\':\n"
    "            for nm in ('sc_perfswitch', 'sc_viewswitch'):\n"
    "                sw = op('/project1/' + nm)\n"
    "                if sw is not None:\n"
    "                    sw.par.index = 1 - int(sw.par.index.eval())\n"
    "            return\n"
    "        g = op('/project1/sc_game_exec')\n"
    "        if g is None:\n"
    "            return\n"
    "        if character == ' ' or key == 'space':\n"
    "            g.store('door_open', True)\n"
    "            return\n"
    "        if not character or len(character) != 1:\n"
    "            return\n"
    "        if character in BKEYS:\n"
    "            g.store('key', 'b' + str(BKEYS.index(character)))\n"
    "        elif character in KEYS:\n"
    "            g.store('key', str(KEYS.index(character)))\n"
    "    except Exception as e:\n"
    "        print('sc_kb_cb 出错：', repr(e)[:100])\n"
    "    return\n"
)
cb.nodeX, cb.nodeY = 2100, -3900
kb = p.op('sc_kb') or p.create(keyboardinDAT, 'sc_kb')
kb.nodeX, kb.nodeY = 1900, -3900
ok = False
for nm in ('callbacks', 'callbackdat', 'callbackDAT'):
    if hasattr(kb.par, nm):
        setattr(kb.par, nm, cb)
        ok = True
        break
if hasattr(kb.par, 'active'):
    kb.par.active = True
if ok:
    print('OK: 键盘已接好。点一下 TD 窗口，先挥手找到光点，再按数字/字母键（白键），Shift+字母是黑键')
else:
    print('没找到回调参数，请把下面这行发给我：', [x.name for x in kb.pars()][:40])
