# -*- coding: utf-8 -*-
"""第 8 课演示：会写的手 —— 闸门在代码里，不在提示词里。

前七课的工具都是**只读**的：查天气、翻笔记、查账本，跑一百遍，硬盘上的东西一个字不变。
今天加一只手 **add_expense**：往账本里 INSERT 一行。跑一次，世界就变了。

同一个问题，三遍：

    甲  没闸门：模型递了单子，你的代码直接写 —— 用户哪怕喊"别"，也已经写进去了
    乙  有闸门、用户答 n：停在你这里，账本 21 → 21
    乙  有闸门、用户答 y：放行，账本 21 → 22

然后每遍再问一句「现在 10 月餐饮一共多少」，用数字看有没有真的写进去：

    甲        10 月餐饮 = 270.50   ← 多了一笔 28
    乙 (n)    10 月餐饮 = 242.50   ← 没写
    乙 (y)    10 月餐饮 = 270.50   ← 写了

⚠️ 三遍各用各的账本副本（每次运行重新复制一份），不会弄脏 `记账演示.db`。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _写操作演示.py

⚠️ 只要一个环境变量：DEEPSEEK_API_KEY
"""

import json
import os
import re
import shutil
import sqlite3
import sys

import requests

sys.stdout.reconfigure(errors="replace")

接口 = "https://api.deepseek.com"
聊天地址 = 接口 + "/chat/completions"
模型名 = "deepseek-flash"

这里 = os.path.dirname(os.path.abspath(__file__))
母本 = os.path.join(这里, "记账演示.db")

问题_写 = "帮我记一笔：2026 年 10 月 24 日午饭 28 块，记在餐饮。"
问题_查 = "现在 10 月餐饮一共多少？"


# ================================================================ 两只手
def 查账(month: str = "", category: str = "") -> str:
    """只读那只手，第 6 课原样搬来。"""
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
        f"SELECT date, category, amount, note FROM 记录 WHERE {' AND '.join(条件)} ORDER BY date", 值
    ).fetchall()
    连接.close()

    if not 行们:
        return f"没有符合条件的支出（月份={month or '全部'}，分类={category or '全部'}）。"
    合计 = sum(额 for _, _, 额, _ in 行们)
    return f"共 {len(行们)} 笔，合计 {合计:.2f} 元。"


def 记一笔(amount: float, category: str, date: str, note: str = "") -> str:
    """会写的那只手：校验 → INSERT → 回答「写了几行、id 多少、现在共几笔」。

    ⚠️ 写和查最大的不同：查错了没损失；写错了，硬盘上多了一行，世界已经变了。
       所以写之前先校验，写之后要说清楚"改了什么"。
    """
    if amount <= 0:
        raise ValueError(f"金额必须是正数，收到 {amount}")
    if not category.strip():
        raise ValueError("分类不能为空")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"日期要写成 YYYY-MM-DD，收到 {date!r}")

    连接 = sqlite3.connect(账本路径)
    try:
        游 = 连接.execute(
            "INSERT INTO 记录 (amount, category, kind, date, note) VALUES (?, ?, 'expense', ?, ?)",
            (amount, category, date, note),
        )
        连接.commit()
        新号 = 游.lastrowid
        总数 = 连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
    finally:
        连接.close()

    return (
        f"已写入 1 行：id={新号}，{date} {category} {amount:.2f} {note}。"
        f"账本现在共 {总数} 笔。"
    )


工具表 = {"read_ledger": 查账, "add_expense": 记一笔}

菜单 = [
    {
        "type": "function",
        "function": {
            "name": "read_ledger",
            "description": "查我的记账本，问花了多少、某月/某分类开销、总共支出时用。只读，不改账本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "月份 YYYY-MM，比如 2026-10；不填=全部"},
                    "category": {"type": "string", "description": "分类，比如 餐饮；不填=全部"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": (
                "往我的记账本**写入**一笔支出。用户说“记一笔 / 帮我记 / 花了多少要记下来”时用。"
                "只读查询不要用它。写入前会让我人工确认。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "金额，正数，比如 28.0"},
                    "category": {"type": "string", "description": "分类，比如 餐饮、交通、房租"},
                    "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD，比如 2026-10-24"},
                    "note": {"type": "string", "description": "备注，比如 午饭"},
                },
                "required": ["amount", "category", "date"],
            },
        },
    },
]

规矩 = (
    "你是我的记账助手。\n"
    "只是问数字（花多少、某月开销），调用 read_ledger，不要动账本。\n"
    "我说“记一笔 / 帮我记”时，调用 add_expense 写入，四个参数按我说的填。\n"
    "每次调用之前，先把你要做的事用一句话说出来。\n"
    "查不到或没写成，就明说，不要猜。"
)

# 哪些工具算“会改东西”，执行前必须过闸门
写工具 = {"add_expense"}


def 发请求(消息们: list) -> dict:
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


