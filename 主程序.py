# -*- coding: utf-8 -*-
"""第 ⑨ 课：把整条线接成一只 Agent —— 检索不再每次必跑，改成它自己决定。

改造前（第 ③ 步那版）：
    问题 ──► 检索一次（写死 top 3）──► 拼进提示词 ──► 模型答

改造后：
    问题 ──► 它看菜单递申请：search_notes / read_ledger / add_expense
          ──► 你替它跑 ──► 结果塞回去 ──► 它再决定 ──► 答

⚠️ 外面的人一个字不用改（这是这次改造的硬要求）：
    · web/服务.py      调 主程序.回答一个问题(问题, 块们)
    · _端到端体检.py   调 主程序.回答一个问题(问题, 块们)
    · 命令行           python 主程序.py "闭包是什么"
   拿到的还是一个字符串；拒答时里面还是 [[无答案]]。
   所以改完第一件事不是庆祝，是拿旧尺子重跑一遍。

为什么是"硬"要求：三个调用点里，体检脚本是**尺子** —— 尺子跟着接口一起改，
改造前后的数就没法比，"改造成功"也就没有证据；web 那张脸还挂在魔搭上，
改接口要连部署一起改，漏一处就是线上 500。
换引擎、不换方向盘，才能用同一把尺子证明"里面换了、外面没坏"。
"""

import json
import os
import re
import shutil
import sqlite3
import sys

import 检索
import 问模型

取几块 = 3

这里 = os.path.dirname(os.path.abspath(__file__))
账本路径 = os.path.join(这里, "我的账本.db")
账本母本 = os.path.join(这里, "记账演示.db")

# 工具函数只收得到模型给的那几个参数。笔记是"我这边的东西"，不进菜单：
# 每次 回答一个问题 进来时先装到这里，查笔记 再从这里拿。
当前块们: list[dict] = []


def 准备好账本() -> None:
    """第一次跑：把演示账本（21 笔）复制成 我的账本.db。

    已经存在就一个字不动。想回到 21 笔：删掉 我的账本.db 再跑。
    """
    if not os.path.exists(账本路径) and os.path.exists(账本母本):
        shutil.copyfile(账本母本, 账本路径)


# ================================================================ 三只手
def 查笔记(query: str) -> str:
    """只读的手：拿一句话去笔记里翻，把挑中的几块拼成带出处的文字。"""
    # TODO 1 —— 两行，第 5 课那只手原样搬进来：
    #
    #   ① 翻：挑中的 = 检索.找相关(query, 当前块们, 取几块)
    #        ⚠️ 第二个参数是 当前块们 —— 工具函数只收得到模型给的那一个 query，
    #           笔记是"我这边的东西"，进 回答一个问题 时已经装进 当前块们 了。
    #
    #   ② 拼：一块一段，空一行，每段开头带出处：
    #         [python-learning-2026-09-01.md:99 ### 二、闭包]
    #         （这块的正文）
    #       一行就够：
    #         return "\n\n".join(f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的)
    #
    #       挑中 0 块时，先 return 一句"没找到"（别返回空字符串 ——
    #       模型分不清"没查到"和"没说话"）。
    #
    #   ③ 顺手打印：先一行 `[search_notes] 'query' → 挑中 N 块`，再逐块打印 文件:行号 标题。
    #      日志里才看得出它每次翻了什么 —— 看不出来的东西，变成能数的数。
    #
    #   ⚠️ 别 return str(挑中的)：那是 Python 字典的长相（单引号、逗号、大括号），
    #      给模型看等于看乱码。第 3、5 课都踩过。
    挑中的 = 检索.找相关(query,当前块们,取几块)
    print(f"    [search_notes] {query!r} → 挑中 {len(挑中的)} 块")
    return "\n\n".join(f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的)



def 查账(month: str = "", category: str = "") -> str:
    """只读的手：查账本。第 6 课原样搬来，只有路径换成了 我的账本.db。"""
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


