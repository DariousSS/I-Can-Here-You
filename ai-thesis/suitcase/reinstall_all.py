# 在 TD 的 Textport 里运行：换了新琴（Impact LX61+）之后，一次把整套重装并对好纹理。需要几十秒，运行完会打印各步结果。
# 运行前：先在 Kantan 画布空白处点一下，取消所有形状的选中
B_ = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/'
for f_ in ('code/td_scripts/gaze_setup.py', 'suitcase/suitcase_all.py', 'suitcase/fix_textures.py', 'suitcase/subtitle_setup.py'):
    print('=== 运行', f_)
    exec(open(B_ + f_, encoding='utf-8').read())
print('=== 全部完成。按 Cmd+S 保存。然后按住钢琴中间的 do，运行下面这行看 TD 有没有收到：')
print("print({k: v for k, v in op('/project1/gz_exec').fetch('st')['midi'].items() if k.startswith('ch1n') and v > 0})")
