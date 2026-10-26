# -*- coding: utf-8 -*-
"""第 12 课 · 流式练习 —— 把"一片一片到"拼回"一条 message"。

三个 TODO：
  TODO 1（不花钱）  拼碎片：一串 delta → 一条完整 message。脚本会自己判对错。
  TODO 2（花 1 次）  流式发消息：真发一次，边收边打，返回 (消息, 首包秒, 首字秒)。
  TODO 3（花 2 次）  两条路对着看：同一问，非流式 / 流式各来一次，比形状。

跑法：  python _流式练习.py
先只填 TODO 1，跑一遍 —— 两个 ✓ 出来再往下写，别一口气写完再跑。
"""

import json
import time

import requests

import 问模型

头 = {"Authorization": "Bearer " + 问模型.拿钥匙(), "Content-Type": "application/json"}


# ================================================================ 假碎片（不花钱）
# 真服务器发来的碎片就长这样：一条一条 delta，按先后顺序排。（这里手打，为了可复现）
假碎片们 = [
    {"role": "assistant", "content": None, "reasoning_content": ""},
    {"content": None, "reasoning_content": "用户"},
    {"content": None, "reasoning_content": "问"},
    {"content": "闭"},
    {"content": "包"},
    {"content": "。"},
    {"content": "", "reasoning_content": None},
]

假碎片们_带申请 = [
    {"role": "assistant", "content": None, "reasoning_content": ""},
    {"content": None, "reasoning_content": "先查账"},
    {"tool_calls": [{"index": 0, "id": "call_a", "type": "function",
                     "function": {"name": "read_ledger", "arguments": ""}}]},
    {"tool_calls": [{"index": 1, "id": "call_b", "type": "function",
                     "function": {"name": "search_notes", "arguments": ""}}]},
    {"tool_calls": [{"index": 0, "function": {"arguments": "{\"mo"}}]},
    {"tool_calls": [{"index": 1, "function": {"arguments": "{\"qu"}}]},
    {"tool_calls": [{"index": 0, "function": {"arguments": "nth\": \"2026-09\"}"}}]},
    {"tool_calls": [{"index": 1, "function": {"arguments": "ery\": \"闭包\"}"}}]},
]


