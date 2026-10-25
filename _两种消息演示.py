# -*- coding: utf-8 -*-
"""第 7 课补演示：那两句 append，添的到底是谁说的话。

只问一句，只让它递一张申请，然后把本子打开，一条一条念：

    第 1 条   你     system      规矩
    第 2 条   你     user        问题
    第 3 条   它     assistant   申请单（里面有 tool_calls）
    第 4 条   你的代码 tool      回执（里面有 tool_call_id + 结果）
    第 5 条   它     assistant   人话答案

两句 append 的动作一模一样（都是往列表尾巴上加一条），
差别只在**这一条是谁的发言、里面有哪些键**。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _两种消息演示.py
"""

import json
import os
import sqlite3
import sys

import requests

sys.stdout.reconfigure(errors="replace")

接口 = "https://api.deepseek.com"
聊天地址 = 接口 + "/chat/completions"
模型名 = "deepseek-flash"

这里 = os.path.dirname(os.path.abspath(__file__))
账本路径 = os.path.join(这里, "记账演示.db")

规矩 = "你是我的记账助手。问数字就调用 read_ledger，不要凭印象算。"
问题 = "9 月我餐饮花了多少钱？"

菜单 = [
    {
        "type": "function",
        "function": {
            "name": "read_ledger",
            "description": "查我的记账本（2026 年 9 月、10 月的收支），问花了多少、某月/某分类开销就用这个。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "月份 YYYY-MM，比如 2026-09；不填=全部"},
                    "category": {"type": "string", "description": "分类，比如 餐饮；不填=全部"},
                },
                "required": [],
            },
        },
    }
]


def 查账(month: str = "", category: str = "") -> str:
    条件 = ["kind = 'expense'"]
    值: list = []
    if month:
        条件.append("date LIKE ?")
        值.append(month + "%")
    if category:
        条件.append("category = ?")
        值.append(category)
    连接 = sqlite3.connect(账本路径)
    行们 = 连接.execute(
        f"SELECT date, category, amount FROM 记录 WHERE {' AND '.join(条件)} ORDER BY date", 值
    ).fetchall()
    连接.close()
    合计 = sum(额 for _, _, 额 in 行们)
    拼 = "\n".join(f"{日} {类} {额:.2f}" for 日, 类, 额 in 行们)
    return f"{拼}\n合计：{合计:.2f}（共 {len(行们)} 笔）"


def 发一次(消息们: list) -> dict:
    钥匙 = os.environ.get("DEEPSEEK_API_KEY")
    if not 钥匙:
        raise SystemExit("没拿到 DEEPSEEK_API_KEY")
    r = requests.post(
        聊天地址,
        headers={"Authorization": "Bearer " + 钥匙, "Content-Type": "application/json"},
        json={"model": 模型名, "messages": 消息们, "tools": 菜单},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]


def 念一条(本子: list, 谁说: str) -> None:
    """把刚 append 进去的那条，原样念出来。"""
    条 = 本子[-1]
    print(f"\n本子第 {len(本子)} 条 —— {谁说}")
    print(f"    role = {条.get('role')!r}")
    print(f"    这条上全部的键 = {list(条.keys())}")
    if 条.get("tool_calls"):
        申请 = 条["tool_calls"][0]
        print(f"    tool_calls[0].id = {申请['id']!r}      ← 单号，只写在它这里")
        print(f"    tool_calls[0].function.name = {申请['function']['name']!r}")
        print(f"    tool_calls[0].function.arguments = {申请['function']['arguments']!r}")
    if 条.get("tool_call_id"):
        print(f"    tool_call_id = {条['tool_call_id']!r}  ← 和上一条那个单号是同一个")
    if 条.get("content"):
        正文 = str(条["content"])
        print("    content = " + (正文[:60].replace("\n", " / ") + ("…" if len(正文) > 60 else "")))


def 主流程() -> None:
    本子 = [{"role": "system", "content": 规矩}]
    print("=" * 64)
    print("问题：" + 问题)
    print("=" * 64)

    本子.append({"role": "user", "content": 问题})
    念一条(本子, "你写的 —— 用户说的话")

    # ---------------------------------------------------------- 第一次请求
    选 = 发一次(本子)
    回话 = 选["message"]
    申请们 = 回话.get("tool_calls") or []

    print("\n" + "-" * 64)
    print("【第一句 append】本子.append(回话)")
    print("-" * 64)
    本子.append(回话)
    念一条(本子, "API 返回的 —— 模型说的话")

    # ---------------------------------------------------------- 办事员跑
    申请 = 申请们[0]
    参数 = json.loads(申请["function"]["arguments"])
    结果 = 查账(**参数)

    print("\n" + "-" * 64)
    print("【第二句 append】本子.append({\"role\": \"tool\", ...})")
    print("-" * 64)
    本子.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})
    念一条(本子, "你的代码新造的 —— 办事员的回执")

    # ---------------------------------------------------------- 第二次请求
    选 = 发一次(本子)
    回话 = 选["message"]
    本子.append(回话)

    print("\n" + "=" * 64)
    print("本子现在长这样（谁说的 / role / 有没有单号）")
    print("=" * 64)
    谁 = ["你", "你", "模型", "你的代码", "模型"]
    for i, (人, 条) in enumerate(zip(谁, 本子), 1):
        标记 = ""
        if 条.get("tool_calls"):
            标记 = "  ← 递单子，带 tool_calls"
        elif 条.get("tool_call_id"):
            标记 = "  ← 回执，带 tool_call_id"
        print(f"    {i}. {人:<4} {条.get('role'):<9}{标记}")

    print("\n" + "-" * 64)
    print("那两句 append 的动作一模一样：都是往列表尾巴上加一条。")
    print("不一样的是**谁在说话、这条上有什么键**：")
    print("    assistant 那条 = 模型说的，带 tool_calls（单号在里面）")
    print("    tool 那条      = 你造的，带 tool_call_id（把同一张单号抄回来）+ 结果")
    print("本子是一份聊天记录，不是只有模型一个人在里面说话。")


if __name__ == "__main__":
    主流程()
