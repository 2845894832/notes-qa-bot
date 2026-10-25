# -*- coding: utf-8 -*-
"""Agent 第 8 课练习：给菜单挂一只**会写**的手（记一笔），并且让它先问你。

前七课的工具都是只读的：查天气、翻笔记、查账本 —— 跑一百遍，硬盘一个字不变。
今天要加的是 **add_expense**：往账本里 INSERT 一行。它一跑，世界就变了。

所以这一课多两件事：

    ① 写之前先校验（金额、分类、日期）—— 参数是模型给的，不能信
    ② 真写之前停一下，问你一句 y/n —— 闸门在**你的代码**里，不在提示词里

三个 TODO：
    ① 记一笔()    —— 校验 + INSERT + 回来报「写了 1 行 / id / 现在共几笔」
    ② 请求确认()  —— 把「将要发生什么」摊给用户看，收一个 y/n
    ③ 执行申请()  —— 接线：写工具必须先过闸门；用户拒了就不执行，但也要回一句

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _写操作练习.py

    ⚠️ 会停下来问你 y/n。答 n 一次、答 y 一次，分别看账本行数。
    ⚠️ 每次运行都会从 `记账演示.db` 复制一份新的 `记账练习.db`，写坏了重跑就行。

材料：Agent-复习速查.md「第 8 课：会写的手」
     演示：_写操作演示.py（先跑那个，看没闸门 / 有闸门差在哪）
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
钥匙名 = "DEEPSEEK_API_KEY"

这里 = os.path.dirname(os.path.abspath(__file__))
母本 = os.path.join(这里, "记账演示.db")
账本路径 = os.path.join(这里, "记账练习.db")

问题_写 = "帮我记一笔：2026 年 10 月 24 日午饭 28 块，记在餐饮。"
问题_查 = "现在 10 月餐饮一共多少？"


# ================================================================ TODO 1
def 记一笔(amount: float, category: str, date: str, note: str = "") -> str:
    """会写的那只手：校验 → INSERT → 报「写了几行、id 多少、现在共几笔」。

    TODO 1 —— 五步，前四步一步都不能省：

     ① 校验（先拦，别等 SQLite 报错）：
          amount <= 0            → raise ValueError(f"金额必须是正数，收到 {amount}")
          category.strip() 为空  → raise ValueError("分类不能为空")
          date 不是 YYYY-MM-DD   → raise ValueError(f"日期要写成 YYYY-MM-DD，收到 {date!r}")
          （正则已经 import re 了：re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", date)）

     ② 连柜子，INSERT 一行：
          INSERT INTO 记录 (amount, category, kind, date, note) VALUES (?, ?, 'expense', ?, ?)
          ⚠️ 值全走 ? —— 这四个值都来自模型
          ⚠️ kind 是写死的 'expense'，因为它不是参数，是你自己定的

     ③ 提交：`连接.commit()` —— 不 commit，关掉连接就白写

     ④ 拿两个数：
          `游.lastrowid`                                  刚插进去那一行的 id
          `连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]`   现在共几笔

     ⑤ return 一句人话，必须包含：写了几行、id、日期/分类/金额/备注、现在共几笔
          例如：已写入 1 行：id=22，2026-10-24 餐饮 28.00 午饭。账本现在共 22 笔。
          ⚠️ 只说"写入成功"不够 —— 模型和用户都得知道**写成了什么样**

    已给：连接怎么开、怎么关（try/finally），表名和列名
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
        新行id = 游.lastrowid
        总笔数 = 连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
        return f"已写入 1 行：id={新行id}，{date} {category} {amount:.2f} {note or ''}。账本现在共 {总笔数} 笔。"
    finally:    
        连接.close()


# ================================================================ TODO 2
# 哪些工具算“会改东西”，执行前必须过闸门
写工具 = set({"add_expense"})          # ← TODO 2(a)：填上写工具的名字（字符串），比如 {"add_expense"}


def 请求确认(名字: str, 参数: dict) -> bool:
    """把「将要发生什么」摊给用户看，收一个 y/n。

    TODO 2(b)：四步
     ① 打印要执行的东西：名字 + 参数（json.dumps(参数, ensure_ascii=False)）
        再打印一句“会改账本：写入 1 行”
     ② `答 = input("执行吗？(y/N) ")`
     ③ 返回 True 只当答的是 y / yes（大小写都算）：
        答.strip().lower() in ("y", "yes")
     ④ 其它一律 False —— 空回车、乱打字，都当“不执行”

    ⚠️ 默认必须是“不执行”。手一抖按了回车，宁可没写，也别写进去。
    """
    print(f"将要执行：{名字} {json.dumps(参数, ensure_ascii=False)}")
    print("会改账本：写入 1 行")
    答 = input("执行吗？(y/N) ")
    return 答.strip().lower() in ("y", "yes")


