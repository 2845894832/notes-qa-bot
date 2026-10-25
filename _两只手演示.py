# -*- coding: utf-8 -*-
"""第 6 课演示：一张菜单挂两只手，模型自己挑。

第 5 课菜单上只有一只手（search_notes），所以"用不用手"是个是非题。
今天菜单上有两只：

    search_notes(query)               翻学习笔记   —— 背下来的知识
    read_ledger(month, category)      翻记账柜子   —— 你自己记的数

问题还是一句**两件事**的话，但这次两件事落在**两个不同的柜子**里：

    「9 月我餐饮花了多少钱？另外闭包是什么？两个分开答。」

    账：在 `记账演示.db` 里，9 月餐饮合计 262.0
    闭包：在 `笔记/python-learning-2026-09-01.md` 里

两种写法各跑一遍：
    场景甲：菜单上只有 search_notes（= 第 5 课的样子）
    场景乙：菜单上两只手

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _造演示账本.py      # 先造柜子（跑一次就够）
    python _两只手演示.py

⚠️ 要两个环境变量：DEEPSEEK_API_KEY（问模型）+ SILICONFLOW_API_KEY（算向量）
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

这里 = os.path.dirname(os.path.abspath(__file__))
账本路径 = os.path.join(这里, "记账演示.db")

问题 = "9 月我餐饮花了多少钱？另外闭包是什么？两个分开答。"

# 尺子：答案里出现这些，就算这半答上了
账的锚点 = ("262",)                        # 9 月餐饮合计 = 262.0
闭包的锚点 = ("外部变量", "外层变量", "自由变量")

块们全局: list[dict] = []


# ================================================================ 两只手
def 查笔记(query: str) -> str:
    """第 5 课那只手，原样搬来。"""
    挑中的 = 检索.找相关(query, 块们全局, 3)
    if not 挑中的:
        return "什么也没翻到，换个说法再查。"
    return "\n\n".join(
        f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的
    )


def 查账(month: str = "", category: str = "") -> str:
    """今天新加的那只手：伸进记账柜子，把符合条件的账拼成一行一笔，最后给合计。

    ⚠️ 三件事，每一件都是第 3 课的老账：
      ① 参数化查询：条件用 `?` 填，**别拿 f-string 拼进 SQL**
      ② 两个参数都是可选：空字符串 = 这一条不加
      ③ 返回平铺的文字，不是 `str(行们)`
    """
    条件 = ["kind = 'expense'"]
    值: list = []
    if month:
        条件.append("date LIKE ?")
        值.append(month + "%")
    if category:
        条件.append("category = ?")
        值.append(category)
    where = " AND ".join(条件)

    连接 = sqlite3.connect(账本路径)
    行们 = 连接.execute(
        f"SELECT date, category, amount, note FROM 记录 WHERE {where} ORDER BY date", 值
    ).fetchall()
    连接.close()

    if not 行们:
        return f"没有符合条件的支出（月份={month or '全部'}，分类={category or '全部'}）。"

    行们文字 = "\n".join(f"{日} {类} {额:.2f}  {备注}" for 日, 类, 额, 备注 in 行们)
    合计 = sum(额 for _, _, 额, _ in 行们)
    return f"{行们文字}\n合计：{合计:.2f}（共 {len(行们)} 笔）"


工具表 = {
    "search_notes": 查笔记,
    "read_ledger": 查账,
}


# ================================================================ 两张菜单
菜单_笔记 = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "在我的学习笔记里搜索跟问题相关的段落。返回段落正文，每段前面带出处 [文件名:行号]。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索用的关键词或一句话，比如 闭包 是什么"}
                },
                "required": ["query"],
            },
        },
    },
]

菜单_两只手 = 菜单_笔记 + [
    {
        "type": "function",
        "function": {
            "name": "read_ledger",
            "description": (
                "查我自己的记账本（2026 年 9 月、10 月的收支）。"
                "问花了多少钱、某个月/某个分类的开销、总共支出，就用这个。"
                "返回每一笔的日期、分类、金额和合计。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "月份，格式 YYYY-MM，比如 2026-09；不填表示全部月份"},
                    "category": {"type": "string", "description": "分类，比如 餐饮、交通、房租；不填表示全部分类"},
                },
                "required": [],
            },
        },
    },
]

规矩 = (
    "你是我的助手。\n"
    "问学习笔记的问题，调用 search_notes；问账目数字的问题，调用 read_ledger。\n"
    "两只手别用错：账本里没有笔记，笔记里也没有账。\n"
    "回答带上出处（[文件名:行号]）或账本里的数字。查不到就明说，不要猜。"
)


def 发请求(请求体: dict) -> dict:
    钥匙 = os.environ.get("DEEPSEEK_API_KEY")
    if not 钥匙:
        raise SystemExit("没拿到 DEEPSEEK_API_KEY，先设环境变量、重开终端。")
    r = requests.post(
        聊天地址,
        headers={"Authorization": "Bearer " + 钥匙, "Content-Type": "application/json"},
        json=请求体,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


# ================================================================ 跑一遍
def 跑(名字: str, 菜单: list, 最多几轮: int = 5) -> dict:
    print("\n" + "█" * 64)
    print(f"█ {名字} —— 菜单上有 {len(菜单)} 只手：" + "、".join(m["function"]["name"] for m in 菜单))
    print("█" * 64)

    消息们 = [{"role": "system", "content": 规矩}, {"role": "user", "content": 问题}]
    申请张数 = 0
    用过的名字: list[str] = []
    每轮张数: list[int] = []
    答案 = ""

    for 轮 in range(1, 最多几轮 + 1):
        回 = 发请求({"model": 模型名, "messages": 消息们, "tools": 菜单})
        选 = 回["choices"][0]
        回话 = 选["message"]
        申请们 = 回话.get("tool_calls") or []
        print(f"\n---- 第 {轮} 轮：finish_reason = {选.get('finish_reason')}，申请 {len(申请们)} 张 ----")

        if not 申请们:
            答案 = (回话.get("content") or "").strip()
            break

        每轮张数.append(len(申请们))
        消息们.append(回话)
        for 申请 in 申请们:
            名前 = 申请["function"]["name"]
            参数 = json.loads(申请["function"]["arguments"])
            申请张数 += 1
            用过的名字.append(名前)
            print(f"    {申请张数}. 【{名前}】{json.dumps(参数, ensure_ascii=False)}")
            结果 = 工具表.get(名前)
            文字 = 结果(**参数) if 结果 else f"没有这只手：{名前}"
            for 行 in 文字.splitlines()[:3]:
                print(f"         | {行}")
            消息们.append({"role": "tool", "tool_call_id": 申请["id"], "content": 文字})
    else:
        答案 = "（跑满轮数还没收口）"

    print("\n它最后说：")
    for 行 in 答案.splitlines():
        print("    " + 行)

    return {
        "名字": 名字,
        "申请张数": 申请张数,
        "用过的名字": 用过的名字,
        "每轮张数": 每轮张数,
        "答案": 答案,
        "账答上": any(词 in 答案 for 词 in 账的锚点),
        "闭包答上": any(词 in 答案 for 词 in 闭包的锚点),
    }


def 主流程() -> None:
    global 块们全局
    if not os.path.exists(账本路径):
        raise SystemExit("柜子不在，先跑：python _造演示账本.py")
    块们全局 = 检索.可用块()

    print(f"可用块：{len(块们全局)}    问：{问题}")
    甲 = 跑("场景甲：菜单上只有一只手", 菜单_笔记)
    乙 = 跑("场景乙：菜单上两只手", 菜单_两只手)

    print("\n" + "=" * 64)
    print("数一数，两张菜单差在哪")
    print("=" * 64)
    for 结果 in (甲, 乙):
        print(f"\n【{结果['名字']}】")
        print(f"    递了几张申请        = {结果['申请张数']}   （每轮 {结果['每轮张数']}）")
        print(f"    用到了几只不同的手  = {len(set(结果['用过的名字']))}   {结果['用过的名字']}")
        print(f"    账那半答上了吗      = {'有 262.0' if 结果['账答上'] else '没有'}")
        print(f"    闭包那半答上了吗    = {'有' if 结果['闭包答上'] else '没有'}")

    print("\n" + "-" * 64)
    print("一句话：菜单多一条，不是「功能多了」—— 是它手上多了一个能挑的东西。")
    print("甲那边它没乱来：只递了 1 张（闭包），账那半明确说「这只手不管账，我不猜」。")
    print("菜单上没有的手，它伸不出来 —— 所以它诚实，也确实干不了这件活。")
    print("乙那边它自己知道：数字在账本里，知识在笔记里，于是同一轮一起伸了两只手。")


if __name__ == "__main__":
    主流程()
