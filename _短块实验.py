# -*- coding: utf-8 -*-
"""实验：50 字硬门槛到底误伤了多少？把短块放回来会怎样？

只量，不改线上代码。跑法：

    cd "D:/CC Switch/问答机器人"
    python _短块实验.py

比这几种「短块怎么处理」的规则，看 9 道有答案的题里对的块进前 3 几个：

    当前          正文 < 50 字直接扔掉
    全放行        只扔 ## 进度，短块照常参加排名
    短块打折      全放行，但正文 < 50 字的块分数 × 0.8 / 0.9 / 0.95
    要有反引号    短块必须含 `代码` 才留下（只有状态/清单的空壳扔掉）
    要有反引号或句号  同上，或者含一个句号

⚠️ 会读 `_向量缓存.json`；缓存里没有的块会去调 embedding 接口。
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

import 切块
import 检索_向量

答案表 = Path(__file__).resolve().parent / "标准答案表.txt"


def 读表():
    题目表: dict[int, str] = {}
    答案: dict[int, set[tuple[str, int]]] = {}
    当前 = 0
    for 行 in 答案表.read_text(encoding="utf-8").splitlines():
        剥 = 行.strip()
        号 = re.match(r"^(\d+)\)", 剥)
        if 号 and not 行.startswith((" ", "\t")):
            当前 = int(号.group(1))
            题目表[当前] = 剥[号.end():].strip()
            答案.setdefault(当前, set())
            continue
        对 = re.match(r"^对的块\s*=\s*(\S+\.md)\s+行(\d+)", 剥)
        if 对 and 当前:
            答案[当前].add((对.group(1), int(对.group(2))))
    return 题目表, 答案


def 不是台账(块: dict) -> bool:
    return 块["标题"].strip() != "## 进度"


def 当前规则(块: dict) -> bool:
    return 不是台账(块) and len(块["正文"]) >= 50


def 全放行(块: dict) -> bool:
    return 不是台账(块)


def 短块要有反引号(块: dict) -> bool:
    return 不是台账(块) and (len(块["正文"]) >= 50 or "`" in 块["正文"])


def 短块要有反引号或句号(块: dict) -> bool:
    return 不是台账(块) and (
        len(块["正文"]) >= 50 or "`" in 块["正文"] or "。" in 块["正文"]
    )


def 跑(规则, 折扣, 全部, 块向量, 题目表, 答案, 问题向量们):
    命中 = 应有 = 0
    明细 = []
    题号们 = [i for i in sorted(题目表) if 答案.get(i)]
    for i in 题号们:
        对的 = 答案[i]
        应有 += len(对的)
        带分 = []
        for 块, 向 in zip(全部, 块向量):
            if not 规则(块):
                continue
            分 = 检索_向量.夹角(问题向量们[i], 向)
            if len(块["正文"]) < 50:
                分 *= 折扣
            带分.append((分, 块))
        带分.sort(key=lambda 对: 对[0], reverse=True)
        前3 = [块 for _, 块 in 带分[:3]]
        中 = sum(1 for 块 in 前3 if (块["文件"], 块["行号"]) in 对的)
        命中 += 中
        明细.append(f"{i}:{中}/{len(对的)}")
    return 命中, 应有, 明细


def main() -> None:
    题目表, 答案 = 读表()
    全部 = 切块.切全部()
    块向量 = 检索_向量.建块向量(全部)
    题号们 = [i for i in sorted(题目表) if 答案.get(i)]
    问题向量们 = dict(
        zip(题号们, 检索_向量.变成向量们([题目表[i] for i in 题号们]))
    )

    规则们 = [
        ("当前（<50 扔掉）", 当前规则, 1.0),
        ("全放行", 全放行, 1.0),
        ("全放行·短块×0.8", 全放行, 0.8),
        ("全放行·短块×0.9", 全放行, 0.9),
        ("全放行·短块×0.95", 全放行, 0.95),
        ("短块要有反引号", 短块要有反引号, 1.0),
        ("短块要有反引号或句号", 短块要有反引号或句号, 1.0),
    ]

    for 名, 规则, 折扣 in 规则们:
        中, 应, 明细 = 跑(规则, 折扣, 全部, 块向量, 题目表, 答案, 问题向量们)
        print(f"{名:<24} {中}/{应}   " + " ".join(明细))


if __name__ == "__main__":
    main()
