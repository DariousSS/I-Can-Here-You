# 在 TD 的 Textport 里运行：一键整理 /project1 里【所有】节点（你自己连的和我装的）。
# 做法：1) 先把我装的节点按功能分成几组并涂色；你自己连的节点按"连在一起的一团"分组；
#       2) 每一组内部，按连线的流向从左到右排（信号从哪来、到哪去），一列放不下就分成几列；
#       3) 各组再一块一块地排开，组与组之间留空隙。
# 只改位置和颜色，不改任何连线和功能。运行前建议先 Cmd+S 保存一次。排完在网络窗口里点空白处，按 H 键看全貌。
p = op('/project1')

OURS = [
    ('输入与目光', (0.35, 0.50, 0.80), ['gz_out', 'gz_heat', 'gz_ai', 'gz_attn', 'gz_kb', 'gz_exec', 'clap_in']),
    ('画面与场景', (0.30, 0.65, 0.55), ['gz_switch', 'gz_tile', 'gz_fit', 'gz_mode', 'gz_xfade', 'gz_xfade2', 'gz_over', 'gz_final', 'gz_win', 'crowd_bg', 'crowd_comp'] + ['cf' + str(i) for i in range(20)]),
    ('城堡纹理', (0.85, 0.65, 0.30), ['castle_tile', 'castle_mix', 'castle_pre', 'castle_xf', 'stack_img']),
    ('海洋球', (0.90, 0.50, 0.60), ['ball_img', 'ball_fit', 'ball_tf', 'castle_ball_img', 'castle_ball_fit', 'castle_ball_tf']),
    ('投影映射', (0.60, 0.40, 0.80), ['kantanMapper', 'map_sel', 'poke_fx', 'poke_fx_pixel', 'map_fit']),
    ('木头手', (0.75, 0.55, 0.30), ['hand_img', 'hand_out', 'hand_fit']),
    ('木偶', (0.55, 0.70, 0.35), ['puppet_img', 'puppet_tf', 'hand_img_r', 'pL_tf', 'pR_tf', 'string_img', 'pstr1', 'pstr2', 'pstr3', 'pstr4', 'pc1', 'pc2', 'pc3', 'pc4', 'pc5', 'pc6', 'scene_out']),
    ('爆开的脸', (0.85, 0.40, 0.40), ['blank_small'] + [pre + str(i) for i in range(12) for pre in ('burst_img', 'burst_tf', 'burst_ov')] + ['burst_fade', 'burst_fit', 'burst_over']),
    ('天使', (0.85, 0.85, 0.90), ['angel_body_img', 'angel_pupil_img', 'blank_img', 'ang1_body', 'ang1_pupil', 'ang1_comp', 'ang1_fade', 'ang_chain1', 'ang2_body', 'ang2_pupil', 'ang2_comp', 'ang2_fade', 'ang_chain2', 'ang3_body', 'ang3_pupil', 'ang3_comp', 'ang3_fade', 'scene_all']),
    ('面具', (0.90, 0.80, 0.95), ['blank_sq', 'mask_std_img', 'mask_oval_img', 'mask_live_tf_in', 'mask_live_tf', 'mask_rand_tf_in', 'mask_rand_tf', 'mask_rand_tf_L_in', 'mask_rand_tf_L', 'mask_L', 'mask_R', 'castle_tri']),
    ('声音', (0.45, 0.45, 0.45), ['midiin1', 'air_note', 'air_out', 'snd_in', 'snd_gain', 'snd_clip', 'snd_vol', 'snd_out']),
]
DX, DY = 260, 130        # 列间距、行间距
MAXROW = 8               # 一列最多放几个，放不下就再开一列
GAP = 360                # 组与组之间的空隙
ROW_W = 5200             # 一排组最多多宽，超过就换行

allops = list(p.children)
by_name = {o.name: o for o in allops}
owned = {}
for gi, (title, color, names) in enumerate(OURS):
    for n in names:
        if n in by_name:
            owned[n] = gi


