# -*- coding: utf-8 -*-
"""第 12 课：把 拼碎片 那一段**一行一行跑给你看**。

不看文字描述，只看数：每收一片，正文多长、柜子里有几张申请、每张的表填到哪了。

三幕：
  幕一  一片一片走，每片之后把两个袋子倒出来
  幕二  收尾那两行（消息 = ... / if 申请们:）分别干了什么
  幕三  故意改坏其中一行，看坏在哪（五个版本，同一批碎片）
"""

import json

碎片们 = [
    {"role": "assistant", "content": None, "reasoning_content": ""},
    {"content": None, "reasoning_content": "先查账"},
    {"tool_calls": [{"index": 0, "id": "call_a", "type": "function",
                     "function": {"name": "read_ledger", "arguments": ""}}]},
    {"tool_calls": [{"index": 1, "id": "call_b", "type": "function",
                     "function": {"name": "search_notes", "arguments": ""}}]},
    {"tool_calls": [{"index": 0, "function": {"arguments": '{"mo'}}]},
    {"tool_calls": [{"index": 1, "function": {"arguments": '{"qu'}}]},
    {"tool_calls": [{"index": 0, "function": {"arguments": 'nth": "2026-09"}'}}]},
    {"tool_calls": [{"index": 1, "function": {"arguments": 'ery": "闭包"}'}}]},
]


def 摘要(申请们: dict) -> str:
    """把柜子压成一行字，方便每片之后看一眼。"""
    if not 申请们:
        return "（空的）"
    行们 = []
    for 序 in sorted(申请们):
        壳 = 申请们[序]
        函数 = 壳.get("function") or {}
        行们.append(f"[{序}] id={壳.get('id')!r} 名={函数.get('name')!r} 参数={函数.get('arguments')!r}")
    return "  |  ".join(行们)


# ================================================================ 幕一
print("=" * 66)
print("幕一：一片一片走，每片之后看两个袋子")
print("=" * 66)

print("  ① 先看正文那一条支路（这是一批『单纯说话』的碎片）：")
内容碎片们 = [
    {"role": "assistant", "content": None, "reasoning_content": ""},
    {"content": None, "reasoning_content": "我想想"},
    {"content": "闭"},
    {"content": "包"},
    {"content": "。"},
]
正文 = ""
for 号, 片 in enumerate(内容碎片们, 1):
    段 = 片.get("content")
    if 段 is not None:
        正文 += 段
    print(f"     第 {号} 片  content={段!r:8} →  正文 {正文!r}")
print("     ★ content 是 None 的片不加（那不是正文，是草稿）；是 '' 的加了也没变化。")
print()

print("  ② 再看申请那一条支路（这批是『递申请』的回话，所以正文一直是空的 —— 它没说话）：")
正文 = ""
申请们: dict[int, dict] = {}

