# -*- coding: utf-8 -*-
"""第 12 课插问：setdefault 是什么。

一句话：**按号走到格子柜前取东西 —— 格子空，就先塞一个默认的进去，再把那个递给你；格子不空，直接递给你。**

跟 .get() 的区别就一个字：**塞**。
  .get("乙")              → 给你 None，**什么也没塞进柜子**
  .setdefault("乙", [])   → 塞一个空盒子进去，然后把盒子递给你
"""

import json

print("=" * 58)
print("幕一：没有它的时候，得写三行")
print("=" * 58)

分数 = {}
for 人, 分 in [("甲", 90), ("乙", 80), ("甲", 95)]:
    if 人 not in 分数:          # ① 先问：这个格子有没有
        分数[人] = []           # ② 没有就放一个空盒子进去
    分数[人].append(分)         # ③ 再往里装
print("  三行版  →", 分数)

分数 = {}
for 人, 分 in [("甲", 90), ("乙", 80), ("甲", 95)]:
    分数.setdefault(人, []).append(分)     # 三步压成一行
print("  setdefault 版 →", 分数)
print()
print("  注意它**有返回值**：返回的就是格子里现在那个盒子，所以能直接 .append(分)。")


print()
print("=" * 58)
print("幕二：跟 .get() 差在哪 —— 柜子里到底有没有多东西")
print("=" * 58)

格子 = {"甲": ["第一次"]}
print(f"  一开始         格子 = {格子}")
print(f"  .get('乙')     → {格子.get('乙')!r}          ← 给你 None（假的）")
print(f"  取完再看       格子 = {格子}   ← 乙没进去")
print()
print(f"  .setdefault('乙', []) → {格子.setdefault('乙', [])!r}")
print(f"  取完再看       格子 = {格子}   ← 乙进去了")
print()
print("  格子不空的时候，默认值没用，返回的是原来那个：")
格子 = {"甲": ["第一次"]}
print(f"  .setdefault('甲', ['全新的']) → {格子.setdefault('甲', ['全新的'])}")
print(f"  甲还是原来的：{格子}")


print()
print("=" * 58)
print("幕三：第 12 课就是用它 —— 碎片按 index 归队")
print("=" * 58)

# 真实的流式碎片：开头那片带 id 和 name，后面只有 index + arguments
碎片们 = [
    {"index": 0, "id": "call_a", "type": "function",
     "function": {"name": "read_ledger", "arguments": ""}},
    {"index": 1, "id": "call_b", "type": "function",
     "function": {"name": "search_notes", "arguments": ""}},
    {"index": 0, "function": {"arguments": '{"mo'}},
    {"index": 1, "function": {"arguments": '{"qu'}},
    {"index": 0, "function": {"arguments": 'nth": "2026-09"}'}},
    {"index": 1, "function": {"arguments": 'ery": "闭包"}'}},
]

申请们: dict[int, dict] = {}
for 片 in 碎片们:
    # 第 1 次见到 0 号 → 塞一个空壳进去，并把壳递回来；之后再见到就用同一个壳
    壳 = 申请们.setdefault(
        片["index"],
        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
    )
    if 片.get("id"):
        壳["id"] = 片["id"]
    函数 = 片.get("function") or {}
    if 函数.get("name"):
        壳["function"]["name"] = 函数["name"]
    壳["function"]["arguments"] += 函数.get("arguments") or ""

    print(f"  收到 index={片['index']} 的片 → 柜子里现在是这样：")
    print("    " + json.dumps(申请们, ensure_ascii=False))

print()
print("  ★ 没有 setdefault，就得先写 `if 序 not in 申请们:` 三行去占位。")
print("    有它，一行就够，而且**返回的壳一定能往里写** —— 这就是它存在的理由。")
print()
print("  ⚠️ 一个坑：第二个参数是**每次都先算出来**的，不是'需要了才算'。")
print("     这里是个字典字面量，无所谓；要是那一下很贵（比如查一次数据库），")
print("     就先 if 判断再算，别指望它偷懒。")
