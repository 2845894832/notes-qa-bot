# -*- coding: utf-8 -*-
"""第 5 课演示：把「检索」接成一只工具，机器人从"查一次就答"变成"自己决定查几次"。

老机器人（主程序.py 现在的样子）：
    问题 ──► 检索一次（固定 top 3）──► 拼进提示词 ──► 模型答
    检索是**必经之路**，跑在模型前面，模型对"查什么"一个字都说不上。

新机器人（今天要做的）：
    问题 ──► 模型自己说"我要查这个" ──► 你替它查 ──► 它看着结果决定还要不要查 ──► 答
    检索变成**模型手里的一只手**，它想查几次、拿什么词去查，都是它自己定的。

这个脚本跑同一个问题，两种写法各跑一遍，最后把差别数出来。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _接工具演示.py

⚠️ 要两个环境变量：DEEPSEEK_API_KEY（问模型）+ SILICONFLOW_API_KEY（算向量）
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


# 这道题故意选成**两个话题、两篇笔记**：闭包在 09-01，with 在 08-14。
问题 = "闭包是什么？另外 with 语句怎么用？两个分开答。"

# 尺子：标准答案表里的「对的块」（第 1 题 + 第 3 题）
对的块 = {
    "python-learning-2026-09-01.md 行99",   # 闭包
    "python-learning-2026-08-14.md 行43",   # with
    "python-learning-2026-08-14.md 行55",   # with
}
# 挡在尺子前面的一步：得先知道"这话算不算答上了"
话题锚点 = {
    "闭包": ("外部变量", "外层变量", "自由变量"),
    "with": ("close", "关闭", "finally"),
}


def 取块们() -> list[dict]:
    return 检索.可用块()


def 块的钥匙(块: dict) -> str:
    return f"{块['文件']} 行{块['行号']}"


def 块文字(块: dict) -> str:
    """一块笔记 → 塞给模型的那段字。**开头必须有出处**，不然它答完你没法核对。"""
    return f"[{块的钥匙(块)} {块['标题']}]\n{块['正文']}"


# ================================================================ 场景甲：老写法
def 场景甲(块们: list[dict]) -> dict:
    print("█" * 64)
    print("█ 场景甲：老写法 —— 先检索，再问（检索跑在模型前面，只跑一次）")
    print("█" * 64)

    挑中的 = 检索.找相关(问题, 块们, 3)
    查过的 = []
    print(f"\n检索一次，挑中 {len(挑中的)} 块：")
    for 块 in 挑中的:
        print("    " + 块的钥匙(块) + "  " + 块["标题"][:32])
        查过的.append(块的钥匙(块))

    提示词 = (
        "下面是给你的笔记节选：\n\n"
        + "\n\n".join(块["正文"] for 块 in 挑中的)
        + f"\n\n根据上面的笔记回答：{问题}\n如果笔记里没有，只输出：[[无答案]]"
    )
    回 = 发请求({"model": 模型名, "messages": [{"role": "user", "content": 提示词}]})
    答案 = (回["choices"][0]["message"].get("content") or "").strip()

    print("\n它最后说：")
    for 行 in 答案.splitlines():
        print("    " + 行)

    return {"检索次数": 1, "查过的块": 查过的, "答案": 答案}


# ================================================================ 场景乙：工具写法
def 场景乙(块们: list[dict]) -> dict:
    print("\n" + "█" * 64)
    print("█ 场景乙：工具写法 —— 检索装在模型手里（它想查几次就查几次）")
    print("█" * 64)

    消息们 = [
        {
            "role": "system",
            "content": (
                "你是我的笔记助手，只能根据笔记内容回答。\n"
                "回答之前必须先调用 search_notes 查笔记；一次查不准就换个说法再查一次。\n"
                "回答时带上出处（[文件名:行号]）。笔记里确实没有的，就明说「笔记里没有」。"
            ),
        },
        {"role": "user", "content": 问题},
    ]

    查过的: list[str] = []
    检索次数 = 0
    for 轮 in range(1, 5):
        回 = 发请求({"model": 模型名, "messages": 消息们, "tools": 工具清单})
        选 = 回["choices"][0]
        回话 = 选["message"]
        申请们 = 回话.get("tool_calls") or []
        print(f"\n---- 第 {轮} 轮：finish_reason = {选.get('finish_reason')}，申请 {len(申请们)} 张 ----")

        if not 申请们:
            答案 = (回话.get("content") or "").strip()
            print("\n它最后说：")
            for 行 in 答案.splitlines():
                print("    " + 行)
            break

        消息们.append(回话)
        for 申请 in 申请们:
            参数 = json.loads(申请["function"]["arguments"])
            名前 = 申请["function"]["name"]
            print(f"    申请单：{名前}({json.dumps(参数, ensure_ascii=False)})")

            回话内容, 这几块 = 工具表[名前](**参数)
            检索次数 += 1
            print("    查到的：" + "、".join(块的钥匙(块) for 块 in 这几块))
            查过的.extend(块的钥匙(块) for 块 in 这几块)

            消息们.append({"role": "tool", "tool_call_id": 申请["id"], "content": 回话内容})

    else:
        答案 = "（跑满 4 轮还没收口）"
        print("\n" + 答案)

    return {"检索次数": 检索次数, "查过的块": 查过的, "答案": 答案}


# ================================================================ 那只手 + 那张菜单
def 查笔记(query: str) -> tuple[str, list[dict]]:
    """模型手里那只手：拿一句话去柜子里翻笔记。

    返回两个东西：塞回去给模型的字、这一次翻出来的块（第二个是给我们自己数的，
    模型看不到它 —— 它只看得到第一个）。
    """
    挑中的 = 检索.找相关(query, 块们全局, 3)
    if not 挑中的:
        return "什么也没翻到，换个说法再查。", []
    return "\n\n".join(块文字(块) for 块 in 挑中的), 挑中的


工具表 = {
    "search_notes": 查笔记,
}


工具清单 = [
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

块们全局: list[dict] = []


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


# ================================================================ 数一数
def 话题答上了(答案: str) -> dict[str, bool]:
    """答案里有没有说到那个话题的关键词。看到就算答上，没看到就算没答上。"""
    结果 = {}
    for 话题, 锚点 in 话题锚点.items():
        结果[话题] = any(词 in 答案 for 词 in 锚点)
    return 结果


def 对的块进了几块(查过的: list[str]) -> dict[str, bool]:
    """两个话题各有没有至少一块「对的块」被查到。"""
    return {
        "闭包": "python-learning-2026-09-01.md 行99" in 查过的,
        "with": ("python-learning-2026-08-14.md 行43" in 查过的)
        or ("python-learning-2026-08-14.md 行55" in 查过的),
    }


def 主流程() -> None:
    global 块们全局
    块们全局 = 取块们()
    print(f"可用块：{len(块们全局)}    问：{问题}\n")

    甲 = 场景甲(块们全局)
    乙 = 场景乙(块们全局)

    print("\n" + "=" * 64)
    print("数一数，两种写法差在哪")
    print("=" * 64)

    for 名字, 结果 in (("老写法", 甲), ("工具写法", 乙)):
        查到 = 对的块进了几块(结果["查过的块"])
        答上 = 话题答上了(结果["答案"])
        print(f"\n【{名字}】")
        print(f"    检索次数            = {结果['检索次数']}")
        print(f"    查过的块（去重）    = {len(set(结果['查过的块']))}")
        print(f"    对的块进了几个话题  = {sum(查到.values())}/2   （闭包 {'有' if 查到['闭包'] else '无'} / with {'有' if 查到['with'] else '无'}）")
        print(f"    最终答案答上了几个  = {sum(答上.values())}/2   （闭包 {'有' if 答上['闭包'] else '无'} / with {'有' if 答上['with'] else '无'}）")

    print("\n" + "-" * 64)
    print("一句话：模型不是变聪明了，是你把「查什么」这个决定还给了它。")
    print("老写法里那个决定是你写死的（找相关(问题, 块们, 3)），一句两问的话就被一句话查走了；")
    print("工具写法里它看到「闭包查到了」，就知道「with 还没查」，于是自己再要一次。")


if __name__ == "__main__":
    主流程()
