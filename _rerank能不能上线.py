# -*- coding: utf-8 -*-
"""实验：rerank / 融合，到底能不能把「同文件两块抢座」治好。

只量，不改线上代码。跑法：

    cd "D:/CC Switch/问答机器人"
    python _rerank能不能上线.py

量 5 道有标准答案的题，比这几种排法「对的块进前 3 几个」：

    纯向量       现在线上跑的
    纯 rerank    粗筛 20 块 → 只用 rerank 分取前 3
    RRF          向量名次 + rerank 名次，倒数相加（k=10 / 60）
    加权         向量分和 rerank 分各自拉回 0~1，再按 w 混合

⚠️ 只读笔记；rerank 会真的调接口（5 次）。
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

import 检索
import 检索_向量
import _两段式

答案表 = Path(__file__).resolve().parent / "标准答案表.txt"
题目 = [
    "闭包是什么",
    "装饰器是干嘛的",
    "with 语句怎么用",
    "字典怎么按值排序",
    "虚拟环境是干嘛的",
]
粗筛取几块 = 20
取名次 = 3


def 读对的块() -> dict[int, set[tuple[str, int]]]:
    """从 标准答案表.txt 里读「对的块 = xxx.md 行NNN」。"""
    import re

    表: dict[int, set[tuple[str, int]]] = {}
    当前 = 0
    for 行 in 答案表.read_text(encoding="utf-8").splitlines():
        剥 = 行.strip()
        号 = re.match(r"^(\d+)\)", 剥)
        if 号:
            当前 = int(号.group(1))
            表.setdefault(当前, set())
            continue
        对 = re.match(r"^对的块\s*=\s*(\S+\.md)\s+行(\d+)", 剥)
        if 对 and 当前:
            表[当前].add((对.group(1), int(对.group(2))))
    return 表


def 拉回01(分数们: list[float]) -> list[float]:
    """最小-最大归一化。全是同一个数时返回全 0，避免除零。"""
    低, 高 = min(分数们), max(分数们)
    if 高 == 低:
        return [0.0 for _ in 分数们]
    return [(分 - 低) / (高 - 低) for 分 in 分数们]


def 数命中(前几: list[dict], 对的: set[tuple[str, int]]) -> int:
    return sum(1 for 块 in 前几 if (块["文件"], 块["行号"]) in 对的)


def main() -> None:
    块们 = 检索.可用块()
    块向量们 = 检索_向量.建块向量(块们)
    表 = 读对的块()

    总计 = {
        "纯向量": 0,
        "纯rerank": 0,
        "RRF k=10": 0,
        "RRF k=60": 0,
        "加权 w=0.3": 0,
        "加权 w=0.5": 0,
        "加权 w=0.7": 0,
    }
    应有 = 0

    for i, 问题 in enumerate(题目, 1):
        对的 = 表.get(i, set())
        应有 += len(对的)

        问题向量 = 检索_向量.变成向量们([问题])[0]
        向量分 = [
            (检索_向量.夹角(问题向量, 块向量), 块)
            for 块, 块向量 in zip(块们, 块向量们)
        ]
        向量分.sort(key=lambda 对: 对[0], reverse=True)
        候选 = [块 for _, 块 in 向量分[:粗筛取几块]]

        # rerank：候选 20 块重打分，返回 [(分, 块)]，已按分排好
        rerank带分 = _两段式.精排(问题, 候选)
        rerank名次 = {id(块): 名次 for 名次, (_, 块) in enumerate(rerank带分, 1)}
        向量名次 = {id(块): 名次 for 名次, (_, 块) in enumerate(向量分, 1)}
        向量分表 = {id(块): 分 for 分, 块 in 向量分}
        rerank分表 = {id(块): 分 for 分, 块 in rerank带分}

        纯向量前3 = [块 for _, 块 in 向量分[:取名次]]
        纯rerank前3 = [块 for _, 块 in rerank带分[:取名次]]

        def 融合前3(算分):
            带分 = [(算分(块), 块) for _, 块 in rerank带分]
            带分.sort(key=lambda 对: 对[0], reverse=True)
            return [块 for _, 块 in 带分[:取名次]]

        def rrf(块, k):
            return 1 / (k + 向量名次[id(块)]) + 1 / (k + rerank名次[id(块)])

        # 加权：在候选 20 块里各自拉回 0~1
        向量01 = dict(zip([id(块) for _, 块 in rerank带分],
                          拉回01([向量分表[id(块)] for _, 块 in rerank带分])))
        rerank01 = dict(zip([id(块) for _, 块 in rerank带分],
                            拉回01([rerank分表[id(块)] for _, 块 in rerank带分])))

        def 加权分(w):
            return lambda 块: w * 向量01[id(块)] + (1 - w) * rerank01[id(块)]

        结果 = {
            "纯向量": 数命中(纯向量前3, 对的),
            "纯rerank": 数命中(纯rerank前3, 对的),
            "RRF k=10": 数命中(融合前3(lambda 块: rrf(块, 10)), 对的),
            "RRF k=60": 数命中(融合前3(lambda 块: rrf(块, 60)), 对的),
            "加权 w=0.3": 数命中(融合前3(加权分(0.3)), 对的),
            "加权 w=0.5": 数命中(融合前3(加权分(0.5)), 对的),
            "加权 w=0.7": 数命中(融合前3(加权分(0.7)), 对的),
        }
        for 名, 数 in 结果.items():
            总计[名] += 数
        print(f"{i}) {问题}  对的 {len(对的)} 个   " +
              "  ".join(f"{名} {数}/{len(对的)}" for 名, 数 in 结果.items()))

    print()
    print("=" * 60)
    for 名, 数 in 总计.items():
        print(f"  {名:<12} {数} /{应有}")
    print("=" * 60)
    print("⚠️ 第 4 题语料里没答案，它只能贡献 0。")


if __name__ == "__main__":
    main()
