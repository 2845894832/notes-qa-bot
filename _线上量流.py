# -*- coding: utf-8 -*-
"""线上量流 —— 数第一个字节是什么时候到的（第 16 课）。

为什么不用眼睛看：
    "一段一段蹦出来"和"五秒憋一大坨"在屏幕上都很像"流"。
    唯一不会骗人的是时间戳：从**发出请求**到**收到第一片**用了多少秒。

为什么要 requests 的 stream=True：
    不加它，requests 会先把整个响应体收完再给你 —— 你量到的永远是"总耗时"，
    看不到"第一片什么时候到"。这跟第 12 课那个道理一样：不流式，就只有一个数。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _线上量流.py                     # 量线上
    python _线上量流.py --本地               # 量本地（先起 uvicorn 服务:app）
    python _线上量流.py "闭包是什么"          # 换问题

第一次可能十几秒（容器在睡觉，要唤醒），别当它坏了 —— 那个数要单独看。
"""

import json
import sys
import time

import requests

sys.stdout.reconfigure(errors="replace")

本地 = "--本地" in sys.argv
问题 = next((a for a in sys.argv[1:] if not a.startswith("--")), "闭包是什么")

if 本地:
    地址 = "http://127.0.0.1:8000/问流"
else:
    地址 = "https://budon777-notes-qa-bot.ms.show/问流"

头 = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.modelscope.cn/studios/budon777/notes-qa-bot",
    "Origin": "https://www.modelscope.cn",
    "Accept": "text/event-stream",
}

print(f"地址：{地址}")
print(f"问题：{问题}")
开始 = time.time()
首片 = None
片数 = 0
字们 = []

try:
    响应 = requests.get(地址, params={"问题": 问题}, headers=头,
                        stream=True, timeout=(10, 120))
    print(f"状态码：{响应.status_code}")
    响应.raise_for_status()

    for 行 in 响应.iter_lines(decode_unicode=False):
        if not 行:
            continue
        行 = 行.decode("utf-8", errors="replace")
        if not 行.startswith("data: "):
            continue
        段 = 行[len("data: "):]
        片数 += 1
        if 首片 is None:
            首片 = time.time() - 开始
            print(f"  第一片：{首片:.2f} 秒  ← 这个数才是'真流'的证据")
        if 段.strip() == "[DONE]":
            print("  收到 [DONE]，闸门关了")
            break
        字们.append(json.loads(段).get("字", ""))

except Exception as 错:
    print(f"出错了：{type(错).__name__}: {错}")
    sys.exit(1)

整问 = time.time() - 开始
全文 = "".join(字们)
print()
print(f"片段数：{片数}")
print(f"整问秒：{整问:.2f}")
print(f"首片秒：{'—' if 首片 is None else f'{首片:.2f}'}")
print(f"字数：{len(全文)}")
print(f"开头：{全文[:40]}{'…' if len(全文) > 40 else ''}")
print()
if 片数 <= 1:
    print("⚠ 只有一片 —— 多半不是流（网关攒成一包了，或者服务端走的是老接口）")
elif 首片 is not None and 整问 > 0 and 首片 > 整问 * 0.6:
    print("⚠ 第一片来得太晚（占整问的六成以上）—— 像是一起攒着发的")
else:
    print("√ 像真流：第一片来得很早，后面还在继续来")