def 记一笔(amount: float, category: str, date: str, note: str = "") -> str:
    """会写的手：校验 → INSERT → 报「写了几行、id 多少、现在共几笔」。第 8 课原样搬来。"""
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
        return (
            f"已写入 1 行：id={新行id}，{date} {category} {amount:.2f} {note or ''}。"
            f"账本现在共 {总笔数} 笔。"
        )
    finally:
        连接.close()


# ================================================================ 闸门
# 会改东西的工具，全在这里点名。漏一个 = 世界已经变了，但没人问过你。
写工具 = {"add_expense"}


def 请求确认(名字: str, 参数: dict) -> bool:
    """把「将要发生什么」摊给用户看，收一个 y/n。默认必须是"不执行"。"""
    print(f"将要执行：{名字} {json.dumps(参数, ensure_ascii=False)}")
    print("会改账本：写入 1 行")
    # ⚠️ 第 10 课补的：容器里的 stdin 不是"结束"，是"一根永远没人说话的空管"。
    # 直接 input() 不会抛 EOFError，而是**一直等**下去 —— 线上表现就是 504（121 秒）。
    # isatty() = "接在我后面的是不是一个真人终端"。不是 → 当没人点头。
    if not sys.stdin.isatty():
        print("（这里没有终端可问 → 按拒绝处理）")
        return False
    try:
        答 = input("执行吗？(y/N) ")
    except EOFError:
        # 第二道保险：真终端被关掉、或 stdin 已经到头 —— 同样当"没人点头"
        print("（键盘没了 → 按拒绝处理）")
        return False
    return 答.strip().lower() in ("y", "yes")


def 执行申请(申请: dict) -> tuple[str, bool]:
    """执行一张申请。返回 (塞回给模型的文字, 这次算不算失败)。"""
    名字 = 申请["function"]["name"]
    参数 = json.loads(申请["function"]["arguments"])

    # TODO 2 —— 闸门，三行，写在 try 前面（第 8 课那一遍，但这次守的是真账本）：
    #
    #   if 名字 in 写工具 and not 请求确认(名字, 参数):
    #       return "用户拒绝了这次写入，账本一个字没改。不要重试，先把情况说清楚。", False
    #
    # ⚠️ 必须在**调用工具之前**。写完了再问，那不叫确认，叫通知。
    # ⚠️ 拒绝也要回一条（返回的第二项是 False，不算失败）——
    #    每张申请都得有 tool 消息，少一条下一次请求直接 400（第 4 课那条）。
    # ⚠️ web/ 里没有键盘：请求确认() 抓到 EOFError 会按"拒绝"处理 ——
    #    公共网页上任何人问它记账，都写不进你的账本。这是默认值该有的样子。
    if 名字 in 写工具 and not 请求确认(名字,参数):
        return "用户拒绝了这次写入，账本一个字没改。不要重试，先把情况说清楚。", False
    try:
        return str(工具表[名字](**参数)), False
    except Exception as 错:
        return (
            f"【工具报错】{type(错).__name__}: {错}\n"
            "先别重试同样的调用，把情况说清楚。",
            True,
        )


# ================================================================ 菜单
工具表 = {
    "search_notes": 查笔记,
    "read_ledger": 查账,
    "add_expense": 记一笔,
}

菜单 = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": (
                "翻我的学习笔记（Python、SQL、Git、Agent 等课程笔记）。"
                "知识类问题都要先查它；返回正文 + 出处（文件名:行号）。"
                "一次查不准可以换个说法再查一次。只读。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要查的内容，比如 闭包 是什么、with 语句 用法",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_ledger",
            "description": "查我的记账本：花了多少、某月/某分类开销、总共支出。只读，不改账本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "月份 YYYY-MM，比如 2026-09；不填=全部"},
                    "category": {"type": "string", "description": "分类，比如 餐饮、交通；不填=全部"},
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
    "你是我的个人助手：能翻我的学习笔记，也能查、记我的账本。\n"
    "先调用 search_notes 查笔记，再决定怎么答；一次查不准就换个说法再查。\n"
    "回答里带上出处，比如 [python-learning-2026-09-01.md:99]。\n"
    "查到的块里只要有一块在讲我问的那件事，就照着它回答，别嫌不完整。\n"
    "一块都不相干（天气、做饭、别的编程语言、公司流程……），整个回答只能是 [[无答案]]，\n"
    "不许加解释、猜测或道歉。\n"
    "问花了多少钱、某月/某分类开销，调用 read_ledger，不要凭记忆算。\n"
    "我说“记一笔 / 帮我记”时，调用 add_expense，参数按我说的填。\n"
    "工具返回查不到或没写成时，照实转述，不要补编。"
)


