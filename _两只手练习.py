# -*- coding: utf-8 -*-
"""Agent 第 6 课练习：一张菜单挂两只手 —— 把记账本那只手也写进同一张菜单。

第 5 课菜单上只有一只手：
    search_notes(query)      翻学习笔记
所以"用不用手"是个是非题。今天菜单上有两只：

    search_notes(query)          翻学习笔记   —— 背下来的知识（第 5 课那只，今天直接给你）
    read_ledger(month, category) 翻记账柜子   —— 你自己记的数（今天要写的那只）

题目也换成一句**两件事、两个柜子**的话：
    「9 月我餐饮花了多少钱？另外闭包是什么？两个分开答。」
    账  → 在 `记账演示.db` 里（9 月餐饮合计 262.0）
    闭包 → 在 `笔记/python-learning-2026-09-01.md` 里

三个 TODO，就是「手 / 菜单 / 接线」：
    ① 查账()      —— 那只手：伸进 SQLite 柜子，把符合条件的账拼成平铺的文字
    ② 工具清单     —— 菜单上添第二条：告诉模型有这么一只手、什么时候用、要什么参数
    ③ 接线        —— 两处都要接：工具表里登记（不然 KeyError）+ 规矩里指路（不然它拿错手）

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _造演示账本.py      # 先造柜子（跑一次就够，已经跑过就不用）
    python _两只手练习.py

材料：Agent-复习速查.md「第 6 课：一张菜单挂两只手」
     演示：_两只手演示.py（先跑那个，看两张菜单差在哪）
"""

import json
import os
import sqlite3
import sys

import requests

import 检索

sys.stdout.reconfigure(errors="replace")

接口 = "https://api.deepseek.com"
聊天地址 = 接口 + "/chat/completions"
模型名 = "deepseek-flash"
钥匙名 = "DEEPSEEK_API_KEY"

取几块 = 3
这里 = os.path.dirname(os.path.abspath(__file__))
账本路径 = os.path.join(这里, "记账演示.db")

问题 = "9 月我餐饮花了多少钱？另外闭包是什么？两个分开答。"

块们 = 检索.可用块()


# ================================================================ TODO 1
def 查账(month: str = "", category: str = "") -> str:
    """模型手里新加的那只手：伸进记账柜子，把符合条件的支出拼成一段文字。

    柜子是 `记账演示.db`，表叫 `记录`，六列：
        id, amount, category, kind, date, note

    TODO 1 —— 四步：
     ① 拼条件：只查支出 → 条件是 `kind = 'expense'`；
        month 给了就再 `AND date LIKE ?`（值是 month + "%"）；
        category 给了就再 `AND category = ?`。
        ⚠️ 三个参数里，**只有值**放 `?`，值装进一个列表，**别拿 f-string 把值拼进 SQL**
           （第 3 课的老账：拼进去的字符串就是 SQL 注入）
     ② 连柜子、查：`连接.execute(f"SELECT date, category, amount, note FROM 记录 WHERE {条件} ORDER BY date", 值)`
        —— `{条件}` 里拼的是**你自己写死的几段 SQL 片段**，没有一个字来自模型，这才安全
     ③ 一行一笔拼成文字：`2026-09-02 餐饮 25.50  午饭`
     ④ 最后加一行合计：`合计：262.00（共 7 笔）`，然后 return 这段文字
        ⚠️ 别 return str(行们)。那是 Python 的元组长相，给模型看等于看乱码（第 3、5 课踩过两次）
     ⑤ 一条都没查到（比如月份写错）→ 返回一句人话：「没有符合条件的支出（月份=…，分类=…）」，
        **别让合计那一行写 0 就完事** —— 0 元和"没查到"是两回事

    已给：空柜子/空结果的处理骨架、连接怎么关
    """
    # TODO 1：把下面这行换成你的代码
    if not os.path.exists(账本路径):    
        raise SystemExit("柜子不在，先跑：python _造演示账本.py")
    连 = sqlite3.connect(账本路径)
    try:   
        条件 = ["kind = 'expense'"]
        值 = []
        if month:
            条件.append("date LIKE ?")
            值.append(month + "%")
        if category:
            条件.append("category = ?")
            值.append(category)
        where = " AND ".join(条件)
        sql = f"SELECT date, category, amount, note FROM 记录 WHERE {where} ORDER BY date"
        行们 = 连.execute(sql, 值).fetchall()
    finally:
        连.close()
    拼 = "\n".join(f"{日}  {分}  {额:.2f}  {注}" for 日, 分, 额, 注 in 行们)
    if not 行们:
        return f"没有符合条件的支出（月份={month}，分类={category}）"
    合计 = sum(额 for _, _, 额, _ in 行们)
    拼 += f"\n合计：{合计:.2f}（共 {len(行们)} 笔）"
    return 拼

