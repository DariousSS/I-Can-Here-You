# 在 TD 的 Textport 里运行（只读）：水波特效（poke_fx）的现状 -> td_live/poke_probe.txt
lines = []
p = op('/project1')
for n in ('map_sel', 'poke_fx', 'map_fit', 'gz_win', 'poke_fx_pixel'):
    o = p.op(n)
    if o is None:
        lines.append(n + ': NOT FOUND')
        continue
    s = n + ': ' + str(o.type)
    try:
        s += ' size=' + str(o.width) + 'x' + str(o.height)
    except Exception:
        pass
    try:
        s += ' inputs=' + str([(i.name if i is not None else None) for i in o.inputs])
    except Exception:
        pass
    lines.append(s)
fx = p.op('poke_fx')
if fx is not None:
    try:
        lines.append('poke_fx errors: ' + repr(str(fx.errors())))
        lines.append('poke_fx warnings: ' + repr(str(fx.warnings())))
        lines.append('uniform uPoke = ' + str((fx.par.vec0name.eval(), fx.par.vec0valuex.eval(), fx.par.vec0valuey.eval(), fx.par.vec0valuez.eval(), fx.par.vec0valuew.eval())))
        d = fx.par.pixeldat.eval()
        lines.append('pixel shader dat: ' + (d.path + ' length ' + str(len(d.text)) + ' | has uPoke: ' + str('uPoke' in d.text) if d is not None else 'None'))
    except Exception as e:
        lines.append('fx read error ' + repr(e)[:120])
try:
    lines.append('gz_win.winop = ' + str(p.op('gz_win').par.winop.eval()))
except Exception as e:
    lines.append('win error ' + repr(e)[:80])
try:
    st = p.op('gz_exec').fetch('st', {})
    import time as _t
    pt = st.get('poke_time')
    lines.append('poke_time age(s)=' + (str(round(_t.time() - pt, 1)) if pt else 'None') + ' poke_P=' + str(st.get('poke_P')) + ' hand_t0=' + str(st.get('hand_t0')) + ' fx_key=' + str(st.get('fx_key')) + ' pokefx_err=' + str(st.get('pokefx_err')))
    lines.append('exec has _update_poke_fx: ' + str('_update_poke_fx' in p.op('gz_exec').text))
    c = st.get('fx_cfg') or {}
    lines.append('cfg poke_fx_on=' + str(c.get('poke_fx_on')) + ' amp=' + str(c.get('poke_fx_amp')) + ' mapping_on=' + str(c.get('mapping_on')))
except Exception as e:
    lines.append('gz_exec read error ' + repr(e)[:100])
for path in ('/project1/map_sel', '/project1/poke_fx', '/project1/map_fit'):
    try:
        a = op(path).numpyArray()
        lines.append(path + ' mean rgba=' + str([round(float(a[:, :, i].mean()), 4) for i in range(4)]))
    except Exception as e:
        lines.append(path + ' numpy error ' + repr(e)[:80])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/poke_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('poke probe written')