for 号, 片 in enumerate(碎片们, 1):
    带了啥 = []
    if 片.get("content") is not None:
        正文 += 片["content"]
        带了啥.append(f"正文 {片['content']!r}")
    if 片.get("tool_calls"):
        带了啥.append(f"申请单 {len(片['tool_calls'])} 张")

    for 申 in 片.get("tool_calls") or []:
        壳 = 申请们.setdefault(
            申["index"],
            {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
        )
        if 申.get("id"):
            壳["id"] = 申["id"]
        函数 = 申.get("function") or {}
        if 函数.get("name"):
            壳["function"]["name"] = 函数["name"]
        壳["function"]["arguments"] += 函数.get("arguments") or ""

    print(f"  第 {号} 片  带来：{'、'.join(带了啥) if 带了啥 else '什么也没有（草稿片 / 空片）'}")
    print(f"          正文   {正文!r}   长度 {len(正文)}")
    print(f"          申请们 {摘要(申请们)}")
    if 片.get("tool_calls"):
        print(f"          ↑ 柜子里第几次被碰：这一片是 {len(片['tool_calls'])} 张，"
              f"每一张都先 setdefault 占位、再往里填")
    print()

print("  幕一走完：")
print(f"    正文   {正文!r}")
print(f"    申请们 {摘要(申请们)}")


# ================================================================ 幕二
print()
print("=" * 66)
print("幕二：收尾那两行，各干一件事")
print("=" * 66)

消息 = {"role": "assistant", "content": 正文}
print(f"  ① 消息 = {{'role': 'assistant', 'content': 正文}}")
print(f"     → {消息}")
print()
print(f"  ② if 申请们:  消息['tool_calls'] = [申请们[序] for 序 in sorted(申请们)]")
print("     为什么要 if：没有申请的时候，非流式那条消息里【根本没有 tool_calls 这个键】，")
print("     你要是硬塞一个空列表，键就对不上了 —— 比形状的时候会露。")
print(f"     为什么要 sorted：字典的键顺序 = 你第一次见到它的顺序。")
print(f"     这批碎片先来 0 再来 1，所以正好有序；要是模型先来 1 再来 0，")
print(f"     不 sorted 就会把申请单排成 1、0 —— 执行顺序和日志顺序都会乱。")

if 申请们:
    消息["tool_calls"] = [申请们[序] for 序 in sorted(申请们)]
print()
print(f"  最后拼出来的消息：")
print("    " + json.dumps(消息, ensure_ascii=False, indent=2).replace("\n", "\n    "))


# ================================================================ 幕三
print()
print("=" * 66)
print("幕三：故意改坏一行，看坏在哪")
print("=" * 66)

def 正版(碎片们):
    正文 = ""
    申请们 = {}
    for 片 in 碎片们:
        if 片.get("content") is not None:
            正文 += 片["content"]
        for 申 in 片.get("tool_calls") or []:
            壳 = 申请们.setdefault(
                申["index"],
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if 申.get("id"):
                壳["id"] = 申["id"]
            函数 = 申.get("function") or {}
            if 函数.get("name"):
                壳["function"]["name"] = 函数["name"]
            壳["function"]["arguments"] += 函数.get("arguments") or ""
    return 正文, 申请们


def 每片覆盖(碎片们):
    """错法一：把碎片本身当成申请单存进去（没有空壳、没有 +=）。"""
    正文 = ""
    申请们 = {}
    for 片 in 碎片们:
        if 片.get("content") is not None:
            正文 += 片["content"]
        for 申 in 片.get("tool_calls") or []:
            申请们[申["index"]] = 申          # ← 每来一片就整个盖掉
    return 正文, 申请们


def 不判id(碎片们):
    """错法二：没有 `if 申.get("id")`，后面的片把 id 覆盖成 None。"""
    正文 = ""
    申请们 = {}
    for 片 in 碎片们:
        if 片.get("content") is not None:
            正文 += 片["content"]
        for 申 in 片.get("tool_calls") or []:
            壳 = 申请们.setdefault(
                申["index"],
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            壳["id"] = 申.get("id")          # ← 后面那些片没有 id，就成了 None
            函数 = 申.get("function") or {}
            if 函数.get("name"):
                壳["function"]["name"] = 函数["name"]
            壳["function"]["arguments"] += 函数.get("arguments") or ""
    return 正文, 申请们


def 参数用等号(碎片们):
    """错法三：arguments 写成 = 不是 +=，最后只剩最后一片。"""
    正文 = ""
    申请们 = {}
    for 片 in 碎片们:
        if 片.get("content") is not None:
            正文 += 片["content"]
        for 申 in 片.get("tool_calls") or []:
            壳 = 申请们.setdefault(
                申["index"],
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if 申.get("id"):
                壳["id"] = 申["id"]
            函数 = 申.get("function") or {}
            if 函数.get("name"):
                壳["function"]["name"] = 函数["name"]
            壳["function"]["arguments"] = 函数.get("arguments") or ""   # ← =
    return 正文, 申请们


for 名字, 函数 in [("✅ 正版", 正版), ("❌ 每片覆盖", 每片覆盖),
                   ("❌ 不判 id", 不判id), ("❌ 参数用 =", 参数用等号)]:
    _, 申请们 = 函数(碎片们)
    print(f"  {名字:<10} {摘要(申请们)}")
    # 顺手试一下能不能当成"给主程序用的申请单"：取 id 和 json.loads(参数)
    for 序 in sorted(申请们):
        壳 = 申请们[序]
        函数体 = 壳.get("function") or {}
        print(f"     第 {序} 张 → id={壳.get('id')!r}  名字={函数体.get('name')!r}  "
              f"json.loads(参数) = ", end="")
        try:
            print(json.loads(函数体.get("arguments") or ""))
        except Exception as 错:
            print(f"【炸】{type(错).__name__}: {错}")
    print()

print("  ★ 四个版本跑完，只有第一个能交给主程序用：")
print("    · 每片覆盖：柜子里只剩最后一片，id 和名字全丢")
print("    · 不判 id  ：id 从 call_a 变成 None，主程序拿 None 去挂 tool_call_id")
print("    · 参数用 = ：参数只剩一个 '}'，json.loads 当场炸")
print()
print("  这三行代码（setdefault 占位 / if 申.get('id') / +=）就是整段的命门。")
