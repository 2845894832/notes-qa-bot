# -*- coding: utf-8 -*-
"""第 14 课 · MCP —— 手不在你家里。

这个文件不花 API 钱：不接模型，只演示"问另一个进程要工具"。
幕一  手在自己家：直接 import，直接调函数
幕二  起一个服务器子进程：一行一行的 JSON-RPC 长什么样
幕三  tools/list 回来的菜单，能不能直接当 OpenAI 的 tools 用
幕四  工具出错：isError=true（跟第 4 课"失败也要回一条"对得上）
幕五  把服务器关了，再伸手 —— 供应商不在了

一句话：清单还是清单、申请单还是申请单；变的只是**谁在执行**。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

这里 = Path(__file__).resolve().parent
服务器文件 = 这里 / "_MCP服务器.py"

计数器 = {"发": 0, "收": 0}


def 起服务器():
    环境 = dict(os.environ)
    环境["PYTHONIOENCODING"] = "utf-8"
    return subprocess.Popen(
        [sys.executable, str(服务器文件)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,               # 服务器的日志留在屏幕上，方便看
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=环境,
    )


def 发(进程, 消息):
    print("  → " + json.dumps(消息, ensure_ascii=False))
    进程.stdin.write(json.dumps(消息, ensure_ascii=False) + "\n")
    进程.stdin.flush()
    计数器["发"] += 1
    if "id" not in 消息:          # 通知：不回
        return None
    行 = 进程.stdout.readline()
    if not 行:
        print("  ← （空 —— 服务器已经不在了）")
        return None
    计数器["收"] += 1
    回话 = json.loads(行)
    print("  ← " + json.dumps(回话, ensure_ascii=False))
    return 回话


def 转成OpenAI菜单(工具们):
    """MCP 的 inputSchema 就是 JSON Schema —— OpenAI 的 parameters 也是它。"""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"],
            },
        }
        for t in 工具们
    ]


print("=" * 66)
print("幕一：手在自己家 —— import 进来直接调")
print("=" * 66)
import _MCP服务器 as 服务器

print("  " + 服务器.查账("2026-09", "餐饮").splitlines()[0])
print("  ★ 这一课之前，你的三只手就是这么活的：同一个进程、同一个 import。")
print("    缺点：想换掉一只手，得改你这个程序的代码、重新启动它。")


print()
print("=" * 66)
print("幕二：手搬到隔壁 —— 起一个服务器，用 JSON 说话")
print("=" * 66)
进程 = 起服务器()
print("  （服务器已经作为**另一个进程**跑起来了，它有自己的 stdin/stdout）\n")

握手 = 发(进程, {
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
               "clientInfo": {"name": "演示", "version": "0.1"}},
})
服务器名 = 握手["result"]["serverInfo"]["name"]
print(f"  ★ 握手：对面叫「{服务器名}」，会说 tools 这一摊\n")

发(进程, {"jsonrpc": "2.0", "method": "notifications/initialized"})   # 通知，不回

菜单回话 = 发(进程, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
工具们 = 菜单回话["result"]["tools"]
print(f"  ★ 菜单回来了：{len(工具们)} 只 —— {'、'.join(t['name'] for t in 工具们)}\n")

结果 = 发(进程, {
    "jsonrpc": "2.0", "id": 3, "method": "tools/call",
    "params": {"name": "read_ledger", "arguments": {"month": "2026-09", "category": "餐饮"}},
})
文字 = 结果["result"]["content"][0]["text"]
print("  ★ 下单回来了，第一行：" + 文字.splitlines()[0])
print("    注意：**结果在 content[0].text 里**，不是 `result` 本身 —— 跟模型的 tool 消息一个道理，都要字符串。")


print()
print("=" * 66)
print("幕三：菜单能直接喂给模型吗")
print("=" * 66)
转换后 = 转成OpenAI菜单(工具们)
print("  转换之后长这样（跟你第 6 课手写的那张一模一样）：")
print("  " + json.dumps(转换后[0], ensure_ascii=False)[:220] + " …")
print()
print("  ★ 这就是 MCP 能通吃的原因：`inputSchema` 本来就是 JSON Schema，")
print("    OpenAI 的 `parameters` 也是 —— 只差外面套一层 `type: function / function`。")


print()
print("=" * 66)
print("幕四：工具出错，跟第 4 课对上")
print("=" * 66)
坏 = 发(进程, {
    "jsonrpc": "2.0", "id": 4, "method": "tools/call",
    "params": {"name": "没有这只手", "arguments": {}},
})
print(f"  isError = {坏['result']['isError']}")
print("  ★ 工具错不走 JSON-RPC 的 error 那一栏，而是**照常回一条结果**、打上 isError。")
print("    跟第 4 课那句一样：失败也必须占一条回音，模型才看得见。")


print()
print("=" * 66)
print("幕五：把服务器关掉，再伸手")
print("=" * 66)
进程.terminate()
进程.wait(timeout=5)
try:
    发(进程, {"jsonrpc": "2.0", "id": 5, "method": "tools/list"})
except (BrokenPipeError, ValueError, OSError) as 错:
    print(f"  ← 发不出去：{type(错).__name__}: {错}")
print()
print("  ★ 手跟着供应商一起没了。你的程序**没崩**，只是这一趟拿不到东西 ——")
print("    所以真实项目里，连不上服务器要当成一条**工具失败**塞回给模型（第 4 课），不是让整个程序炸掉。")

for 管 in (进程.stdin, 进程.stdout):
    try:
        管.close()
    except OSError:
        pass


print()
print("=" * 66)
print(f"账：协议来回 {计数器['发']} 发 / {计数器['收']} 收；工具 {len(工具们)} 只")
print("=" * 66)
