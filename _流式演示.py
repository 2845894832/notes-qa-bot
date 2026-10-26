# -*- coding: utf-8 -*-
"""第 12 课 · 流式输出 —— 回答不是一次到齐的，是一片一片到的。

类比：看视频。**整片下载完再播** = 缓冲条拉到 100% 才有第一帧；
**边下边播** = 半秒钟就有画面，只是后面还在路上。

模型本来就是一个字一个字往外吐的。以前是你自己按住了它的嘴：
`stream=False`（默认）→ 它吐完一整句，服务器攒好再交给你。
`stream=True` → 它吐一片，你就收到一片。

四幕：
  幕一（不花钱）看"一行一行"到底长什么样 —— 用假数据，先看清格式
  幕二（真跑 2 次）非流式 vs 流式：量三个数（首包 / 首字 / 总耗时）
  幕三（真跑 1 次）带工具菜单：arguments 也是碎片，得按 index 拼回去
  幕四（不花钱）拼完的东西，跟一次性拿到的**形状一样** —— 所以主程序只换快递员
"""

import json
import time

import requests

import 问模型

头 = {"Authorization": "Bearer " + 问模型.拿钥匙(), "Content-Type": "application/json"}


def 发一次(本子, 菜单=None, 流式=False):
    """这堂课唯一的请求函数：只多一个 流式 开关。"""
    体 = {"model": 问模型.模型名, "messages": 本子}
    if 菜单:
        体["tools"] = 菜单
    if 流式:
        体["stream"] = True
    r = requests.post(问模型.聊天地址, headers=头, json=体, stream=流式, timeout=60)
    r.raise_for_status()
    return r


# ================================================================ 幕一
print("=" * 62)
print("幕一：流式到底「流」的是什么 —— 假数据，一行一片")
print("=" * 62)

假流 = """data: {"choices":[{"delta":{"content":"闭"}}]}

data: {"choices":[{"delta":{"content":"包"}}]}

data: {"choices":[{"delta":{"content":"是"}}]}

data: {"choices":[{"delta":{"content":"函数"}}]}

data: [DONE]
"""

print("服务器发过来的原文长这样（注意每片之间有个空行）：")
for 行 in 假流.splitlines():
    print("    " + 行 if 行 else "    ←空行")
print()

print("切成一行一行来读：")
for 行 in 假流.splitlines():
    if not 行.strip():
        continue                     # 空行只是分隔符，没内容
    if not 行.startswith("data: "):
        continue                     # 万一有别的行（注释/心跳），一律不认
    if 行 == "data: [DONE]":
        print("    [DONE] ← 收工信号，它不是 JSON，别 json.loads")
        break
    片 = json.loads(行[len("data: "):])["choices"][0]["delta"]
    print(f"    data: 之后的 {len(行) - 6} 个字符 → 一片正文：{片.get('content')!r}")

print()
print("  ★ 三个动作：① 只认 `data: ` 开头的行  ② [DONE] 就停  ③ 剩下那段交给 json.loads")
print("    你不用自己切逗号 —— 服务器已经帮你切成一行一个完整 JSON 了（这就是 jsonl 那招）。")


# ================================================================ 幕二
print()
print("=" * 62)
print("幕二：同一句话，两条路，量三个数（真跑 2 次）")
print("=" * 62)

问题 = "用一句话说说闭包是什么，不要用术语。"
本子 = [{"role": "user", "content": 问题}]

开始 = time.time()
r = 发一次(本子)
一次消息 = r.json()["choices"][0]["message"]
一次耗时 = time.time() - 开始
print(f"  非流式：干等了 {一次耗时:.2f} 秒，屏幕上才出现第一行字；")
print(f"          然后 {len(一次消息.get('content') or '')} 个字一下子全出来。")
print()

开始 = time.time()
r = 发一次(本子, 流式=True)
首包 = 首字 = None
片数 = 0
想的字 = 0
正文 = ""
print("  流式：它到一片我打一片 →  ", end="")
for 行 in r.iter_lines(decode_unicode=True):
    if not 行 or not 行.startswith("data: "):
        continue
    正文行 = 行[len("data: "):]
    if 正文行 == "[DONE]":
        break
    片 = json.loads(正文行)["choices"][0].get("delta") or {}
    片数 += 1
    if 首包 is None:
        首包 = time.time() - 开始          # ⚠️ 别写 `首包 = 首包 or ...`，0.0 也算假
    想的字 += len(片.get("reasoning_content") or "")   # 草稿，不给用户看
    段 = 片.get("content")
    if 段:
        if 首字 is None:
            首字 = time.time() - 开始
        正文 += 段
        print(段, end="", flush=True)
