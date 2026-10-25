# -*- coding: utf-8 -*-
"""把一张「申请单」拆开看：参数 是什么、json.loads 干了什么、**参数 又是什么。

这三样每次都在 `执行申请` 里连着出现：

    名字 = 申请["function"]["name"]
    参数 = json.loads(申请["function"]["arguments"])
    工具表[名字](**参数)

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _参数演示.py

下面这张单子是真的（第 5 课 `_一次来回.py` 打出来的形状，只换了查询词）：
    · id / type 是单号，回 tool 消息时要抄回去
    · function.name 是「要动哪只手」
    · function.arguments 是它填的那几格 —— 注意：是一串**字**，不是字典
"""

import json

申请 = {
    "id": "call_00_9mJb1xKq2",
    "type": "function",
    "function": {
        "name": "search_notes",
        "arguments": '{"query": "isdigit 字符串 数字 校验"}',
    },
}

print("=" * 66)
print("第 1 层：申请 —— 整张单子")
print("=" * 66)
print("   ", 申请)
print("    类型 =", type(申请).__name__)

print()
print("=" * 66)
print("第 2 层：申请['function'] —— 单子里真正干活的那一格")
print("=" * 66)
print("   ", 申请["function"])
print("    类型 =", type(申请["function"]).__name__)

print()
print("=" * 66)
print("第 3 层：申请['function']['arguments'] —— 它填的参数")
print("=" * 66)
原样 = 申请["function"]["arguments"]
print("   ", repr(原样))
print("    类型 =", type(原样).__name__, "  长度 =", len(原样), "个字符")
print("    ⚠️ 它现在只是一串「字」：长得像字典，但还不是字典。")
try:
    原样["query"]
except TypeError as 错:
    print("    不信就试试 原样['query'] →", type(错).__name__, ":", 错)

print()
print("=" * 66)
print("第 4 层：json.loads(原样) —— 把「字」翻译成字典")
print("=" * 66)
参数 = json.loads(原样)
print("   ", 参数)
print("    类型 =", type(参数).__name__)
print("    ↑ 变量 参数 装的就是这个字典：它在单子上填的每一格，一格一个键。")

print()
print("=" * 66)
print("第 5 层：参数['query'] —— 它决定要查的那个词")
print("=" * 66)
print("   ", repr(参数["query"]))
print("    类型 =", type(参数["query"]).__name__)
print("    这个词不是你的代码写的，是从回包里读出来的（第 9 课那句「决定权挪了」）。")


def 查笔记(query: str) -> str:
    """假装是那只手。注意形参名就叫 query —— 跟单子上的键同名。"""
    return f"（翻了笔记，查的是：{query}）"


工具表 = {"search_notes": 查笔记}

print()
print("=" * 66)
print("最后一步：工具表[名字](**参数)")
print("=" * 66)
名字 = 申请["function"]["name"]
print(f"    名字 = {名字!r}")
print(f"    参数 = {参数!r}")
print(f"    **参数 的效果 = 把字典拆成一个个关键字参数：")
print(f"        查笔记(query={参数['query']!r})")
print("    结果 =", 工具表[名字](**参数))
print()
print("    键名对不上会怎样？下一行故意写错一个键：")
try:
    查笔记(**{"查询词": "闭包"})
except TypeError as 错:
    print("        →", type(错).__name__, ":", 错)
print("    所以菜单 parameters 里的键名 = 参数里的键名 = 函数的形参名，三处必须一个字不差。")
