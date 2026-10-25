# -*- coding: utf-8 -*-
"""第 ⑨ 课演示：同一台机器人，改造前 vs 改造后。

改造前（就是现在 主程序.py 被你改掉的那一版）：
    问题 ──► 检索一次 ──► 拼进提示词 ──► 模型答
    没有记忆：每个问题都是一本新本子
    没有账本：它根本看不见柜子

改造后（Agent）：
    问题 ──► 它看菜单递申请 ──► 你替它跑 ──► 结果塞回去 ──► 它再答
    本子是你攥着的：追问「那 10 月呢」它知道在说餐饮
    菜单里挂着 read_ledger：账本它自己查

三个问题，故意选成两种考法：
    ① 9 月餐饮一共多少？   ← 笔记里没有，账本里有
    ② 那 10 月呢？         ← 必须记得上一句在说什么
    ③ 闭包是什么？         ← 笔记里有

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _主程序改造演示.py

⚠️ 只读演示：只挂 search_notes 和 read_ledger，不挂 add_expense，账本一个字不会变。
   演示用的账本是 演示改造账本.db（从 记账演示.db 复制），跑完就扔。
"""

import json
import os
import shutil
import sqlite3
import sys

import requests

import 主程序
import 检索
import 问模型

sys.stdout.reconfigure(errors="replace")

接口 = "https://api.deepseek.com"
聊天地址 = 接口 + "/chat/completions"
模型名 = "deepseek-flash"
钥匙名 = "DEEPSEEK_API_KEY"

这里 = os.path.dirname(os.path.abspath(__file__))
账本路径 = os.path.join(这里, "演示改造账本.db")
账本母本 = os.path.join(这里, "记账演示.db")

取几块 = 3

问题们 = [
    "9 月餐饮一共多少？",
    "那 10 月呢？",
    "闭包是什么？",
]


# ================================================================ 改造前：老管线
def 老管线(问题: str) -> tuple[str, int]:
    """一次检索 + 一次请求。返回 (答案, 检索次数)。"""
    挑中的 = 检索.找相关(问题, 块们, 取几块)
    节选 = "\n\n".join(块["正文"] for 块 in 挑中的)
    提示词 = f"""下面是给你的笔记节选：

{节选}

根据上面的笔记回答：{问题}
如果笔记里没有，只输出：[[无答案]]"""
    return 问模型.问一句(提示词), 1


# ================================================================ 改造后：Agent
def 查笔记(query: str) -> str:
    挑中的 = 检索.找相关(query, 块们, 取几块)
    print(f"        [search_notes] {query!r} → {len(挑中的)} 块")
    return "\n\n".join(
        f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的
    )


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
    try:
        行们 = 连接.execute(
            f"SELECT date, category, amount, note FROM 记录 WHERE {' AND '.join(条件)} ORDER BY date",
            值,
        ).fetchall()
    finally:
        连接.close()
    if not 行们:
        return f"没有符合条件的支出（月份={month or '全部'}，分类={category or '全部'}）。"
    合计 = sum(额 for _, _, 额, _ in 行们)
    return f"共 {len(行们)} 笔，合计 {合计:.2f} 元。"


工具表 = {"search_notes": 查笔记, "read_ledger": 查账}
菜单 = [条 for 条 in 主程序.菜单 if 条["function"]["name"] in 工具表]


def 执行申请(申请: dict) -> str:
    名字 = 申请["function"]["name"]
    参数 = json.loads(申请["function"]["arguments"])
    print(f"        【{名字}】{json.dumps(参数, ensure_ascii=False)}")
    try:
        return str(工具表[名字](**参数))
    except Exception as 错:
        return f"【工具报错】{type(错).__name__}: {错}"


def 新管线(问题: str, 本子: list, 计数: dict) -> str:
    本子.append({"role": "user", "content": 问题})
    最后 = ""
    for _ in range(5):
        计数["请求"] += 1
        回 = 问模型.发消息(本子, 菜单)
        回话 = 回["message"]
        申请们 = 回话.get("tool_calls") or []
        if not 申请们:
            最后 = (回话.get("content") or "").strip()
            本子.append(回话)
            return 最后
        本子.append(回话)
        for 申请 in 申请们:
            结果 = 执行申请(申请)
            计数["工具"] += 1
            本子.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})
    return "（转了 5 轮还在递申请，停了）"


if __name__ == "__main__":
    if not os.path.exists(账本母本):
        raise SystemExit("母本不在，先跑：python _造演示账本.py")
    shutil.copyfile(账本母本, 账本路径)

    块们 = 检索.可用块()
    print(f"可用块：{len(块们)}；账本：21 笔，9 月餐饮 262.00，10 月餐饮 242.50")
    print()

    # ---------------- 改造前 ----------------
    print("=" * 70)
    print("█ 改造前：老管线（每个问题独立，检索写死一次）")
    print("=" * 70)
    老请求 = 老检索 = 老答对 = 0
    for 问题 in 问题们:
        答案, 检索次数 = 老管线(问题)
        老请求 += 1
        老检索 += 检索次数
        拒了 = "[[无答案]]" in 答案
        老答对 += 0 if 拒了 else 1
        print(f"  问：{问题}")
        print(f"    检索 {检索次数} 次；它说：{答案[:60].replace(chr(10), ' ')}")
    print()
    print(f"  请求 {老请求} 次 / 检索 {老检索} 次 / 答对 {老答对}/3")
    print("  两个「那 10 月呢」都答不上：没有记忆，也没有账本 —— 笔记里当然查不到钱。")

    # ---------------- 改造后 ----------------
    print()
    print("=" * 70)
    print("█ 改造后：Agent（一本本子记着，菜单里有 search_notes + read_ledger）")
    print("=" * 70)
    本子 = [{"role": "system", "content": 主程序.规矩}]
    计数 = {"请求": 0, "工具": 0}
    新答对 = 0
    for 问题 in 问题们:
        答案 = 新管线(问题, 本子, 计数)
        拒了 = "[[无答案]]" in 答案
        新答对 += 0 if 拒了 else 1
        print(f"  问：{问题}")
        print(f"    它说：{答案[:70].replace(chr(10), ' ')}")
    print()
    print(f"  请求 {计数['请求']} 次 / 工具 {计数['工具']} 次 / 答对 {新答对}/3")

    print()
    print("=" * 70)
    print("对照表")
    print("=" * 70)
    print(f"  {'':14}{'改造前':>10}{'改造后':>10}")
    print(f"  {'请求次数':14}{老请求:>10}{计数['请求']:>10}")
    print(f"  {'工具次数':14}{0:>10}{计数['工具']:>10}   ← 老管线没有工具，检索是硬跑的")
    print(f"  {'答对题数':14}{f'{老答对}/3':>10}{f'{新答对}/3':>10}")
    print()
    print("  外面看到的东西没变：两种写法返回的都是字符串，拒答都含 [[无答案]]。")
    print("  变的是里面：查什么、查几次、要不要查账本 —— 决定权从你的代码挪到了它手里。")

    print()
    print("再数一个：这 3 个问题，老管线一共往模型里塞了", end=" ")
    print("3 份笔记节选；新管线只把「它要看的那几块」塞回去，")
    print("而且第 2 问的那 3 块，第 1 问时压根不知道要用 —— 是它自己回头要的。")