def inputs_of(o):
    out = []
    try:
        for i in o.inputs:
            if i is not None and i.name in by_name and i.parent().path == p.path:
                out.append(i.name)
    except Exception:
        pass
    return out


def components(names):
    """names 里的节点，按"连在一起"分成若干团（只看这些节点之间的连线）。"""
    names = set(names)
    adj = {n: set() for n in names}
    for n in names:
        for pn in inputs_of(by_name[n]):
            if pn in names:
                adj[n].add(pn)
                adj[pn].add(n)
    seen, comps = set(), []
    for n in sorted(names):
        if n in seen:
            continue
        stack, comp = [n], []
        seen.add(n)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(sorted(comp))
    return comps


def layout_cluster(names):
    """按连线流向排：返回 ({名字: (x, y)}, 宽, 高)，坐标相对这一组的左上角，y 向下为正。"""
    nameset = set(names)
    preds = {n: [q for q in inputs_of(by_name[n]) if q in nameset] for n in names}
    layer = {n: 0 for n in names}
    for _ in range(len(names)):
        changed = False
        for n in names:
            for q in preds[n]:
                if layer[q] + 1 > layer[n] and layer[q] + 1 < len(names):
                    layer[n] = layer[q] + 1
                    changed = True
        if not changed:
            break
    layers = {}
    for n in names:
        layers.setdefault(layer[n], []).append(n)
    order = {}
    for L in sorted(layers):
        layers[L].sort()
        for i, n in enumerate(layers[L]):
            order[n] = i
    for _ in range(3):                                           # 几遍"重心"排序，减少连线交叉
        for L in sorted(layers):
            if L == 0:
                continue
            def bary(n):
                ps = [order[q] for q in preds[n] if q in order]
                return sum(ps) / len(ps) if ps else order[n]
            layers[L].sort(key=lambda n: (bary(n), n))
            for i, n in enumerate(layers[L]):
                order[n] = i
    pos = {}
    col = 0
    maxrows = 1
    for L in sorted(layers):
        items = layers[L]
        for k in range(0, len(items), MAXROW):
            chunk = items[k:k + MAXROW]
            for r, n in enumerate(chunk):
                pos[n] = (col * DX, r * DY)
            maxrows = max(maxrows, len(chunk))
            col += 1
    return pos, max(col, 1) * DX, maxrows * DY


clusters = []      # (标题, 颜色或None, [名字])
for gi, (title, color, names) in enumerate(OURS):
    present = [n for n in names if n in by_name]
    if present:
        clusters.append((title, color, present))
rest = [o.name for o in allops if o.name not in owned]
comps = components(rest)
multi = [c for c in comps if len(c) > 1]
single = [c[0] for c in comps if len(c) == 1]
for i, c in enumerate(sorted(multi, key=lambda c: -len(c))):
    clusters.append(('你自己连的部分 ' + str(i + 1) + '（' + c[0] + ' 等）', None, c))
if single:
    clusters.append(('零散的节点', None, single))

# 放置：一块一块排开
x, y, rowh = 0, 0, 0
moved = 0
for title, color, names in clusters:
    pos, w, h = layout_cluster(names)
    if x > 0 and x + w > ROW_W:
        x = 0
        y -= rowh + GAP
        rowh = 0
    for n in names:
        o = by_name[n]
        px, py = pos[n]
        try:
            o.nodeX = x + px
            o.nodeY = y - py
            if color is not None:
                o.color = color
            moved += 1
        except Exception as e:
            print('移动失败:', n, repr(e)[:60])
    try:
        by_name[names[0]].comment = '【' + title + '】'
    except Exception:
        pass
    x += w + GAP
    rowh = max(rowh, h)
print('已整理', moved, '个节点，分成', len(clusters), '块（我装的 + 你自己连的）。在网络窗口里点空白处，按 H 键看全貌。')
