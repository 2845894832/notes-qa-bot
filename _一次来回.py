# -*- coding: utf-8 -*-
"""第 5 课补充：「把检索装在模型手里」到底是把什么装进去的？

只跑一次来回，把三张纸的原样打印出来看：

    第一张  tools 里那条说明书   —— 你发给它的（跟 system 一样，每次请求都跟着走）
    第二张  回话里的 tool_calls  —— 它发给你的（申请单，query 是它自己填的）
    第三张  role=tool 那条消息   —— 你塞回去的（检索结果，你的代码跑出来的）

看完你会明白：**"装进手里"= 往请求体里加一个 tools 数组 + 外面套一个 while 循环。**
检索的代码一行都没进模型 —— 它还在你硬盘上，被你的循环调用。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _一次来回.py
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

问题 = "with 语句怎么用"
块们 = 检索.可用块()

# ---- 那张菜单（要"装进去"的就是这一条）--------------------------------
工具清单 = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "在我的学习笔记里搜索跟问题相关的段落。返回段落正文，每段前面带出处 [文件名:行号]。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索用的关键词或一句话"}
                },
                "required": ["query"],
            },
        },
    },
]


def 查笔记(query: str) -> str:
    """那只手。注意：这是我硬盘上的普通函数，模型看不见它，也调不动它。"""
    挑中的 = 检索.找相关(query, 块们, 3)
    print(f"        （你的代码正在跑：检索.找相关({query!r}) → 翻出 {len(挑中的)} 块）")
    return "\n\n".join(
        f"[{块['文件']}:{块['行号']} {块['标题']}]\n{块['正文']}" for 块 in 挑中的
    )


工具表 = {"search_notes": 查笔记}


def 发一次(消息们: list) -> dict:
    请求体 = {"model": 模型名, "messages": 消息们, "tools": 工具清单}
    r = requests.post(
        聊天地址,
        headers={
            "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"],
            "Content-Type": "application/json",
        },
        json=请求体,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]


def 打印(标题: str, 内容) -> None:
    print("\n" + "=" * 70)
    print(标题)
    print("=" * 70)
    print(内容 if isinstance(内容, str) else json.dumps(内容, ensure_ascii=False, indent=2))


def 主流程() -> None:
    print("问：" + 问题)

    # ---- 第一张纸：你发给它的 tools ----
    打印("第一张纸【你 → 它】：请求体里的 tools（就是「装在手里」的全部东西）", 工具清单)

    消息们 = [{"role": "user", "content": 问题}]

    # ================= 第 1 次请求 =================
    回 = 发一次(消息们)
    回话 = 回["message"]
    打印(
        f"第二张纸【它 → 你】：finish_reason = {回['finish_reason']}，回话原文如下",
        回话,
    )

    申请们 = 回话.get("tool_calls") or []
    if not 申请们:
        print("\n它没申请工具，直接答了：" + (回话.get("content") or ""))
        return

    消息们.append(回话)   # 先把它这张申请单存进对话，不然下一轮它不认账

    # ---- 你的循环替它做的三件事：查表 → 跑函数 → 装箱塞回 ----
    查询词们 = []
    for 申请 in 申请们:
        名字 = 申请["function"]["name"]
        参数 = json.loads(申请["function"]["arguments"])
        print(f'\n>>> 你的代码接手：工具表["{名字}"](**{参数})')
        查询词们.append(参数.get("query", ""))
        结果 = 工具表[名字](**参数)
        消息们.append({"role": "tool", "tool_call_id": 申请["id"], "content": 结果})

    打印(
        "第三张纸【你 → 它】：刚才塞回去的那条 role=tool（正文只打前 300 字）",
        json.dumps(
            {**消息们[-1], "content": 消息们[-1]["content"][:300] + "……"}, ensure_ascii=False, indent=2
        ),
    )

    # ================= 第 2 次请求：它现在看得到结果了 =================
    回2 = 发一次(消息们)
    第二句 = (回2["message"].get("content") or "").strip()
    打印(
        f"它第二次的回话（finish_reason = {回2['finish_reason']}）",
        第二句 if 第二句 else "（空的 —— 它又要工具了。这个脚本只跑两趟，就此打住；真流程里那个 while 会接着转。）",
    )

    print("\n" + "-" * 70)
    print(f"数一数：请求 2 次、tools 数组大小 1、你的函数跑了 {len(查询词们)} 次。")
    print("从头到尾，检索的代码都在你这边跑；模型只写了这几个词：")
    for 词 in 查询词们:
        print("    " + json.dumps({"query": 词}, ensure_ascii=False))
    print("—— 那就是「把检索装在它手里」的全部含义：它决定问什么，你负责去查。")


if __name__ == "__main__":
    主流程()
