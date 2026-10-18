# 在 TD 的 Textport 里运行（只读）：城堡画面链路的现状 -> td_live/castle_probe.txt
lines = []
p = op('/project1')
for n in ('sw_dummy',):
    pass
for n in ('gz_switch', 'castle_tile', 'castle_mix', 'castle_xf', 'gz_attn'):
    o = p.op(n)
    if o is None:
        lines.append(n + ': NOT FOUND')
        continue
    s = n + ': type=' + str(o.type) + ' size=' + str(o.width) + 'x' + str(o.height)
    try:
        s += ' inputs=' + str([(i.name if i is not None else None) for i in o.inputs])
    except Exception:
        pass
    lines.append(s)
for n, names in (('castle_tile', ('sx', 'sy', 'rotate', 'extend', 'outputresolution', 'resolutionw', 'resolutionh')),
                 ('castle_mix', ('cross',)), ('castle_xf', ('cross',)), ('gz_tile', ('sx', 'sy', 'extend'))):
    o = p.op(n)
    if o is None:
        continue
    d = {}
    for nm in names:
        try:
            d[nm] = getattr(o.par, nm).eval()
        except Exception as e:
            d[nm] = 'ERR'
    lines.append(n + ' pars: ' + str(d))
try:
    a = p.op('castle_tile').numpyArray()
    lines.append('castle_tile mean rgb: ' + str([round(float(a[:, :, i].mean()), 3) for i in range(3)]))
    a = p.op('castle_xf').numpyArray()
    lines.append('castle_xf mean rgb: ' + str([round(float(a[:, :, i].mean()), 3) for i in range(3)]))
except Exception as e:
    lines.append('numpy error ' + repr(e)[:100])
try:
    st = p.op('gz_exec').fetch('st', {})
    lines.append('scene=' + str(st.get('scene')) + ' xa=' + str(st.get('xa')) + ' cm=' + str(st.get('cm')) + ' ctile_s=' + str(st.get('ctile_s')) + ' tiles_cur=' + str(st.get('tiles_cur')))
    txt = p.op('gz_exec').text
    lines.append('exec has castle_tiles_min: ' + str('castle_tiles_min' in txt) + ' | has castle_mix: ' + str('castle_mix' in txt) + ' | has scene_hold: ' + str('scene_hold' in txt))
except Exception as e:
    lines.append('gz_exec read error ' + repr(e)[:100])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/castle_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('castle probe written')
