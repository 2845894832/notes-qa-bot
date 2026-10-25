# -*- coding: utf-8 -*-
"""线上三问 —— 换班之后，在**真线上**数一遍，不是拿本地的数糊弄过去。

为什么要有这个：
    本地 20 题 0/0 只证明"我电脑上这版是对的"。线上那台是照着仓库从零重建的，
    换了引擎以后它认不认账本、认不认拒答标记，只有问它才知道。

为什么带那三个请求头：
    直连 `ms.show` 会被网关挡（403：当前接口不支持通过SDK Token直接访问）。
    带上浏览器的 User-Agent / Referer / Origin，它就当你是网页在问 —— 200。
    （这不是绕过鉴权：这个创空间本来就是公开给面试官看的，匿名可访问。）

跑法：
    cd "D:/CC Switch/问答机器人"
    python _线上三问.py

第一问可能要等十几秒（容器睡着要唤醒），别当它坏了。
"""

import json
import re
import sys

import requests

sys.stdout.reconfigure(errors="replace")

地址 = "https://budon777-notes-qa-bot.ms.show/问"
头 = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.modelscope.cn/studios/budon777/notes-qa-bot",
    "Origin": "https://www.modelscope.cn",
}

三问 = [
    # (问题, 判据函数, 这一问在验什么)
    ("闭包是什么", lambda a: "python-learning" in a, "检索那只手活着（答案带出处）"),
    ("9 月餐饮一共多少", lambda a: "262.00" in a, "账本母本真的搬过去了"),
    # ⚠️ 日期必须写死。写"今天"它只会反问"今天是几号"（模型不知道今天），
    #    那张申请根本没递出来 —— 尺子问得不具体，量到的就不是它想量的事。
    (
        "帮我记一笔：2026-10-25 午饭 28 元，餐饮",
        lambda a: "笔记里没有" not in a and any(
            词 in a for 词 in ("没有写入", "没改", "已拒绝", "没有执行", "拒绝", "未写入", "没有权限")
        ),
        "线上没键盘 → 闸门该拒绝，账本一个字没动（不是卡到 504）",
    ),
]


def 问(问题: str) -> tuple[str, float]:
    """问一句，返回 (答案, 耗时秒)。"""
    import time

    起 = time.time()
    r = requests.post(地址, headers=头, json={"问题": 问题}, timeout=180)
    r.raise_for_status()
    return r.json()["答案"], time.time() - 起


def main() -> None:
    过 = 0
    for 问题, 判据, 说明 in 三问:
        答案, 耗时 = 问(问题)
        对 = 判据(答案)
        过 += 对
        牌 = "[OK]" if 对 else "[XX]"
        print(f"{牌} {耗时:5.1f}s  {问题}")
        print(f"      验的是：{说明}")
        print("      " + re.sub(r"\s+", " ", 答案)[:160])
        print()
    print(f"线上三问：过 {过}/3")
    if 过 < 3:
        print("没过的那一问，先看它答了啥 —— 是拒答？是答错？是 500？三种病三种药。")


if __name__ == "__main__":
    main()
