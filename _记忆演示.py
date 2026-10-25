# -*- coding: utf-8 -*-
"""第 7 课演示：它不记事，记事的是你手里那本本子。

连着问三句：

    ① 9 月我餐饮花了多少钱？
    ② 那 10 月呢？
    ③ 它们一共多少？

第 ② 句里**没有"餐饮"两个字**。缺的那半句不在话里，在上一句里。
谁来把它接上？不是模型 —— 是你在第二个请求里**多带了几条消息**。

两种写法各跑一遍：

    场景甲「每次从零」：每一问都只发 [规矩, 这一句]   —— 本子用完就扔
    场景乙「带着本子」：一个 本子 列表从头带到尾        —— 本子越写越厚

菜单上只有一只手 read_ledger（第 6 课那只，原样搬来）。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _造演示账本.py      # 先造柜子（跑一次就够）
    python _记忆演示.py

⚠️ 只要一个环境变量：DEEPSEEK_API_KEY
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

问句们 = [
    "9 月我餐饮花了多少钱？",
    "那 10 月呢？",
    "它们一共多少？",
]


# ================================================================ 那只手（第 6 课原样）
def 查账(month: str = "", category: str = "") -> str:
    """伸进记账柜子，把符合条件的支出拼成一行一笔，最后给合计。"""
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


工具表 = {"read_ledger": 查账}

菜单 = [
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
    "你是我的记账助手。\n"
    "问数字就调用 read_ledger，不要凭印象算。\n"
    "回答里带上具体金额。查不到就明说，不要猜。"
)


def 发请求(消息们: list) -> dict:
    钥匙 = os.environ.get("DEEPSEEK_API_KEY")
    if not 钥匙:
        raise SystemExit("没拿到 DEEPSEEK_API_KEY，先设环境变量、重开终端。")
    r = requests.post(
        聊天地址,
        headers={"Authorization": "Bearer " + 钥匙, "Content-Type": "application/json"},
        json={"model": 模型名, "messages": 消息们, "tools": 菜单},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]


# ================================================================ 问一句
def 问一句(本子: list, 话: str, 最多几轮: int = 5) -> dict:
    """往本子后面接着问一句。

    本子进来时是什么样，决定它这一句"能看见什么"：
        场景甲：本子只有 [规矩]  → 它看见的只有这一句
        场景乙：本子带着前面所有来回 → 它看见"9 月""餐饮"这些字

    本子出去时变厚了：多了这一句 user、它回的 assistant、还有 tool 回音。
    """
    print(f"\n本子里现在有 {len(本子)} 条 —— 这一句发给它之前，它只能看见这 {len(本子)} 条")

    本子.append({"role": "user", "content": 话})

    递了 = []
    答案 = ""
    for 轮 in range(1, 最多几轮 + 1):
        选 = 发请求(本子)
        回话 = 选["message"]
        申请们 = 回话.get("tool_calls") or []

        if not 申请们:
            答案 = (回话.get("content") or "").strip()
            # 把它的最后一句话也记进本子：下一句还得靠它
            本子.append(回话)
            break

        本子.append(回话)
        for 申请 in 申请们:
            名字 = 申请["function"]["name"]
            参数 = json.loads(申请["function"]["arguments"])
            递了.append((名字, 参数))
            结果 = 工具表[名字](**参数)
            本子.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})
    else:
        答案 = "（跑满轮数还没收口）"

    print(f"    它递的申请：{json.dumps(递了, ensure_ascii=False)}")
    print("    它说：")
    for 行 in 答案.splitlines():
        print("        " + 行)
    print(f"    问完这一句，本子变成 {len(本子)} 条")
    return {"答案": 答案, "递了": 递了, "本子条数": len(本子)}


def 主流程() -> None:
    if not os.path.exists(账本路径):
        raise SystemExit("柜子不在，先跑：python _造演示账本.py")

    print("连着问三句：")
    for i, 话 in enumerate(问句们, 1):
        print(f"    {i}. {话}")

    # ---------------------------------------------------------- 场景甲
    print("\n" + "█" * 64)
    print("█ 场景甲「每次从零」：每一问都只带 [规矩, 这一句]")
    print("█" * 64)
    甲的结果们 = []
    for 话 in 问句们:
        本子 = [{"role": "system", "content": 规矩}]   # ← 用完就扔，下一问重新开一本
        print(f"\n──── 问：{话}")
        甲的结果们.append(问一句(本子, 话))

    # ---------------------------------------------------------- 场景乙
    print("\n" + "█" * 64)
    print("█ 场景乙「带着本子」：同一个 本子 从头带到尾")
    print("█" * 64)
    本子 = [{"role": "system", "content": 规矩}]
    乙的结果们 = []
    乙的本子条数 = []
    for 话 in 问句们:
        print(f"\n──── 问：{话}")
        结果 = 问一句(本子, 话)
        乙的结果们.append(结果)
        乙的本子条数.append(结果["本子条数"])

    # ---------------------------------------------------------- 数一数
    print("\n" + "=" * 64)
    print("数一数，差别在哪")
    print("=" * 64)

    def 答上了(答案: str, 数: str) -> bool:
        return 数 in 答案

    def 填了啥(结果: dict) -> str:
        """第 2 问它填给 read_ledger 的参数，长什么样。"""
        if not 结果["递了"]:
            return "（没递申请）"
        return json.dumps(结果["递了"][0][1], ensure_ascii=False)

    print("\n第 ② 句「那 10 月呢？」—— 这一句里没有“餐饮”两个字，也没有“9 月”")
    print(f"    甲（从零）：它填的参数 = {填了啥(甲的结果们[1])}   ← 只填了月份，“餐饮”丢了")
    print(f"                 它答的是 10 月全部支出（2889.50），不是餐饮：{'含 2889.5' if 答上了(甲的结果们[1]['答案'], '2889.5') else '没含 2889.5'}")
    print(f"    乙（带本子）：它填的参数 = {填了啥(乙的结果们[1])}   ← 月份 + 分类，缺的半句补上了")
    print(f"                 它答的是 10 月餐饮（242.50）：{'含 242.5' if 答上了(乙的结果们[1]['答案'], '242.5') else '没含 242.5'}")
    print("    ⚠️ 甲那份答案里其实也能翻到 242.50 —— 但它把整张表都搬回来了，那是顺带列出来的分类小计。")
    print("       数字碰巧在，问题没答对。尺子量“它填了什么参数”，不量“答案里有没有这个数”。")

    print("\n第 ③ 句「它们一共多少？」")
    print(f"    甲（从零）：答 504.5（262 + 242.5）吗？ {'是' if 答上了(甲的结果们[2]['答案'], '504.5') else '不是'}")
    print(f"    乙（带本子）：答 504.5（262 + 242.5）吗？ {'是' if 答上了(乙的结果们[2]['答案'], '504.5') else '不是'}")
    print(f"    “它们”指谁？甲看不见上一句，只能反问；乙的本子里躺着前两问，直接算。")

    print("\n本子厚度（乙）：", " → ".join(str(条) for 条 in 乙的本子条数))
    print("    每问一句，本子就厚一截：你说的 + 它说的 + 工具回的音，全都留着。")

    print("\n" + "-" * 64)
    print("一句话：模型没有记性 —— 每次请求它只看见 messages 里装的东西。")
    print("甲那边它没乱编：不知道问哪个分类，就去查了 10 月的全部支出。")
    print("数是真的，问题是错的 —— 缺的那半句，只有你的本子上有。")


if __name__ == "__main__":
    主流程()
