# -*- coding: utf-8 -*-
"""Agent 第 7 课练习：它不记事 —— 记事的是你手里那本本子。

还是那三句：

    ① 9 月我餐饮花了多少钱？
    ② 那 10 月呢？          ← 这一句里没有“餐饮”
    ③ 它们一共多少？         ← “它们”是谁，只有本子上写着

第 ① 课到第 ⑥ 课，每一问都是现拼一份 [规矩, 这一句] 发出去，问完就扔。
今天改成：一本本子从头带到尾，每问一句就往后写几行。

三个 TODO：
    ① 开场白()   —— 新本子：开头只有规矩，**没有用户的问题**
    ② 问一句()   —— 三个地方往本子里写：它回的整条（两处）、每条工具回音
    ③ 裁本子()   —— 本子太厚要裁，但**按“用户的话”切**，别把工具回音和它的申请拆散

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _造演示账本.py      # 柜子（跑过一次就行）
    python _记忆练习.py

材料：Agent-复习速查.md「第 7 课：会话记忆」
     演示：_记忆演示.py（先跑那个，看“从零”和“带本子”差在哪）
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
钥匙名 = "DEEPSEEK_API_KEY"

这里 = os.path.dirname(os.path.abspath(__file__))
账本路径 = os.path.join(这里, "记账演示.db")

问句们 = [
    "9 月我餐饮花了多少钱？",
    "那 10 月呢？",
    "它们一共多少？",
]


# ================================================================ TODO 1
规矩 = (
    "你是我的记账助手。\n"
    "问数字就调用 read_ledger，不要凭印象算。\n"
    "回答里带上具体金额。查不到就明说，不要猜。"
)


def 开场白() -> list[dict]:
    """开一本**新本子**。

    第 1~6 课的 `开场白()` 长这样：
        return [{"role": "system", "content": 规矩},
                {"role": "user",   "content": 问题}]
    —— 问题是一次就写死的，因为那时候只问一句。

    今天问题是一句一句加上来的，所以这里**只放规矩**（一条 system）。
    用户的话由 问一句() 往里接。

    TODO 1：返回一本新本子 —— 一个列表，里面只有那条 system。
            ⚠️ system 只放一次。每一问都往本子里再塞一条 system，它会被一堆规矩夹住。
    """
    return [{"role": "system", "content": 规矩},
            ]  


# ================================================================ TODO 2
def 问一句(本子: list[dict], 话: str, 最多几轮: int = 5) -> str:
    """把「话」接在本子后面问出去；问完，本子变厚。返回它最后说的那句。"""
    本子.append({"role": "user", "content": 话})

    答案 = ""
    for 轮 in range(1, 最多几轮 + 1):
        选 = 发一次(本子)          # ← 发出去的是**整本本子**，不是只有这一句
        回话 = 选["message"]
        申请们 = 回话.get("tool_calls") or []
        print(f"    ---- 第 {轮} 轮：finish_reason = {选.get('finish_reason')}，申请 {len(申请们)} 张 ----")

        if not 申请们:
            答案 = (回话.get("content") or "").strip()
            # ---------------------------------------------------- TODO 2 (a)
            # 它说完了。把「它回的这条消息」接进本子 —— 下一问还得靠它记住这一问聊了啥。
            # ⚠️ 接的是 回话 这**一整条**，不是回话["content"] 那一句话。
            #    这里有 content 就够；但下面那些带 tool_calls 的 assistant 消息，
            #    丢掉的正是 tool_calls 这个键。
            # 本子.append(回话)        ← 换成你的
            本子.append((回话))
            break       

        # -------------------------------------------------------- TODO 2 (b)
        # 把 回话 一整条接进本子。它带着 tool_calls，是下面那些 tool 回音的“主”。
        # ⚠️ 这一条最容易漏 —— 少了它，下一问里那几条 tool 消息就成了“没主的回音”，
        #    下一次请求直接 400。数字上的症状：每问只多 2 条（只有 user + 最后那句），不是 4~5 条。
        # 本子.append(回话)        ← 换成你的
        本子.append(回话)
        for 申请 in 申请们:
            名字 = 申请["function"]["name"]
            参数 = json.loads(申请["function"]["arguments"])
            结果 = 工具表[名字](**参数)
            print(f"    【{名字}】{json.dumps(参数, ensure_ascii=False)}")
            for 行 in 结果.splitlines()[:3]:
                print("        | " + 行)

            # 第二件事：把这一条回音接进本子。
            # 三个键一个都不能少：role / tool_call_id / content。
            # ---------------------------------------------------- TODO 2 (c)
            本子.append({"role": "tool", "tool_call_id": 申请["id"], "content":
                结果})
    else:
        答案 = "（跑满轮数还没收口）"

    return 答案


# ================================================================ TODO 3
def 裁本子(本子: list[dict], 保留几轮: int = 2) -> list[dict]:
    """本子越写越厚，每一问都得把整本再发一遍 —— 又贵又容易超长。砍掉最前面的。

    ⚠️ 不能按“条数”随便切：`assistant(tool_calls)` 和它的 `tool` 回音是一对，
       切在中间，剩下那条 tool 找不到“主”，下一次请求直接 400。

    最稳的切法：**按用户的话切**。
        第一条 system 永远留；
        找出本子里所有 role == "user" 的位置；
        从倒数第 保留几轮 条 user 那里开始，一直留到末尾。

    这样切出来的每一段都是完整的：user → assistant(申请) → tool(回音) → assistant(回答)。

    TODO 3：实现它，返回一个新列表，别改传进来的那个。

    提示：
        下标们 = [i for i, 条 in enumerate(本子) if 条.get("role") == "user"]
        —— 如果 len(下标们) <= 保留几轮，说明不用裁，原样返回
        —— 否则 起点 = 下标们[-保留几轮]，返回 [本子[0]] + 本子[起点:]
    """
    下标们 = [i for i, 条 in enumerate(本子) if 条.get("role") == "user"]
    if len(下标们) <= 保留几轮:
        return 本子
    else:
        起点 = 下标们[-保留几轮]
        return [本子[0]] + 本子[起点:]



# ================================================================ 以下全是给你的，一个字别改
def 查账(month: str = "", category: str = "") -> str:
    """第 6 课那只手，原样搬来。"""
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


def 主流程() -> None:
    if not os.path.exists(账本路径):
        raise SystemExit("柜子不在，先跑：python _造演示账本.py")

    本子 = 开场白()
    if not 本子:
        raise SystemExit("TODO 1 还没填：开场白() 返回的是一本空本子。")

    print("=" * 64)
    print("同一个本子，连着问三句")
    print("=" * 64)

    厚度 = []
    for 话 in 问句们:
        print(f"\n──── 问：{话}      （本子里现在 {len(本子)} 条）")
        答 = 问一句(本子, 话)
        print("它说：")
        for 行 in 答.splitlines():
            print("    " + 行)
        厚度.append(len(本子))
        print(f"→ 问完，本子 {len(本子)} 条")

    print("\n" + "=" * 64)
    print("数一数")
    print("=" * 64)
    print(f"    本子厚度（每问完一句） = {厚度}        ← 该是 5 起步，之后每问多 4~5 条（一次递几张申请不一定）；只多 2 条 = assistant/tool 没接进来")
    print(f"    本子里 role 的排法     = {[m.get('role') for m in 本子]}")

    print("\n第 ② 句「那 10 月呢？」—— 这一句里没有“餐饮”")
    带申请的 = [m for m in 本子 if m.get("role") == "assistant" and m.get("tool_calls")]
    if len(带申请的) >= 2:
        参数 = json.loads(带申请的[1]["tool_calls"][0]["function"]["arguments"])
        print(f"    它第二次填的参数 = {json.dumps(参数, ensure_ascii=False)}")
        print("    ← 该同时有 month=2026-10 和 category=餐饮。只填了 month，就是本子里没接上第 ① 问。")
    else:
        print(f"    带申请的 assistant 消息只有 {len(带申请的)} 条 —— 它可能直接拿本子里的数算了，看看答案对不对")

    print("\n第 ③ 句「它们一共多少？」")
    print(f"    它最后说：{答}")
    print("    ← 该是 504.50（262.00 + 242.50）。说“它们指什么”/列全部支出，就是前面没记住。")

    # ---------------------------------------------------------- 裁本子
    print("\n" + "=" * 64)
    print("本子太厚，裁到最近 2 轮，再问第 ④ 句")
    print("=" * 64)
    新本子 = 裁本子(本子, 2)
    print(f"    裁之前 {len(本子)} 条 → 裁之后 {len(新本子)} 条（第一条 system 还在）")
    print(f"    裁完的 role 排法 = {[m.get('role') for m in 新本子]}")
    print("    ← 该是 system + 两整段（每段 user…assistant）。要是第一条不是 system，或者开头是 tool，就切散了。")

    print("\n──── 问：我最开始问的是哪个月？")
    答4 = 问一句(新本子, "我最开始问的是哪个月？")
    print("它说：")
    for 行 in 答4.splitlines():
        print("    " + 行)
    print("    ← 它该明说「我能看到的最早一条是 那 10 月呢」，然后只能猜。—— 猜出来的不算记性。")


if __name__ == "__main__":
    主流程()