# ================================================================ TODO 2
工具清单 = [
    # 第 5 课那张菜单，一条一条没动
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "这是我的学习笔记；当你不确定答案时，先调用这个工具去查笔记。返回正文 + 出处。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "你要查的内容，比如 闭包、with 语句"}
                },
                "required": ["query"],
            },
        },
    },

    # TODO 2 —— 在下面这个位置照着上面的样子，添**第二条**（注意末尾的逗号）
    #
    #   {"type": "function",
    #    "function": {
    #        "name": "read_ledger",                  ← 必须跟 工具表 里的键同名
    #        "description": "……",                   ← 写清楚三件事：
    #                                                  · 这是什么：我的个人记账本（2026 年 9 月、10 月的收支）
    #                                                  · 什么时候用：问花了多少、某月/某分类开销、总支出
    #                                                  · 返回什么：每一笔的日期/分类/金额 + 合计
    #        "parameters": {
    #            "type": "object",
    #            "properties": {
    #                "month":    {"type": "string", "description": "…… 格式 YYYY-MM，比如 2026-09；不填=全部"},
    #                "category": {"type": "string", "description": "…… 比如 餐饮、交通；不填=全部分类"},
    #            },
    #            "required": [],                     ← 两个都**可选**，空列表，不是 ["month"]
    #        },
    #    }},
    #
    #   ⚠️ description 里要说"**账本**"两个字。只说"查数据"，它分不清该翻笔记还是翻账本。
    #   ⚠️ 工具名一律英文小写加下划线，写中文直接 400。
    {
        "type": "function",
        "function": {
            "name": "read_ledger",
            "description": "这是我的个人记账本（2026 年 9 月、10 月的收支）；问花了多少、某月/某分类开销、总支出时调用。返回每一笔的日期/分类/金额 + 合计。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "…… 格式 YYYY-MM，比如 2026-09；不填=全部"},
                    "category": {"type": "string", "description": "…… 比如 餐饮、交通；不填=全部分类"},
                },
                "required": [],
            },
        },
    }
]


# ================================================================ TODO 3
def 开场白() -> list[dict]:
    """规矩（system）+ 问题（user）。第 5 课那四条保留，今天加一句指路。"""
    # TODO 3 —— 两处接线，缺一处就跑不通：
    #
    #   (a) 规矩里加一句指路（写进下面的字符串）：
    #       「问学习笔记的问题调用 search_notes；问账目数字的问题调用 read_ledger。
    #         两只手别用错：账本里没有笔记，笔记里也没有账。」
    #       —— 不写这句，它很可能拿 search_notes 去查「9 月餐饮」，
    #          翻回来一堆不相干的笔记，然后拿笔记里的日期凑一个数给你。
    #
    #   (b) 下面「工具表」字典里，登记 read_ledger → 查账（见文件末尾那个 ★ 标记）
    #       —— 菜单上写了、工具表里没登记，模型照样会递申请，
    #          但你的代码按名字查不到这只手，只能回一句【工具报错】KeyError: 'read_ledger'
    #          （这就是第 4 课说的"每条申请都得有回音"：错了也有回音，只是这个错是你的）
    return [
        {"role": "system", "content": (
            "你是我的笔记助手，只能根据笔记内容回答。\n"
            "回答之前必须先调用 search_notes；一次查不准就换个说法再查一次。\n"
            "回答里带上出处，比如 [python-learning-2026-09-01.md:99]。\n"
            "笔记里确实没有的，就明说「笔记里没有」，不要猜。\n"
            "问账目数字的问题调用 read_ledger；问花了多少、某月/某分类开销、总支出时调用。\n"
            "两只手别用错：账本里没有笔记，笔记里也没有账。"
            # ↑ 在这里接着加今天那句指路
        )},
        {"role": "user", "content": 问题},
    ]


