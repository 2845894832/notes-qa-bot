# -*- coding: utf-8 -*-
"""「本子只能做成第三个可选参数」到底保住了什么。

老调用（web/服务.py、_端到端体检.py）都只传两个：
    主程序.回答一个问题(问题, 块们)

新函数变成：
    def 回答一个问题(问题, 块们, 本子=None, 最多几轮=5)

`本子=None` 的意思是：这个参数可以不传，不传就当 None；
进函数后 `if 本子 is None:` 现开一本。
所以老的两参数调用一个字不用改，照样能跑。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _可选参数演示.py
"""


def 回答一个问题(问题: str, 块们: list, 本子: list | None = None) -> list:
    if 本子 is None:
        本子 = [{"role": "system", "content": "规矩"}]
        来源 = "函数里现开了一本"
    else:
        来源 = "用了传进来的那本"

    本子.append({"role": "user", "content": 问题})
    说过的话 = [条["content"] for 条 in 本子]
    print(f"    来源 = {来源}")
    print(f"    本子现在 {len(本子)} 条：{说过的话}")
    return 本子


print("① 老调用：只传两个参数（web、体检就是这么调的）")
回答一个问题("闭包是什么", [])

print()
print("② 老调用再来一次 —— 没传本子，所以每次都是新的，看不见上一问")
回答一个问题("那 10 月呢", [])

print()
print("③ 新调用：把同一本传进去（交互模式）")
本子 = [{"role": "system", "content": "规矩"}]
回答一个问题("9 月餐饮多少", [], 本子)
回答一个问题("那 10 月呢", [], 本子)

print()
print("④ 假如 本子 写成必填（没有 = None），老调用会怎样：")
print("    def 回答一个问题(问题, 块们, 本子):   ← 第三个没有默认值")


def 坏版本(问题: str, 块们: list, 本子: list) -> None:
    pass


try:
    坏版本("闭包是什么", [])
except TypeError as 错:
    print("    →", type(错).__name__, ":", 错)
print()
print("一句话：默认值 = 「这个参数可以不传」。不传也合法，旧调用才不坏。")
