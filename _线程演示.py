# -*- coding: utf-8 -*-
"""线程 = 再叫一个人 —— 两个数就能看出来。不花钱。

  幕一  一个人做两件「等 1 秒」的事  →  2.0 秒（排队，等完一件再做第二件）
  幕二  两个人各做一件            →  1.0 秒（同时睡，一起醒）

回到第 13 课：`干活` 里要等模型好几秒，`生成()` 又要在这几秒里不断往外拿字。
一个人做不到两件事，所以叫第二个人 —— 那行 threading.Thread(...).start()。
"""

import threading
import time


def 等一秒(名字, 开始):
    print(f"    {名字} 开始等（第 {time.time() - 开始:.2f} 秒）")
    time.sleep(1)
    print(f"    {名字} 等完了（第 {time.time() - 开始:.2f} 秒）")


print("=" * 52)
print("幕一：一个人（顺序做）")
print("=" * 52)
开始 = time.time()
等一秒("甲", 开始)
等一秒("乙", 开始)
一个人 = time.time() - 开始
print(f"  → 一共 {一个人:.2f} 秒")


print()
print("=" * 52)
print("幕二：两个人（同时做）")
print("=" * 52)
开始 = time.time()
甲 = threading.Thread(target=等一秒, args=("甲", 开始), daemon=True)
乙 = threading.Thread(target=等一秒, args=("乙", 开始), daemon=True)
甲.start()          # ← 少了这一下，他只是"被雇了"，没上班
乙.start()
甲.join()           # 等他们俩都干完，再往下走（不然 main 先跑，数字会不准）
乙.join()
两个人 = time.time() - 开始
print(f"  → 一共 {两个人:.2f} 秒")


print()
print(f"★ 一个人 {一个人:.2f} 秒，两个人 {两个人:.2f} 秒 —— 两件事真的同时在跑。")
print()
print("三句话记住：")
print("  Thread(target=干活)  雇一个人，写的是【函数名，不带括号】")
print("  .start()             让他上班（不带就一直在旁边站着）")
print("  daemon=True          临时工：主程序一退，他跟着走")
print()
print("  注意：要带参数用 args=(\"甲\",) —— 单元素元组那个逗号不能省")
