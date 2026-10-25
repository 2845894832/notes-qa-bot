# -*- coding: utf-8 -*-
"""把 `连接.execute(...).fetchone()[0]` 拆成四步，一步打印一次。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _count演示.py
"""

import os
import sqlite3

这里 = os.path.dirname(os.path.abspath(__file__))
账本 = os.path.join(这里, "记账演示.db")

连接 = sqlite3.connect(账本)

print("第 1 步：execute 交一句 SQL 下去，回来的是个「游标」")
游 = 连接.execute("SELECT COUNT(*) FROM 记录")
print("    游 =", 游)
print("    类型 =", type(游))
print()

print("第 2 步：fetchone 从结果里取一行")
行 = 游.fetchone()
print("    行 =", 行)
print("    类型 =", type(行))
print()

print("第 3 步：[0] 取这一行的第一格")
数 = 行[0]
print("    数 =", 数)
print("    类型 =", type(数))
print()

print("对照：如果 SQL 查的是两列，fetchone 回来的还是元组，只是格子多")
两列 = 连接.execute("SELECT id, amount FROM 记录 ORDER BY id LIMIT 1").fetchone()
print("    两列 =", 两列, " 类型 =", type(两列))

连接.close()
