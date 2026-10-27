# -*- coding: utf-8 -*-
"""一个最小的 MCP 服务器 —— 手住在另一个进程里。

它不联网、不花钱。跑法：由 `_MCP演示.py` 当子进程拉起来，
也可以自己手动试（一行一条 JSON 喂进去）：

    echo {"jsonrpc":"2.0","id":1,"method":"tools/list"} | python _MCP服务器.py

规矩（MCP 的最小一套）：
- 一行一条 JSON-RPC 2.0，**stdin 收、stdout 回**
- 带 `id` 的 = 请求，必须回一条同样 `id` 的结果
- 不带 `id` 的 = 通知（比如 initialized），不回
- 日志只能写 stderr —— stdout 是协议专用的，混进一个字客户端就解析不了

三个方法就够用：
    initialize   握手（报版本、报能力）
    tools/list   要菜单
    tools/call   下单（名字 + 参数）
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

# 第 15 课：柜子在哪，由「起你的人」说了算 —— 环境变量 账本路径。
# 没给就用隔壁的演示账本（第 14 课那套自检还照旧跑）。
库 = Path(os.environ.get("账本路径") or Path(__file__).with_name("记账演示.db"))

# ══════════════════════════════════════════════════════════════════
# 菜单：格式跟 OpenAI 的 tools 几乎一样 —— inputSchema 就是 JSON Schema
# ══════════════════════════════════════════════════════════════════
工具们 = [
    {
        "name": "read_ledger",
        "description": "查我的记账本：按月份和分类统计**支出**的笔数与合计。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "月份，格式 2026-10；不填=全部"},
                "category": {"type": "string", "description": "分类，比如 餐饮；不填=全部分类"},
            },
            "required": [],
        },
    },
    {
        "name": "count_records",
        "description": "数一数记账本里一共有几笔记录。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    # 🆕 第 15 课 · TODO ③-a：在这里加第三只手 add_expense 的说明书。
    #    照上面 read_ledger 的写法抄一份，字段名一个都不能改：
    #    name / description / inputSchema（type、properties、required）
    #    ⚠️ properties 里四项跟 主程序.py 的菜单**必须对得上** ——
    #       模型是按 主程序 那份说明书填参数的，隔壁按这份收货，对不上就是「参数不对」。
    #       amount(正数) / category / date(YYYY-MM-DD) / note，required = amount、category、date
    {
        "name": "add_expense",
        "description": "记一笔支出：金额、分类、日期、备注。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "金额，必须是正数"},
                "category": {"type": "string", "description": "分类，比如 餐饮"},
                "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD"},
                "note": {"type": "string", "description": "备注，可选"},
            },
            "required": ["amount", "category", "date"],
        },
    }
]


def 查账(month: str = "", category: str = "") -> str:
    """跟第 6 课那只手一个逻辑，只是现在住在服务器这边。"""
    条件, 值 = ["kind = 'expense'"], []
    if month:
        条件.append("substr(date,1,7) = ?")
        值.append(month)
    if category:
        条件.append("category = ?")
        值.append(category)
    where = "WHERE " + " AND ".join(条件)

    连 = sqlite3.connect(库)
    try:
        行们 = 连.execute(
            f"SELECT date, category, amount, note FROM 记录 {where} ORDER BY date DESC", 值
        ).fetchall()
        合计 = 连.execute(
            f"SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM 记录 {where}", 值
        ).fetchone()
    finally:
        连.close()

    if not 行们:
        return f"没有符合条件的支出（月份={month or '全部'}，分类={category or '全部'}）。"
    明细 = "\n".join(f"{d} {c} -{a:.2f} {n}" for d, c, a, n in 行们)
    # 第一行跟 主程序.py 的 查账 说**同一句话** —— 模型和体检脚本认的是这句话，
    # 两个地方说法不一样，它会以为发生了两件事。
    return f"共 {合计[0]} 笔，合计 {合计[1]:.2f} 元。\n{明细}"


def 数记录() -> str:
    连 = sqlite3.connect(库)
    try:
        个数 = 连.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
    finally:
        连.close()
    return f"记账本里一共有 {个数} 笔记录。"


# 🆕 第 15 课 · TODO ③-b：写手也搬到隔壁来。
#    逻辑照抄 主程序.py 里的 记一笔（那边有一份能跑的），只改一件事：
#    柜子用这个文件顶上的 库，不是 主程序 的那个 账本路径。
#
#    def 记一笔(amount: float, category: str, date: str, note: str = "") -> str:
#        连 = sqlite3.connect(库)
#        try:
#            （照 主程序.py 第 118~141 行那份抄：三个校验 → INSERT → commit → 查 count）
#            ⚠️ 只改一件事：sqlite3.connect(库)，不是 账本路径
#        finally:
#            连.close()
#        ⚠️ return 也照抄那边那句「已写入 1 行：id=… 现在共 N 笔」——
#           模型认的是这段话，两个地方说法不一样会让它以为出了两回事
def 记一笔(amount: float, category: str, date: str, note: str = "") -> str:
    连 = sqlite3.connect(库)
    try:
        # 校验
        if amount <= 0:
            raise ValueError(f"金额必须是正数，传进来的是 {amount}")
        if not category:
            raise ValueError("分类不能为空")
        try:
            年, 月, 日 = map(int, date.split("-"))
            assert 1 <= 月 <= 12 and 1 <= 日 <= 31
        except Exception:
            raise ValueError(f"日期格式不对，应该是 YYYY-MM-DD，传进来的是 {date}")

        # 写入
        游 = 连.execute(
            "INSERT INTO 记录 (date, category, amount, note, kind) VALUES (?, ?, ?, ?, 'expense')",
            (date, category, amount, note),
        )
        连.commit()

        # 查总数
        个数 = 连.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
        新行id = 游.lastrowid
    finally:
        连.close()
    return f"已写入 1 行：id={新行id}，{date} {category} {amount:.2f} {note or ''}。账本现在共 {个数} 笔。"

# ══════════════════════════════════════════════════════════════════
# 🆕 第 14 课 · TODO ①：tools/call 的分发（这一课练的就是它）
#
#   收到名字和参数，调对应的本地函数，返回**一句话**（字符串）。
#   两个工具：read_ledger → 查账(**参数)；count_records → 数记录()
#
#   ⚠️ 参数是模型填的，可能来自网络 —— 只按名字白名单分发，别用 eval
#   ⚠️ 名字不认识要 raise ValueError（客户端会把它变成 isError=true）
# ══════════════════════════════════════════════════════════════════
def 执行工具(名字: str, 参数: dict) -> str:
    表 = {
        "read_ledger": 查账,
        "count_records": 数记录,
        # 🆕 第 15 课 · TODO ③-c：这里加一行，让 add_expense 能派到 记一笔
        "add_expense": 记一笔,
    }
    if 名字 not in 表:
        raise ValueError(f"没有这只手：{名字}")
    return 表[名字](**参数)


def 回(编号, 结果):
    print(json.dumps({"jsonrpc": "2.0", "id": 编号, "result": 结果}, ensure_ascii=False), flush=True)


def 回错(编号, 代码, 说法):
    print(
        json.dumps(
            {"jsonrpc": "2.0", "id": 编号, "error": {"code": 代码, "message": 说法}},
            ensure_ascii=False,
        ),
        flush=True,
    )


def 主循环() -> None:
    print("[服务器] 起来了，等指令…", file=sys.stderr, flush=True)
    for 行 in sys.stdin:
        行 = 行.strip()
        if not 行:
            continue
        消息 = json.loads(行)
        方法 = 消息.get("method")
        编号 = 消息.get("id")
        参数 = 消息.get("params") or {}

        if 编号 is None:                      # 通知，不用回
            print(f"[服务器] 收到通知 {方法}", file=sys.stderr, flush=True)
            continue

        try:
            if 方法 == "initialize":
                结果 = {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "记账本", "version": "0.1"},
                }
            elif 方法 == "tools/list":
                结果 = {"tools": 工具们}
            elif 方法 == "tools/call":
                名字 = 参数.get("name", "")
                实参 = 参数.get("arguments") or {}
                # ★ 工具自己出错 ≠ 协议出错：
                #   协议错（方法不认识）走下面的 error；
                #   工具错（名字不对、参数不对）照第 4 课塞回一段话，标 isError=True
                try:
                    文字 = 执行工具(名字, 实参)
                    结果 = {"content": [{"type": "text", "text": 文字}], "isError": False}
                except Exception as 错:
                    结果 = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"{type(错).__name__}: {错}。参数按菜单里的 inputSchema 填；"
                                f"可用的手有：{'、'.join(t['name'] for t in 工具们)}。",
                            }
                        ],
                        "isError": True,
                    }
            else:
                回错(编号, -32601, f"不认识这个方法：{方法}")
                continue
        except Exception as 错:
            回错(编号, -32603, f"{type(错).__name__}: {错}")
            continue

        回(编号, 结果)


if __name__ == "__main__":
    主循环()