# ================================================================ TODO 3
def 执行申请(申请: dict) -> tuple[str, bool]:
    """执行一张申请。返回 (塞回给模型的文字, 这次算不算失败)。

    TODO 3：在 `try` 前面加闸门，三行：

        if 名字 in 写工具 and not 请求确认(名字, 参数):
            return "用户拒绝了这次写入，账本一个字没改。不要重试，先把情况说清楚。", False

    ⚠️ 闸门要在**调用工具之前**。写完了再问，那不叫确认，叫通知。
    ⚠️ 拒绝要回一句，因为第 4 课那条：每张申请都得有回音，否则下一次请求 400。
    ⚠️ 拒绝不算失败（返回 False）：工具没跑、没报错，只是用户说不。
    """
    名字 = 申请["function"]["name"]
    参数 = json.loads(申请["function"]["arguments"])
    if 名字 in 写工具 and not 请求确认(名字, 参数): 
        return "用户拒绝了这次写入，账本一个字没改。不要重试，先把情况说清楚。", False  
    try:
        return str(工具表[名字](**参数)), False
    except Exception as 错:
        return f"【工具报错】{type(错).__name__}: {错}\n这次没有写入。", True


# ================================================================ 以下全是给你的，一个字别改
def 查账(month: str = "", category: str = "") -> str:
    """第 6 课那只只读的手，原样搬来。"""
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


def 拿钥匙() -> str:
    钥匙 = os.environ.get(钥匙名)
    if not 钥匙:
        raise RuntimeError(f"环境变量 {钥匙名} 没拿到。先 setx 一遍，然后开一个新终端。")
    return 钥匙


def 发一次(本子: list) -> dict:
    请求头 = {"Authorization": "Bearer " + 拿钥匙(), "Content-Type": "application/json"}
    请求体 = {"model": 模型名, "messages": 本子, "tools": 菜单}
    r = requests.post(聊天地址, headers=请求头, json=请求体, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]


def 聊一句(本子: list, 话: str, 最多几轮: int = 5) -> str:
    本子.append({"role": "user", "content": 话})
    最后 = ""
    for 轮 in range(1, 最多几轮 + 1):
        选 = 发一次(本子)
        回话 = 选["message"]
        申请们 = 回话.get("tool_calls") or []
        if not 申请们:
            最后 = (回话.get("content") or "").strip()
            本子.append(回话)
            break
        本子.append(回话)
        for 申请 in 申请们:
            名字 = 申请["function"]["name"]
            参数 = json.loads(申请["function"]["arguments"])
            print(f"    【{名字}】{json.dumps(参数, ensure_ascii=False)}")
            结果, 失败了 = 执行申请(申请)
            for 行 in 结果.splitlines()[:3]:
                print("        | " + 行)
            if 失败了:
                print("        ← 这次失败了")
            本子.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})
    return 最后


def 数一下() -> tuple[int, float]:
    连接 = sqlite3.connect(账本路径)
    行数 = 连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
    十月餐饮 = 连接.execute(
        "SELECT SUM(amount) FROM 记录 WHERE kind='expense' AND date LIKE '2026-10%' AND category='餐饮'"
    ).fetchone()[0]
    连接.close()
    return 行数, (十月餐饮 or 0.0)


def 主流程() -> None:
    if not os.path.exists(母本):
        raise SystemExit("母本不在，先跑：python _造演示账本.py")
    shutil.copyfile(母本, 账本路径)      # 每次从干净副本开始

    行数前, 餐饮前 = 数一下()
    本子 = [{"role": "system", "content": 规矩}]

    print("=" * 64)
    print(f"账本现在 {行数前} 笔，10 月餐饮 {餐饮前:.2f}")
    print("=" * 64)

    for 话 in (问题_写, 问题_查):
        print(f"\n──── 问：{话}")
        答 = 聊一句(本子, 话)
        print("它说：")
        for 行 in 答.splitlines():
            print("    " + 行)

    行数后, 餐饮后 = 数一下()
    print("\n" + "=" * 64)
    print("数一数")
    print("=" * 64)
    print(f"    账本行数          = {行数前} → {行数后}")
    print(f"    10 月餐饮合计     = {餐饮前:.2f} → {餐饮后:.2f}")

    连接 = sqlite3.connect(账本路径)
    新行 = 连接.execute(
        "SELECT id, date, category, amount, note FROM 记录 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    连接.close()
    print(f"    最后一行          = {新行}")
    print()
    print("对照答案：")
    print("    · 你答 n：行数不变（21 → 21），10 月餐饮还是 242.50，工具回音里写着“拒绝”")
    print("    · 你答 y：行数 21 → 22，10 月餐饮 242.50 → 270.50，最后一行是 (22, 2026-10-24, 餐饮, 28.0, 午饭)")
    print("    · 两种情况下它都该把“记了 / 没记”说清楚，不编")


if __name__ == "__main__":
    主流程()
