# -*- coding: utf-8 -*-
"""推 vs 拉 —— 用「传菜口」讲清楚第 13 课幕三那根管子。

三幕，都不花钱：
  幕一  只有推：你把函数递出去，**它什么时候叫你，你说了不算**
  幕二  只有拉：你伸手要一次，它给你一个；**你不要，它不动**
  幕三  一个人推、另一个人拉 —— 中间必须有个传菜口（queue.Queue）

一句话：推 = 别人叫你的函数；拉 = 你的代码去要下一个值。
"""

import queue
import threading
import time

三样菜 = ["宫保鸡丁", "米饭", "汤"]


print("=" * 58)
print("幕一：只有推（回调）")
print("=" * 58)


def 后厨(交给谁):
    for 菜 in 三样菜:
        time.sleep(0.2)
        交给谁(菜)          # ★ 后厨主动塞出去，不问你要不要


def 服务员(菜):
    print(f"  端到：{菜}")


后厨(服务员)
print()
print("  注意 服务员 这个函数：没有 for、没有去要。")
print("  它只是被交了出去 —— 后厨做好一道，叫它一次。")


print()
print("=" * 58)
print("幕二：只有拉（生成器）")
print("=" * 58)


def 后厨二():
    for 菜 in 三样菜:
        time.sleep(0.2)
        yield 菜            # ★ 做到这一步就停住，等你来要


锅 = 后厨二()
print("  锅已经在了，但我先干别的 1 秒（后厨一片菜都没做）…")
time.sleep(1)
print(f"  第一次伸手 next(锅)：{next(锅)}")
print(f"  第二次伸手 next(锅)：{next(锅)}")
print(f"  第三次伸手 next(锅)：{next(锅)}")
print()
print("  ★ 三次伸手之间，后厨是停着的 —— 你不伸手，它就不动。")


print()
print("=" * 58)
print("幕三：一个推、一个拉，中间放个传菜口")
print("=" * 58)

传菜口: queue.Queue = queue.Queue()
开始 = time.time()


def 后厨三():
    for 菜 in 三样菜:
        time.sleep(0.3)
        传菜口.put(菜)          # 推：后厨只管往台子上放
        print(f"  [后厨] {time.time() - 开始:.2f} 秒  放上：{菜}")
    传菜口.put("下班")          # ★ 记号：没菜了，别再等了


def 服务员三():
    while True:
        print(f"  [服务员] {time.time() - 开始:.2f} 秒  站到台子前等…")
        菜 = 传菜口.get()       # 拉：台子上没有，就站在这儿等（不空转）
        if 菜 == "下班":
            print(f"  [服务员] {time.time() - 开始:.2f} 秒  看到「下班」，走人")
            break
        print(f"  [服务员] {time.time() - 开始:.2f} 秒  端走：{菜}")


threading.Thread(target=后厨三, daemon=True).start()
服务员三()

print()
print("  ★ 后厨按自己的节奏放（0.3 秒一道），服务员按自己的节奏端。")
print("    两边**从来没握过手**，全靠中间那个台子。")
print("  ★ 台子就是 queue.Queue：put 是推、get 是拉。")
print("  ★ 「下班」那块牌子少不得：没有它，get() 会一直站在台子前等 —— 请求永远不结束。")
print()
print("回到第 13 课：")
print("  `主程序.回答一个问题` 就是后厨（它只会调 打印 回调）")
print("  FastAPI 的 生成() 就是服务员（它必须 yield 出东西）")
print("  管子就是 传菜口，put(None) 就是那块「下班」牌子")
