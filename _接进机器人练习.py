# -*- coding: utf-8 -*-
"""Agent 第 5 课练习：把「检索」接成一只工具，装进你自己的问答机器人。

老机器人（主程序.py）是这么转的：
    问题 ──► 检索一次（写死 top 3）──► 拼进提示词 ──► 模型答
"查什么"是你写死的，"查几次"永远是 1 次。

今天把它换成：
    问题 ──► 模型说"我要查这个" ──► 你替它翻笔记 ──► 它看着结果决定还要不要翻 ──► 答
"查什么、查几次"都还给模型。你只管把**手**给它、把**菜单**印好、把**规矩**立下。

已经能跑的东西全都给你了（前四课的零件，一个字没改）：
    · 发请求、while 循环、执行申请、塞 role=tool 消息   ← 第 2、4 课的骨架
    · 工具表、执行申请 里那个 try/except                ← 第 4 课
    · 检索.找相关(问题, 块们, 几块)                     ← 你自己项目里的那只柜子

三个 TODO，一层一层往上：
    ① 查笔记()   —— 那只手：拿一句话去柜子里翻，把翻到的段落拼成一段带出处的文字
    ② 工具清单   —— 那张菜单：告诉模型有这么一只手、什么时候用、要什么参数
    ③ 规矩       —— 系统消息（system）：先查再答 / 查不准就换词再查 / 带着出处答 / 没有就说没有
                    （规矩不写，它可能一张申请都不发，直接编一段给你）

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _接进机器人练习.py

⚠️ 现在直接跑也能跑完 —— 但它一张申请都不会递，直接凭记忆给你编一段答案
   （`with` 那段它甚至讲成了 JavaScript 的 `with`，因为笔记它根本没见过）。
   这就是「坑二」，不是你的 bug：工具清单空着 = 它不知道有这么一只手。
   不填 TODO 的样子存了一份：`_不填TODO长这样_输出.txt`

材料：Agent-复习速查.md「第 5 课：把检索接成工具」
     演示：_接工具演示.py（先跑那个，看两种写法差在哪）
"""

import json
import os
import sys

import requests

import 检索

sys.stdout.reconfigure(errors="replace")

接口 = "https://api.deepseek.com"
聊天地址 = 接口 + "/chat/completions"
模型名 = "deepseek-flash"
钥匙名 = "DEEPSEEK_API_KEY"

取几块 = 3

# ⚠️ 这一问故意问**两件事、两篇笔记**：
#    闭包在 python-learning-2026-09-01.md
#    with 在 python-learning-2026-08-14.md
#    一句话查一次，多半只捞得着其中一边 —— 这就是要"查两次"的理由
问题 = "闭包是什么？另外 with 语句怎么用？两个分开答。"

块们 = 检索.可用块()


# ================================================================ TODO 1
def 查笔记(query: str) -> str:
    """模型手里那只手：拿一句话去柜子里翻笔记，把翻到的段落拼成一段文字塞回去。"""
    # TODO 1 —— 两行：
    #
    #   ① 翻：挑中的 = 检索.找相关(query, 块们, 取几块)
    #      （跟你项目里 主程序.py 调用它时一模一样，只是第一参数从"问题"变成了 query）
    #
    #   ② 拼：每块拼成下面这个形状，块和块之间空一行
    #
    #         [python-learning-2026-09-01.md:99 ### 二、闭包]
    #         （这块的正文）
    #
    #      开头那对方括号 = **出处**。模型答完会把它抄进答案里，你才有办法核对
    #      "这句话到底是从哪块笔记里来的"。没有出处，它答得再像也没法查。
    #
    #      提示：一行列表推导式就够
    #          return "\n\n".join(f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的)
    #      或者先写 [ ... for 块 in 挑中的] 存成一个列表，再 "\n\n".join(...)
    #
    #   ⚠️ 别 return str(挑中的) —— 那是 Python 的字典长相（单引号、逗号、大括号），
    #      给模型看等于给它看乱码。第 3 课就踩过这个。
    挑中的 = 检索.找相关(query, 块们, 取几块)
    return "\n\n".join(f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的)  


