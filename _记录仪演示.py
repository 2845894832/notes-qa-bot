# -*- coding: utf-8 -*-
"""第 11 课 · 记录仪 —— 屏幕上看见的，关上终端就没了。

这个文件不花 API 钱：三问的数据是假的，为了先让你看清"记"和"不记"的差别。
等你自己改完 主程序.py，再跑真的体检拿真数。

四幕：
  幕一  只打印：跑完想算平均数？只能往上翻屏。
  幕二  写一行 JSON：一行一条，追加，不覆盖。
  幕三  读回来算数：平均轮数 / 工具总次数 / 拒答几题 / 中位耗时。
  幕四  为什么不用"拼字符串"。
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path

本次记录 = Path(__file__).with_name("_记录仪演示_本次.jsonl")

# 假装的三问：(问题, 轮数, 工具次数, 耗时秒, 是不是拒答)
假数据 = [
    ("闭包是什么",       2, 2, 3.1, False),
    ("9 月餐饮多少",     2, 1, 2.2, False),
    ("今天天气怎么样",   1, 1, 1.5, True),
]


def 演一遍(问题, 轮数, 工具, 秒, 拒答):
    """不管记不记，屏幕上都是这几行 —— 这是你现在就有的。"""
    print(f"===== 问：{问题} =====")
    print(f"  （转了 {轮数} 轮，用了 {工具} 次工具，{秒:.1f} 秒）")
    print("  答：……（内容省略）")
    print("-" * 46)


print("=" * 60)
print("幕一：只打印")
print("=" * 60)
for 一条 in 假数据:
    演一遍(*一条)

print()
print("  现在我问你：三问平均转了几轮？")
print("  屏幕往上翻还能数；一百问、一千问呢？关上终端呢？")
print("  屏幕是【一次性的】，它不替你记账。")


print()
print("=" * 60)
print("幕二：每一问往一个文件里追加一行 JSON")
print("=" * 60)

本次记录.write_text("", encoding="utf-8")   # 演示用：先清空，每次跑都从头来

for 问题, 轮数, 工具, 秒, 拒答 in 假数据:
    演一遍(问题, 轮数, 工具, 秒, 拒答)

    一行 = {
        "时间": datetime.now().isoformat(timespec="seconds"),
        "问题": 问题,
        "轮数": 轮数,
        "工具次数": 工具,
        "耗时秒": 秒,
        "拒答": 拒答,
    }
    with 本次记录.open("a", encoding="utf-8") as 文件:
        文件.write(json.dumps(一行, ensure_ascii=False) + "\n")

print()
print("  文件长这样（一行一条，不是一张表）：")
print("  " + "-" * 56)
for 行 in 本次记录.read_text(encoding="utf-8").splitlines():
    print("  " + 行)
print("  " + "-" * 56)


print()
print("=" * 60)
print("幕三：读回来，算四个数")
print("=" * 60)

记录们 = []
for 行 in 本次记录.read_text(encoding="utf-8").splitlines():
    if 行.strip():
        记录们.append(json.loads(行))     # 一行 → 一个 dict，不用切字符串

开始 = time.time()
print(f"  一共 {len(记录们)} 问")
print(f"  平均轮数   {sum(r['轮数'] for r in 记录们) / len(记录们):.2f}")
print(f"  工具总次数 {sum(r['工具次数'] for r in 记录们)}")
print(f"  拒答       {sum(1 for r in 记录们 if r['拒答'])} 题")
print(f"  耗时中位数 {statistics.median(r['耗时秒'] for r in 记录们):.2f} 秒")
print(f"  拒答率     {sum(1 for r in 记录们 if r['拒答']) / len(记录们):.0%}")
print()
print("  ★ 这四个数是从文件里算出来的，不是靠回忆 —— 换 100 问也是同样四行代码。")


print()
print("=" * 60)
print("幕四：如果当初是拼字符串记的呢")
print("=" * 60)

坏文件 = Path(__file__).with_name("_记录仪演示_坏写法.txt")
坏文件.write_text("", encoding="utf-8")
for 问题, 轮数, 工具, 秒, 拒答 in 假数据:
    一行字 = f"{问题} 转了{轮数}轮 工具{工具}次 {秒}秒 拒答={拒答}"
    with 坏文件.open("a", encoding="utf-8") as 文件:
        文件.write(一行字 + "\n")

print("  坏写法长这样：")
for 行 in 坏文件.read_text(encoding="utf-8").splitlines():
    print("    " + 行)
print()
print("  现在想算平均轮数：得先按空格切，再按「转」「轮」切，再转 int。")
print("  问题里只要带一个空格（「9 月餐饮多少」），整个切法就错位了。")
print()
print("  ★ 结论：记的时候多用一步 json.dumps，读的时候省一百步。")
print("     filename: " + 本次记录.name)