def 拼碎片(碎片们: list[dict]) -> dict:
    """把一串 delta 拼成一条 message（跟非流式拿到的那条形状一样）。

    返回：{"role": "assistant", "content": "拼好的正文"}
          有申请就再加一条 "tool_calls": [{"id":..., "type":"function",
                                          "function": {"name":..., "arguments":...}}, ...]

    TODO 1 —— 两步：
      ① 正文：从一个空字符串起，遇到片里的 "content" 不是 None 的就 += 上去
         （"content": "" 是空片，+= 上去也没事；None 不能 +=，会 TypeError）
      ② 申请：准备一个 dict，键是 index，值是那一张申请
            遇到 tool_calls 里的每一片 申：
             拿 序 = 申["index"]，用 申请们.setdefault(序, {...空壳...}) 占位
             申.get("id") 有就写进壳子
             申.get("function") 里的 "name" 有就写进壳子
             申.get("function") 里的 "arguments" **一律 +=**（不覆盖！）
      ③ 收尾：把 申请们 按 序 排好放进 message 的 "tool_calls"；
         一张申请都没有，就不要这个键

    三段自检在下面 __main__ 里，写错了它会直接告诉你哪不对。
    """
    正文 = ""
    申请们: dict[int, dict] = {}
    for 片 in 碎片们:
        if 片.get("content") is not None:
            正文 += 片["content"]
        for 申 in 片.get("tool_calls") or []:
            壳 = 申请们.setdefault(
                申["index"],
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if 申.get("id"):
                壳["id"] = 申["id"]
            函数 = 申.get("function") or {}
            if 函数.get("name"):
                壳["function"]["name"] = 函数["name"]
            壳["function"]["arguments"] += 函数.get("arguments") or ""
    消息 = {"role": "assistant", "content": 正文}
    if 申请们:
        消息["tool_calls"] = [申请们[序] for 序 in sorted(申请们)]
    return 消息


# ================================================================ 自检（不花钱）
def 对一对(名字: str, 拼好: dict, 期望: dict) -> None:
    """只比要紧的东西：正文、每张申请的 (id, 名字, 参数)。"""
    正文ok = 拼好.get("content") == 期望["content"]
    拼的申请 = [(a.get("id"), a["function"]["name"], a["function"]["arguments"])
                for a in 拼好.get("tool_calls") or []]
    期望申请 = [(a["id"], a["function"]["name"], a["function"]["arguments"])
                for a in 期望.get("tool_calls") or []]
    申请ok = 拼的申请 == 期望申请
    print(f"  {'✓' if 正文ok else '✗'} {名字} · 正文      {拼好.get('content')!r}")
    print(f"  {'✓' if 申请ok else '✗'} {名字} · 申请      {拼的申请}")
    if not 申请ok:
        print(f"      期望是：             {期望申请}")


# ================================================================ TODO 2
def 流式发消息(本子: list[dict], 菜单: list[dict] | None = None) -> tuple[dict, float, float]:
    """真发一次流式请求，边收边打正文，最后拼成一条 message。

    返回：(消息, 首包秒, 首字秒)

    TODO 2 —— 四步：
      ① 请求体：{"model": 问模型.模型名, "messages": 本子}
         有菜单就 请求体["tools"] = 菜单；再加 请求体["stream"] = True
      ② r = requests.post(问模型.聊天地址, headers=头, json=请求体,
                          stream=True, timeout=60)      ← ⚠️ stream 是 post 的参数
         r.raise_for_status()
         开始 = time.time()
      ③ for 行 in r.iter_lines(decode_unicode=True):
             空行 / 不是 "data: " 开头 → continue
             正文行 == "[DONE]" → break
             片 = json.loads(正文行[len("data: "):])["choices"][0].get("delta") or {}
             碎片们.append(片)
             首包：第一次进来时 首包 = time.time() - 开始（用 is None 判，别用 or）
             段 = 片.get("content")；是正文就 首字 = ...，然后 print(段, end="", flush=True)
      ④ 循环完（别忘 print() 换行）→ return 拼碎片(碎片们), 首包, 首字
    """
    请求体 = {"model": 问模型.模型名, "messages": 本子, "stream": True}
    if 菜单:
        请求体["tools"] = 菜单
    r = requests.post(问模型.聊天地址, headers=头, json=请求体, stream=True, timeout=60)
    r.raise_for_status()

    开始 = time.time()
    首包 = 首字 = None
    碎片们: list[dict] = []
    草稿字 = 0
    for 行 in r.iter_lines(decode_unicode=True):
        if not 行 or not 行.startswith("data: "):
            continue
        正文行 = 行[len("data: "):]
        if 正文行 == "[DONE]":
            break
        片 = json.loads(正文行)["choices"][0].get("delta") or {}
        碎片们.append(片)
        if 首包 is None:
            首包 = time.time() - 开始
        草稿字 += len(片.get("reasoning_content") or "")
        段 = 片.get("content")
        if 段:
            if 首字 is None:
                首字 = time.time() - 开始
            print(段, end="", flush=True)
    print()
    return 拼碎片(碎片们), 首包, 首字


# ================================================================ TODO 3
if __name__ == "__main__":
    print("=" * 60)
    print("一、拼碎片（不花钱）")
    print("=" * 60)
    对一对("纯正文", 拼碎片(假碎片们),
          {"content": "闭包。"})
    对一对("两张申请", 拼碎片(假碎片们_带申请),
          {"content": "",
           "tool_calls": [
               {"id": "call_a", "function": {"name": "read_ledger",
                                             "arguments": "{\"month\": \"2026-09\"}"}},
               {"id": "call_b", "function": {"name": "search_notes",
                                             "arguments": "{\"query\": \"闭包\"}"}},
           ]})

    print()
    print("=" * 60)
    print("二、真发一次流式（花 1 次钱）")
    print("=" * 60)
    # TODO 3 —— 两问，各来一次，把数打出来：
    #
    #   ① 普通问题（要看到边出边打的效果，问题问长一点）：
    #        消息, 首包, 首字 = 流式发消息([{"role": "user", "content": "用两句话说说闭包是什么"}])
    #        然后打三个数：首包 / 首字 / 正文多少字，还有 len(消息["content"])
    #
    #   ② 要伸手的问题（看 tool_calls 拼回来对不对）：
    #        菜单 = [{
    #            "type": "function",
    #            "function": {
    #                "name": "search_notes",
    #                "description": "翻我的学习笔记，返回正文和出处。只读。",
    #                "parameters": {"type": "object",
    #                               "properties": {"query": {"type": "string"}},
    #                               "required": ["query"]},
    #            },
    #        }]
    #        消息2, _, _ = 流式发消息([{"role": "user", "content": "闭包是什么？先查我的笔记"}], 菜单)
    #        申请们 = 消息2.get("tool_calls") or []
    #        打印 len(申请们)，再把每张申请的 名字 和 json.loads(参数) 打出来
    #        —— json.loads 能过，说明碎片拼对了；过不去 = 少了片或覆盖了
    #
    #   ③ 最后打一句结论：两条路拿到的 message，键是不是一样？
    #        （非流式那条可以顺手发一次拿来做对照：print(sorted(消息))）
    print("边到边打 →  ", end="")
    消息, 首包, 首字 = 流式发消息(
        [{"role": "user", "content": "用两句话说说闭包是什么"}])
    print(f"  首包 {首包:.2f} 秒 / 首字 {首字:.2f} 秒 / 正文 {len(消息['content'])} 字 / 键 {sorted(消息)}")

    print()
    print("=" * 60)
    print("三、要伸手的问题（花 2 次钱）")
    print("=" * 60)
    菜单 = [{
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "翻我的学习笔记，返回正文和出处。只读。",
            "parameters": {"type": "object",
                           "properties": {"query": {"type": "string"}},
                           "required": ["query"]},
        },
    }]
    问 = "闭包是什么？先查我的笔记"
    消息2, _, _ = 流式发消息([{"role": "user", "content": 问}], 菜单)
    申请们 = 消息2.get("tool_calls") or []
    print(f"  拼出 {len(申请们)} 张申请")
    for 申 in 申请们:
        print(f"    {申['function']['name']}  {json.loads(申['function']['arguments'])}")

    r = requests.post(问模型.聊天地址, headers=头,
                      json={"model": 问模型.模型名, "messages": [{"role": "user", "content": 问}],
                            "tools": 菜单}, timeout=60)
    r.raise_for_status()
    非流式 = r.json()["choices"][0]["message"]
    print(f"  非流式那条的键：{sorted(非流式)}")
    print(f"  流式拼出来的键：{sorted(消息2)}")
    print(f"  申请单的键    ：{sorted(非流式['tool_calls'][0])} / {sorted(申请们[0])}")