# ================================================================ TODO 2
工具清单 = [
    # TODO 2 —— 照着第 3 课那张清单的样子，写一条。四层别数错：
    #
    #   {"type": "function",
    #    "function": {
    #        "name": "search_notes",              ← 必须跟 工具表 里的键同名
    #        "description": "……",                ← 写清楚：这是我的学习笔记；什么时候该用；
    #                                                返回什么（正文 + 出处）。这句话决定它会不会用、怎么用
    #        "parameters": {
    #            "type": "object",
    #            "properties": {
    #                "query": {"type": "string", "description": "……"}   ← 告诉它填什么、举两个例子
    #            },
    #            "required": ["query"],            ← 这次是必填，方括号里就这一个词
    #        },
    #    }},
    #
    #   ⚠️ 工具名一律英文小写加下划线，写中文直接 400。
    #   ⚠️ description 里别说"查询数据库"这种含糊话，要说"我的学习笔记"，它才知道该问什么。
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
        }   
    }
]


# ================================================================ TODO 3
def 开场白() -> list[dict]:
    """这一次对话的消息列表：规矩（system）+ 问题（user）。"""
    # TODO 3 —— 系统消息里立四条规矩，一条一句，写进下面这个字符串：
    #
    #   ① 你是谁 + 只能根据笔记回答       → "你是我的笔记助手，只能根据笔记内容回答。"
    #   ② 回答之前必须先查，查不准就换词再查 → "回答之前必须先调用 search_notes；
    #                                          一次查不准就换个说法再查一次。"
    #   ③ 答的时候带出处                   → "回答里带上出处，比如 [python-learning-2026-09-01.md:99]。"
    #   ④ 笔记里真没有就明说               → "笔记里确实没有的，就明说「笔记里没有」，不要猜。"
    #
    #   为什么要系统消息？—— 用户那条消息里只有问题，没有"你该怎么干活"。
    #   system 是每次请求都排在最前面的那张纸，模型每一轮都会重读它。
    #
    #   ⚠️ ②这条最值钱：不写它，模型经常"觉得自己知道"，一张申请都不发就直接答。
    #      跑完看「检索次数」那个数 —— 少于 2，先回来看这条规矩。
    return [
        {"role": "system", "content": "你是我的笔记助手，只能根据笔记内容回答。\n回答之前必须先调用 search_notes；一次查不准就换个说法再查一次。\n回答里带上出处，比如 [python-learning-2026-09-01.md:99]。\n笔记里确实没有的，就明说「笔记里没有」，不要猜。"},   # ← 把四条规矩写进这个空字符串（用 """三个引号换行写）
        {"role": "user", "content": 问题},
    ]


# ================================================================ 以下全是给你的，一个字别改
工具表 = {
    "search_notes": 查笔记,
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
    最多几轮 = 5
    消息们 = 开场白()
    轮 = 请求次数 = 检索次数 = 0
    查询词们 = []
    最后一句 = ""

    print("=" * 64)
    print("问：" + 问题)
    print("=" * 64)

    while 轮 < 最多几轮:
        轮 += 1
        请求次数 += 1
        回 = 发一次(消息们)
        回话 = 回["message"]
        申请们 = 回话.get("tool_calls") or []
        print(f"\n---- 第 {轮} 轮：finish_reason = {回.get('finish_reason')}，申请 {len(申请们)} 张 ----")

        if not 申请们:
            最后一句 = (回话.get("content") or "").strip()
            print("它没有申请 → 循环结束")
            break

        消息们.append(回话)
        for 申请 in 申请们:
            参数 = json.loads(申请["function"]["arguments"])
            结果, 失败了 = 执行申请(申请)
            检索次数 += 1
            if "query" in 参数:
                查询词们.append(参数["query"])
            print(f"    申请单：{申请['function']['name']}({json.dumps(参数, ensure_ascii=False)})")
            print("    塞回去的话（前两行）：")
            for 行 in 结果.splitlines()[:2]:
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
    print(f"    请求发了几次        = {请求次数}")
    print(f"    检索次数（工具跑了） = {检索次数}        ← 该是 2 或 3：两个话题各一次，它觉得不够会自己再补一次")
    print(f"    它拿去查的词        = {查询词们}")
    print(f"    role=tool 条数      = {sum(1 for m in 消息们 if m.get('role') == 'tool')}        ← 必须等于「检索次数」")
    print()
    print("对照答案：")
    print("    · 最终答案里该有 python-learning-2026-09-01（闭包）和 python-learning-2026-08-14（with）两处出处")
    print("    · 闭包那段该说到「内层函数 + 外面那个变量」；with 那段该说到「自动 close / 是 try/finally 的语法糖」")
    print("    · 答案里不该出现「[[无答案]]」")


if __name__ == "__main__":
    主流程()