总耗时 = time.time() - 开始
print()
print()
print(f"  一共收到 {片数} 片；它先在肚子里打了 {想的字} 字草稿（reasoning_content，不显示）")
print(f"  首包 {首包:.2f} 秒   ← 网络这一趟有多快")
print(f"  首字 {首字:.2f} 秒   ← 用户第一次看见东西，真正决定「快不快」的数")
print(f"  说完 {总耗时:.2f} 秒   ← 跟非流式那个 {一次耗时:.2f} 秒是同一件事")
print()
print("  ★ 流式没有让模型变快，总耗时差不多；")
print(f"    它只是把「要干等 {一次耗时:.2f} 秒」变成「{首字:.2f} 秒就开始出字」。")


# ================================================================ 幕三
print()
print("=" * 62)
print("幕三：带工具菜单 —— arguments 也是碎片（真跑 1 次）")
print("=" * 62)

菜单 = [{
    "type": "function",
    "function": {
        "name": "search_notes",
        "description": "翻我的学习笔记，返回正文和出处。只读。",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "要查什么"}},
            "required": ["query"],
        },
    },
}]

本子 = [{"role": "user", "content": "闭包是什么？先查我的笔记"}]
r = 发一次(本子, 菜单, 流式=True)

原样碎片 = []
for 行 in r.iter_lines(decode_unicode=True):
    if not 行 or not 行.startswith("data: "):
        continue
    正文行 = 行[len("data: "):]
    if 正文行 == "[DONE]":
        break
    for 申 in (json.loads(正文行)["choices"][0].get("delta") or {}).get("tool_calls") or []:
        原样碎片.append(申)

print(f"  模型要伸手了，它把「申请单」拆成了 {len(原样碎片)} 片发过来。前 3 片：")
for 片 in 原样碎片[:3]:
    print("    " + json.dumps(片, ensure_ascii=False))
print("  后 3 片（注意：只有 index 和 arguments，连名字都没有）：")
for 片 in 原样碎片[-3:]:
    print("    " + json.dumps(片, ensure_ascii=False))
print()

# 按 index 拼回去
申请们: dict[int, dict] = {}
for 片 in 原样碎片:
    位置 = 申请们.setdefault(片["index"], {"id": "", "type": "function",
                                          "function": {"name": "", "arguments": ""}})
    位置["id"] = 片.get("id") or 位置["id"]
    函数 = 片.get("function") or {}
    位置["function"]["name"] = 函数.get("name") or 位置["function"]["name"]
    位置["function"]["arguments"] += 函数.get("arguments") or ""   # ← 只能加，不能覆盖

for 序, 申请 in 申请们.items():
    print(f"  拼好的第 {序} 张申请：")
    print(f"    名字      {申请['function']['name']}")
    print(f"    参数原文  {申请['function']['arguments']}")
    print(f"    变成 dict {json.loads(申请['function']['arguments'])}   ← 拼完才能 json.loads")
print()
print("  ★ 碎片按 index 归队；name / id 只出现在开头那片，arguments 一片一片往上加。")
print("    谁要是每片都 `申请 = 片`，最后只剩最后一个字符。")


# ================================================================ 幕四
print()
print("=" * 62)
print("幕四：拆包拆完，跟整箱到货是同一个东西")
print("=" * 62)

流式消息 = {"role": "assistant", "content": 正文}     # 幕二拼出来的
print(f"  非流式拿到的 message 有哪些键：{sorted(一次消息)}")
print(f"  流式拼出来的 message 有哪些键：{sorted(流式消息)}")
print()
print(f"  非流式：回话.get('content') → {repr((一次消息.get('content') or '')[:18])}…")
print(f"  流式  ：回话.get('content') → {repr(正文[:18])}…")
print()
print("  ★ 所以 主程序.py 那个循环一行都不用改：它只认 回话['content'] 和 回话['tool_calls']。")
print("    流式换掉的是「怎么到货」，不是「到货是什么」。")
print("    ⚠️ 本子这件事也没变：流式拼出来的那条，照样要 append 回本子。")
print()
print("  唯一的真差别：思考过程在 reasoning_content 里，它不是正文。")
print("  屏幕上要不要显示是你定的；拼回本子时只留 role / content / tool_calls 最干净。")