# ================================================================ 闸门
def 请求确认(名字: str, 参数: dict, 脚本答案: list[str] | None) -> bool:
    """写操作执行前，停一下，把“将要发生什么”摊给用户看。

    脚本答案不为 None 时（演示用），从里面取一个；否则真问终端。
    """
    print("    ┌─ 需要你点头 ────────────────────────────────")
    print(f"    │ 要执行：{名字}({json.dumps(参数, ensure_ascii=False)})")
    print(f"    │ 会改账本：写入 1 行")
    if 脚本答案 is not None:
        答 = 脚本答案.pop(0) if 脚本答案 else "n"
        print(f"    │ 你答：{答}")
    else:
        答 = input("    │ 执行吗？(y/N) ")
    print("    └──────────────────────────────────────────────")
    return 答.strip().lower() in ("y", "yes")


def 执行申请(申请: dict, 有闸门: bool, 脚本答案: list[str] | None) -> tuple[str, bool]:
    名字 = 申请["function"]["name"]
    参数 = json.loads(申请["function"]["arguments"])

    # ---- 闸门：写工具先问，不是模型问，是你的代码问 ----
    if 有闸门 and 名字 in 写工具 and not 请求确认(名字, 参数, 脚本答案):
        return "用户拒绝了这次写入，账本一个字没改。不要重试，先把情况说清楚。", False

    try:
        return str(工具表[名字](**参数)), False
    except Exception as 错:
        return f"【工具报错】{type(错).__name__}: {错}\n这次没有写入。", True


# ================================================================ 跑一场
def 跑(名字: str, 副本名: str, 有闸门: bool, 脚本答案: list[str] | None) -> dict:
    global 账本路径
    账本路径 = os.path.join(这里, 副本名)
    shutil.copyfile(母本, 账本路径)          # 每场用干净副本，跑完不怕写脏

    print("\n" + "█" * 64)
    print(f"█ {名字}")
    print("█" * 64)

    连接 = sqlite3.connect(账本路径)
    行数前 = 连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
    连接.close()

    本子 = [{"role": "system", "content": 规矩}]
    写入次数 = 0
    拒绝次数 = 0
    最后答 = ""

    for 话 in (问题_写, 问题_查):
        print(f"\n──── 问：{话}")
        本子.append({"role": "user", "content": 话})
        for 轮 in range(1, 6):
            选 = 发请求(本子)
            回话 = 选["message"]
            申请们 = 回话.get("tool_calls") or []
            if not 申请们:
                最后答 = (回话.get("content") or "").strip()
                本子.append(回话)
                for 行 in 最后答.splitlines():
                    print("    它说：" + 行)
                break
            本子.append(回话)
            for 申请 in 申请们:
                名字工具 = 申请["function"]["name"]
                参数 = json.loads(申请["function"]["arguments"])
                print(f"    【{名字工具}】{json.dumps(参数, ensure_ascii=False)}")
                结果, _失败 = 执行申请(申请, 有闸门, 脚本答案)
                if "已写入" in 结果:
                    写入次数 += 1
                if "拒绝" in 结果:
                    拒绝次数 += 1
                for 行 in 结果.splitlines()[:3]:
                    print("        | " + 行)
                本子.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})

    连接 = sqlite3.connect(账本路径)
    行数后 = 连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
    十月餐饮 = 连接.execute(
        "SELECT SUM(amount) FROM 记录 WHERE kind='expense' AND date LIKE '2026-10%' AND category='餐饮'"
    ).fetchone()[0]
    连接.close()

    print(f"\n    账本行数：{行数前} → {行数后}    10 月餐饮合计：{十月餐饮:.2f}")
    return {"名字": 名字, "写入": 写入次数, "拒绝": 拒绝次数, "行数后": 行数后, "十月餐饮": 十月餐饮}


def 主流程() -> None:
    if not os.path.exists(母本):
        raise SystemExit("母本不在，先跑：python _造演示账本.py")

    甲 = 跑("甲：没有闸门（用户本想拒绝，但代码不问）", "写演示_甲.db", 有闸门=False, 脚本答案=None)
    乙n = 跑("乙：有闸门，用户答 n", "写演示_乙n.db", 有闸门=True, 脚本答案=["n"])
    乙y = 跑("乙：有闸门，用户答 y", "写演示_乙y.db", 有闸门=True, 脚本答案=["y"])

    print("\n" + "=" * 64)
    print("数一数，三场差在哪")
    print("=" * 64)
    for 结果 in (甲, 乙n, 乙y):
        print(f"\n【{结果['名字']}】")
        print(f"    写入了几次   = {结果['写入']}")
        print(f"    被拒了几次   = {结果['拒绝']}")
        print(f"    账本行数     = {结果['行数后']}   （开始 21）")
        print(f"    10 月餐饮    = {结果['十月餐饮']:.2f}")

    print("\n" + "-" * 64)
    print("甲那一场最刺眼：它压根没停下来问你 —— 28 块照写不误。")
    print("闸门不是模型「记得问」，是你的代码在调用工具之前停下来。")
    print("模型说得再客气，也不等于它会停；停不停，看你的 for 循环里有没有那个 if。")


if __name__ == "__main__":
    主流程()