# ================================================================ 一次问答
def 回答一个问题(
    问题: str,
    块们: list[dict],
    本子: list[dict] | None = None,
    最多几轮: int = 5,
) -> str:
    """跑完一整轮 Agent，返回它最后说的那句话（字符串，拒答时含 [[无答案]]）。

    本子 传进来就用传进来的（交互模式：跨问题记着）；
    没传就新开一本（web、体检：一问一答，互不相干）。
    """
    global 当前块们
    当前块们 = 块们
    准备好账本()

    if 本子 is None:
        本子 = [{"role": "system", "content": 规矩}]
    本子.append({"role": "user", "content": 问题})

    print(f"===== 问：{问题} =====")

    # TODO 3 —— 把这一轮跑完。照第 8 课 聊一句 的形状，六步：
    #
    #   ① 从 1 数到 最多几轮：
    #         for 轮 in range(1, 最多几轮 + 1):
    #
    #   ② 发一次，把 choices[0] 接住：
    #         回 = 问模型.发消息(本子, 菜单)          ← 第二个参数别漏：菜单
    #         回话 = 回["message"]
    #         申请们 = 回话.get("tool_calls") or []    ← 没申请时是 None，统一成 []
    #
    #   ③ 没有申请  →  它说人话了，这一句就是答案：
    #         最后 = (回话.get("content") or "").strip()
    #         本子.append(回话)                 ← 它的回答也记进本子（下一问要用）
    #         break                              ← ⚠️ 别漏。第 7 课漏了 break，每问跑满 5 轮
    #
    #   ④ 有申请  →  先把这条助理回话（带 tool_calls 的整条，原文）记进本子：
    #         本子.append(回话)
    #
    #   ⑤ 一张一张执行：
    #         for 申请 in 申请们:
    #             名字 = 申请["function"]["name"]
    #             参数 = json.loads(申请["function"]["arguments"])
    #             打印一行 【名字】参数（json.dumps(参数, ensure_ascii=False)）
    #             结果, 失败了 = 执行申请(申请)
    #             打印结果前 3 行（结果.splitlines()[:3]），失败再补一句
    #             本子.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})
    #
    #         ⚠️ tool_call_id 用 申请["id"]；一张申请一条回音，少一条下一次 400
    #
    #   ⑥ 顺序不能反：先记 assistant（带申请单），再记 tool 回音。
    #      反了 API 直接 400 —— 它找不到"你回的是哪张单"。
    #
    #   循环跑满还没 break 也不用管：最后一行的兜底会把 最后 填成一句提示。
    for 轮 in range(1,最多几轮 + 1):
        回 = 问模型.发消息(本子,菜单)
        回话 = 回["message"]
        申请们 = 回话.get("tool_calls") or []
        if not 申请们:
            最后 = (回话.get("content") or "").strip()
            本子.append(回话)
            break
        else:
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
        最后 = ""

    if not 最后:
        最后 = f"（没拿到答案：循环没跑，或转了 {最多几轮} 轮还在递申请）"

    print("-" * 50)
    print(最后.replace("[[无答案]]", "笔记里没有相关内容。"))
    return 最后


def 主程序() -> None:
    块们 = 检索.可用块()
    本子 = [{"role": "system", "content": 规矩}]   # 交互模式：一本文一本用到退出
    print("笔记问答机器人（带账本）。输入问题按回车；什么都不输直接回车就退出。")
    while True:
        问题 = input("\n问：")
        if not 问题:
            print("拜拜。")
            break
        回答一个问题(问题, 块们, 本子)


if __name__ == "__main__":
    # 命令行入口：带问题就答这一个，不带就进交互模式。
    if len(sys.argv) > 1:
        回答一个问题(" ".join(sys.argv[1:]), 检索.可用块())
    else:
        主程序()
