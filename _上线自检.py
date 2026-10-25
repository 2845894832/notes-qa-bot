# -*- coding: utf-8 -*-
"""上线自检 —— 推之前先量一遍：这个仓库搬到一个空房间里，够不够它跑起来。

为什么要这一把尺子：
    线上那台机器**没有你的电脑**，它手里只有这个仓库（git 跟踪的那些文件）。
    仓库里没有的东西，线上就没有 —— 而且**不会报错**，只会在某只手伸出去的时候答不上。
    这些"看出来的东西"（哪个文件没跟踪、哪个库没表）眼睛看不见，这里一行一行数给你。

跑法：
    cd "D:/CC Switch/问答机器人"
    python _上线自检.py

最后一行是总数：`自检 7 项，过 7 项`。有 [XX] 就先别推。
"""

import inspect
import os
import sqlite3
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

这里 = os.path.dirname(os.path.abspath(__file__))
结果: list[tuple[bool, str, str]] = []      # (过没过, 这一项叫什么, 说明)


def 记(过了: bool, 名字: str, 说明: str) -> None:
    结果.append((过了, 名字, 说明))


def git(*参数: str) -> str:
    """在仓库里跑一条 git，返回输出（去掉首尾空白）。跑不动就返回空串。"""
    try:
        return subprocess.run(
            ["git", "-C", 这里, *参数],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        ).stdout.strip()
    except Exception:
        return ""


# ── ① 该在仓库里的三个文件，git 认不认 ────────────────────────────
# 线上是照着仓库重建的：这三个少一个，线上就是另一台机器。
该跟踪的 = ["主程序.py", "问模型.py", "记账演示.db"]
跟踪了 = set(git("ls-files").splitlines())
缺 = [f for f in 该跟踪的 if f not in 跟踪了]
记(not 缺, "仓库里有三样必需品", "缺：" + "、".join(缺) if 缺 else "主程序 / 问模型 / 账本母本 都在")


# ── ② 会变的那个，反过来不能进仓库 ───────────────────────────────
# 我的账本.db 是你本地跑出来的（写过 y，笔数已经变了）。
# 它进仓库 = 把一份改过的账本发给所有人，而且以后每次 status 都是脏的。
被忽略 = git("check-ignore", "我的账本.db") != ""
记(被忽略, "我的账本.db 被 .gitignore 挡住", "已忽略" if 被忽略 else "!! 没被忽略，可能被误提交")


# ── ③ 账本母本里真有一张能查的表 ────────────────────────────────
# 光有文件不够：搬过去是个空壳子，`SELECT ... FROM 记录` 一样报 no such table。
母本 = os.path.join(这里, "记账演示.db")
表 = 笔数 = 0
if os.path.exists(母本):
    连接 = sqlite3.connect(母本)
    try:
        表 = 连接.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='记录'"
        ).fetchone()[0]
        笔数 = 连接.execute("SELECT COUNT(*) FROM 记录").fetchone()[0]
    except sqlite3.Error:
        pass
    finally:
        连接.close()
记(表 == 1 and 笔数 == 21, "账本母本：表在、21 笔",
   f"表 {表} 张，共 {笔数} 笔" if os.path.exists(母本) else "!! 文件根本不在")


# ── ④ 外面那三张脸还认得出这个函数 ──────────────────────────────
# web 和体检都只传两个参数。第三个参数一旦没了默认值，它们当场 TypeError。
sys.path.insert(0, 这里)
import 主程序  # noqa: E402

参数们 = inspect.signature(主程序.回答一个问题).parameters
第三个 = list(参数们.values())[2]
记(第三个.default is None, "回答一个问题(问题, 块们, 本子=None)",
   f"第三个参数 = {第三个.name}，默认值 = {第三个.default!r}")


# ── ⑤ web 那扇门还是两参数在敲 ──────────────────────────────────
门 = os.path.join(这里, "web", "服务.py")
门文 = open(门, encoding="utf-8").read() if os.path.exists(门) else ""
记("回答一个问题(单子.问题, 块们)" in 门文, "web/服务.py 调用没变",
   "还是两参数" if "回答一个问题(单子.问题, 块们)" in 门文 else "!! 找不到那行，接口可能被动过")


# ── ⑥ 第 9 课那笔账：str + dict 会当场 TypeError ─────────────────
# 这个错误只在"真调了工具"那条路上才出现 —— 不跑工具永远看不见，所以放尺子上。
源 = open(os.path.join(这里, "主程序.py"), encoding="utf-8").read()
记('" + 申请' not in 源, "没有 str + dict 那种写法", "干净" if '" + 申请' not in 源 else "!! 又写回去了")


# ── ⑦ 线上没有键盘：得先问"有没有终端"，不能只等 EOFError ─────────
# 容器里的 stdin 是"一根永远没人说话的空管"：input() 不抛 EOF，而是一直等 → 504。
记(
    "sys.stdin.isatty()" in 源,
    "闸门先问 isatty 再 input",
    "有" if "sys.stdin.isatty()" in 源 else "!! 只靠 EOFError，线上会卡到 504",
)


# ── ⑧ 本地这把尺子先绿，才配谈线上 ──────────────────────────────
# 这一项不跑体检（要 2 分钟），只提醒：推之前自己跑一次。
记(True, "（手动）python _端到端体检.py", "误拒 0 / 误答 0 再推")


# ── 打印 ────────────────────────────────────────────────────────
print()
for 过, 名字, 说明 in 结果:
    牌 = "[OK]" if 过 else "[XX]"
    print(f"  {牌} {名字:<26} {说明}")
过数 = sum(1 for 过, _, _ in 结果 if 过)
print()
print(f"自检 {len(结果)} 项，过 {过数} 项")
if 过数 < len(结果):
    print("有 [XX] 先别推 —— 线上不会报错，只会某只手伸出去时答不上。")
