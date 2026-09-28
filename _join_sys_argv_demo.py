# -*- coding: utf-8 -*-
"""sys.argv 是怎么变成"一句问题"的 —— 分三步看清楚。

三条命令各跑一次，比着看输出：
    python _join_sys_argv_demo.py
    python _join_sys_argv_demo.py "闭包是什么"
    python _join_sys_argv_demo.py 闭包 是什么
"""

import sys

print("=" * 50)
print("第 1 步：sys.argv 这个列表里到底有几个东西")
print(f"    sys.argv       = {sys.argv}")
print(f"    len(sys.argv)  = {len(sys.argv)}")
for 序号, 词 in enumerate(sys.argv):
    print(f"        第 {序号} 个 → 「{词}」")
print("    ** 第 0 个永远是脚本自己的名字，它不是问题的一部分。")

print()
print("第 2 步：切掉第 0 个，剩下的才是问题")
剩余 = sys.argv[1:]
print(f"    sys.argv[1:]      = {剩余}")
print(f"    len(sys.argv[1:]) = {len(剩余)}")
if len(sys.argv) > 1:
    print("    → 大于 0，说明带了问题 → 走命令行分支")
else:
    print("    → 等于 0，说明没带问题 → 进交互模式")

print()
print("第 3 步：把剩下的词用空格串成一根")
if 剩余:
    print(f'    " ".join({剩余})   = 「{" ".join(剩余)}」')
    print(f'    "".join({剩余})     = 「{"".join(剩余)}」')
    print(f'    "-".join({剩余})    = 「{"-".join(剩余)}」')
    print("    ** 引号里那个字符就是绳子，它被塞进每两颗珠子中间。")
else:
    print("    （这次没带词，没得串 —— 换一条带问题的命令再跑一次）")
print("=" * 50)
