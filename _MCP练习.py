
# -*- coding: utf-8 -*-
r"""第 14 课 · MCP 练习 —— 你当一次**客户端**（三个 TODO）。不花钱、不联网。

    cd "D:\CC Switch\问答机器人"
    python _MCP练习.py

服务器是现成的：`_MCP服务器.py`（隔壁那个进程，手住在它那儿）。
你要写的只有"怎么跟它说话"这三件事：发一条 / 要菜单 / 下单。

填对了，最后会打 4 个 √。不填就是 NotImplementedError。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

这里 = Path(__file__).resolve().parent
服务器文件 = 这里 / "_MCP服务器.py"


# ══════════════════════════════════════════════════════════════════
# 这个给你了（不用改）：把服务器拉起来
# ══════════════════════════════════════════════════════════════════
def 起服务器() -> subprocess.Popen:
    环境 = dict(os.environ)
    环境["PYTHONIOENCODING"] = "utf-8"        # 子进程说 UTF-8，这里也按 UTF-8 读
    return subprocess.Popen(
        [sys.executable, str(服务器文件)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        encoding="utf-8",
        bufsize=1,                            # 行缓冲：写一行就出去
        env=环境,
    )


# ══════════════════════════════════════════════════════════════════
# TODO ①：发一条消息，并（如果需要）读回它的结果
# ══════════════════════════════════════════════════════════════════
def 发(进程, 消息):
    """一行一条 JSON-RPC。

    ① 先 print("  → " + json.dumps(消息, ensure_ascii=False))，方便对账
    ② 一行 = json.dumps(消息, ensure_ascii=False) + "\n"
    ③ 进程.stdin.write(一行)  然后  进程.stdin.flush()
       （⚠️ 不 flush，服务器收不到 —— 管道跟第 12 课的"缓冲区"一个毛病）
    ④ 没有 "id" 的消息 = 通知 → 写完直接 return None
    ⑤ 有 id：读一行 进程.stdout.readline()，json.loads 之后 return
       ⚠️ 读回来是 "空字符串" = 服务器已经没了，return None
    """
    print("  → " + json.dumps(消息, ensure_ascii=False))
    一行 = json.dumps(消息, ensure_ascii=False) + "\n"
    进程.stdin.write(一行)
    进程.stdin.flush()
    if "id" not in 消息:
        return None
    回话 = 进程.stdout.readline()
    if not 回话:
        return None
    return json.loads(回话)

# ══════════════════════════════════════════════════════════════════
# 这个给你了：MCP 的 inputSchema → OpenAI 的 tools 格式
# ══════════════════════════════════════════════════════════════════
def 转成OpenAI菜单(工具们: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"],      # ← 就换了个名
            },
        }
        for t in 工具们
    ]


# ══════════════════════════════════════════════════════════════════
# TODO ②：握手 + 要菜单 + 转成模型能吃的格式
# ══════════════════════════════════════════════════════════════════
def 要菜单(进程):
    """返回 OpenAI 格式的工具清单（list[dict]）。

    ① 发 initialize，id 用 1：
         {"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                     "clientInfo": {"name": "我的客户端", "version": "0.1"}}}
    ② 发 notifications/initialized —— 这条**没有 id**（是通知，服务器不回）
         {"jsonrpc": "2.0", "method": "notifications/initialized"}
    ③ 发 tools/list，id 用 2；从回话里掏 回话["result"]["tools"]
    ④ return 转成OpenAI菜单(工具们)
    """
    消息 = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "我的客户端", "version": "0.1"},
        },
    }
    发(进程, 消息)
    发(进程, {"jsonrpc": "2.0", "method": "notifications/initialized"}) 
    回话 = 发(进程, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    工具们 = 回话["result"]["tools"]
    return 转成OpenAI菜单(工具们)


# ══════════════════════════════════════════════════════════════════
# TODO ③：下单 —— 让服务器那只手干活
# ══════════════════════════════════════════════════════════════════
def 下单(进程, 编号: int, 名字: str, 参数: dict) -> tuple[str, bool]:
    """返回 (文字, 是否失败)。

    ① 发 tools/call，id 用传进来的 编号：
         {"jsonrpc": "2.0", "id": 编号, "method": "tools/call",
          "params": {"name": 名字, "arguments": 参数}}
    ② 文字 = 回话["result"]["content"][0]["text"]
    ③ 是否失败 = 回话["result"].get("isError", False)
       ⚠️ isError=True 时**文字也要带回来** —— 第 4 课：失败也占一条回音，
          模型看见的正是这段文字
    """
    回话 = 发(进程, {"jsonrpc": "2.0", "id": 编号, "method": "tools/call",
                      "params": {"name": 名字, "arguments": 参数}})
    文字 = 回话["result"]["content"][0]["text"]
    是否失败 = 回话["result"].get("isError", False)
    return 文字, 是否失败


# ══════════════════════════════════════════════════════════════════
# 自检（不用改）：跑完看这一串 √
# ══════════════════════════════════════════
if __name__ == "__main__":
    进程 = 起服务器()
    通过 = 0
    try:
        print("=" * 60)
        print("① 要菜单")
        print("=" * 60)
        菜单 = 要菜单(进程)
        名字们 = [t["function"]["name"] for t in 菜单]
        print(f"  菜单：{名字们}")
        if len(菜单) >= 2:
            print(f"  √ [1] 菜单回来 {len(菜单)} 只"); 通过 += 1
        else:
            print(f"  × [1] 至少要 2 只，现在是 {len(菜单)}")
        if "read_ledger" in 名字们:
            print("  √ [2] 里面有 read_ledger"); 通过 += 1
        else:
            print("  × [2] 没找到 read_ledger")

        print()
        print("=" * 60)
        print("② 下单：2026-09 餐饮")
        print("=" * 60)
        文字, 失败 = 下单(进程, 3, "read_ledger", {"month": "2026-09", "category": "餐饮"})
        print("  " + 文字.splitlines()[0])
        if (not 失败) and "共 7 笔" in 文字 and "262.00" in 文字:
            print("  √ [3] 共 7 笔 / 262.00"); 通过 += 1
        else:
            print(f"  × [3] 数不对（失败={失败}）")

        print()
        print("=" * 60)
        print("③ 下错单：没有这只手")
        print("=" * 60)
        坏文字, 坏失败 = 下单(进程, 4, "没有这只手", {})
        print("  " + 坏文字)
        if 坏失败 and 坏文字:
            print("  √ [4] isError=True，而且文字没丢"); 通过 += 1
        else:
            print(f"  × [4] 失败={坏失败}，文字={坏文字[:20]!r}")
    finally:
        进程.terminate()
        进程.wait(timeout=5)
        for 管 in (进程.stdin, 进程.stdout):
            try:
                管.close()
            except OSError:
                pass

    print()
    print("=" * 60)
    print(f"自检：{通过} / 4 个 √")
    print("=" * 60)