# ================================================================ 以下全是给你的，一个字别改
def 查笔记(query: str) -> str:
    """第 5 课那只手，原样搬来。"""
    挑中的 = 检索.找相关(query, 块们, 取几块)
    return "\n\n".join(
        f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的
    )


工具表 = {
    "search_notes": 查笔记,
    "read_ledger": 查账,
    # ★ TODO 3(b)：在这里登记 read_ledger —— 一行，右边是函数名，不是字符串
}


def 执行申请(申请: dict) -> tuple[str, bool]:
    """返回 (塞回去的文字, 这一次是不是失败了)。第 4 课原样搬来。"""
    名字 = 申请["function"]["name"]
    参数 = json.loads(申请["function"]["arguments"])
    try:
        return str(工具表[名字](**参数)), False
    except Exception as 错:
        return f"【工具报错】{type(错).__name__}: {错}\n这个错误不是参数问题，重试同样的调用也没用", True


def 拿钥匙() -> str:
    钥匙 = os.environ.get(钥匙名)
    if not 钥匙:
        raise RuntimeError(f"环境变量 {钥匙名} 没拿到。先 setx 一遍，然后开一个新终端。")
    return 钥匙


def 发一次(消息们: list) -> dict:
    请求头 = {"Authorization": "Bearer " + 拿钥匙(), "Content-Type": "application/json"}
    请求体 = {"model": 模型名, "messages": 消息们, "tools": 工具清单}
    r = requests.post(聊天地址, headers=请求头, json=请求体, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]


def 主流程() -> None:
    if not os.path.exists(账本路径):
        raise SystemExit("柜子不在，先跑：python _造演示账本.py")

    最多几轮 = 5
    消息们 = 开场白()
    轮 = 0
    每只手用了几次 = {"search_notes": 0, "read_ledger": 0}
    每轮张数 = []
    失败次数 = 0
    最后一句 = ""

    print("=" * 64)
    print("问：" + 问题)
    print("=" * 64)

    while 轮 < 最多几轮:
        轮 += 1
        回 = 发一次(消息们)
        回话 = 回["message"]
        申请们 = 回话.get("tool_calls") or []
        print(f"\n---- 第 {轮} 轮：finish_reason = {回.get('finish_reason')}，申请 {len(申请们)} 张 ----")

        if not 申请们:
            最后一句 = (回话.get("content") or "").strip()
            print("它没有申请 → 循环结束")
            break

        每轮张数.append(len(申请们))
        消息们.append(回话)
        for 申请 in 申请们:
            名字 = 申请["function"]["name"]
            参数 = json.loads(申请["function"]["arguments"])
            if 名字 in 每只手用了几次:
                每只手用了几次[名字] += 1
            结果, 失败了 = 执行申请(申请)
            if 失败了:
                失败次数 += 1
            print(f"    【{名字}】{json.dumps(参数, ensure_ascii=False)}")
            for 行 in 结果.splitlines()[:3]:
                print(f"        | {行}")
            if 失败了:
                print("        ← 这次失败了")
            消息们.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})

    print()
    print("=" * 64)
    print("它最后说：")
    print(最后一句)
    print("=" * 64)
    print("数一数：")
    print(f"    转了几轮            = {轮}")
    print(f"    每轮几张申请        = {每轮张数}   ← 第一轮就 2 张 = 它一次递了两张申请")
    print(f"    search_notes 几次   = {每只手用了几次['search_notes']}")
    print(f"    read_ledger  几次   = {每只手用了几次['read_ledger']}        ← 该 ≥1；是 0 就回来看 TODO 2、TODO 3")
    print(f"    失败次数            = {失败次数}        ← 该是 0；是 1 且写着 KeyError，就是 TODO 3(b) 没登记")
    print(f"    role=tool 条数      = {sum(1 for m in 消息们 if m.get('role') == 'tool')}        ← 必须等于两张申请加起来")
    print()
    print("对照答案：")
    print("    · 账那半：答案里该出现 262（9 月餐饮合计），并且说清共 7 笔")
    print("    · 笔记那半：该说到「内层函数 + 外层变量」，出处 python-learning-2026-09-01")
    print("    · 它拿去查账的参数该是 month=2026-09、category=餐饮 —— 你没告诉它这个数，是它自己从问句里拆的")


if __name__ == "__main__":
    主流程()
