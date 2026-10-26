# -*- coding: utf-8 -*-
"""第 12 课插问：iter_lines 是什么。

一句话：**响应体不是一次给你的，你问一次，它给你一行。**
`r.text` / `r.json()` 是"整箱到货"，`r.iter_lines()` 是"你伸手它才给你一行"。

两幕：
  幕一（不花钱）先看"生成器"是个什么手感 —— 用假数据
  幕二（花 1 次钱）真发一次，记下每一行到手的秒数，看它是不是陆续到的
"""

import json
import time

import requests

import 问模型

头 = {"Authorization": "Bearer " + 问模型.拿钥匙(), "Content-Type": "application/json"}


# ================================================================ 幕一
print("=" * 62)
print("幕一：生成器的手感 —— 你不问，它一动不动")
print("=" * 62)


def 假的服务器的流():
    """假装是网络那头：每被拿一次，才吐一行出来，并喊一声。"""
    for 行 in ["data: 第1行", "data: 第2行", "", "data: [DONE]"]:
        print(f"      （网络那头：我又发出了一行 {行!r}）")
        yield 行


流 = 假的服务器的流()
print("  刚从 iter_lines() 手里拿到的东西是：", type(流).__name__)
print("  它现在还没开始干活 —— 你不动它，网络那头也一动不动：")
print()
print("  伸手要第 1 次：")
print("    拿到 →", repr(next(流)))
print("  伸手要第 2 次：")
print("    拿到 →", repr(next(流)))
print("  伸手要第 3 次（空行也会有，它是分隔符）：")
print("    拿到 →", repr(next(流)))
print("  伸手要第 4 次：")
print("    拿到 →", repr(next(流)))
print()
print("  ★ for 行 in 流: 其实就是替我一遍遍伸手，直到要不出东西（StopIteration）。")
print("    所以流只能走一遍 —— 走完再 for 一次，一行都拿不到。")
print()

print("  另一个参数 decode_unicode：")
print("    不加 →", repr(b"data: \xe9\x97\xad"))       # 不加就是 bytes
print("    加了 →", repr(b"data: \xe9\x97\xad".decode("utf-8")))
print("    （不加也能用，但每行都是 b'...'，你得自己 .decode()）")


# ================================================================ 幕二
print()
print("=" * 62)
print("幕二：真跑一次，记每一行到手的秒数（花 1 次钱）")
print("=" * 62)

体 = {"model": 问模型.模型名,
      "messages": [{"role": "user", "content": "用两句话说说什么是变量"}],
      "stream": True}
r = requests.post(问模型.聊天地址, headers=头, json=体, stream=True, timeout=60)
r.raise_for_status()

开始 = time.time()
记录 = []
for 行 in r.iter_lines(decode_unicode=True):
    记录.append((len(记录) + 1, time.time() - 开始, 行))

print(f"  一共 {len(记录)} 行。挑几行看看它们各自的到手时刻：")
print()
挑 = 记录[:4] + 记录[len(记录) // 2: len(记录) // 2 + 2] + 记录[-2:]
for 号, 秒, 行 in 挑:
    样子 = 行 if len(行) <= 54 else 行[:54] + "…"
    print(f"    第 {号:>3} 行   第 {秒:5.2f} 秒   {样子!r}")
print()
空行 = sum(1 for _, _, 行 in 记录 if not 行)
数据行 = sum(1 for _, _, 行 in 记录 if 行.startswith("data: "))
收工 = [号 for 号, _, 行 in 记录 if 行 == "data: [DONE]"]
print(f"  统计：空行 {空行} 个 / data: 行 {数据行} 个 / [DONE] 在第 {收工} 行")
print(f"        第一行到第 {记录[0][1]:.2f} 秒，最后一行到第 {记录[-1][1]:.2f} 秒")
print()
print("  ★ 秒数是从小到大排上去的 —— 行是**陆续**到的，不是最后一起给你。")
print("    这就是为什么能边收边打：每拿到一行，你就处理一行。")
print()
print("  ⚠️ 反过来，如果你写 r.text 或 r.json()：")
print("     那是「整箱到货」，它会一直等到 [DONE] 之后的最后一行为止，然后才返回。")
print("     流式的意义就白费了 —— 你等到的东西跟非流式一样。")
