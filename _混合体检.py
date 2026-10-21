# -*- coding: utf-8 -*-
"""拿标准答案表当尺子，同时量四套找法：撞词 / 向量 / BM25 / 混合。

    cd "D:/CC Switch/问答机器人"
    python _混合体检.py

只读笔记，不改任何东西。BM25 / 混合还没填完时，会跳过那一行并告诉你。

两个数，先看题级：
    题级 = 有几道题至少进了一个对的块（掉下来 = 真有题答不上）
    块级 = 12 条对的块里有几条进了前 3（差一点 = 只是少摆了一块）
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import 检索
import 检索_向量

答案表 = Path(__file__).resolve().parent / "标准答案表.txt"
对的块样式 = re.compile(r"^对的块\s*=\s*(\S+\.md)\s+行(\d+)")
题号样式 = re.compile(r"^(\d+)\)")
取名次 = 3


def 读答案表() -> tuple[dict[int, str], dict[int, set[tuple[str, int]]]]:
    题目表: dict[int, str] = {}
    表: dict[int, set[tuple[str, int]]] = {}
    当前题 = 0
    for 行 in 答案表.read_text(encoding="utf-8").splitlines():
        剥 = 行.strip()
        号 = 题号样式.match(剥)
        if 号 and not 行.startswith((" ", "\t")):
            当前题 = int(号.group(1))
            题目表[当前题] = 剥[号.end():].strip()
            表.setdefault(当前题, set())
            continue
        对 = 对的块样式.match(剥)
        if 对 and 当前题:
            表[当前题].add((对.group(1), int(对.group(2))))
    return 题目表, 表


def 撞词版找相关(问题: str, 块们: list[dict], 取几块: int = 3) -> list[dict]:
    权重 = 检索.建权重表(块们)
    return sorted(块们, key=lambda 块: 检索.打分(问题, 块, 权重), reverse=True)[:取几块]


def 跑一套(名: str, 找相关, 块们, 题目表, 表) -> tuple[int, int] | None:
    总命中 = 0
    总应有 = 0
    题命中 = 0
    逐题: list[str] = []
    有答案的题 = [i for i in sorted(题目表) if 表.get(i)]
    try:
        for i in sorted(题目表):
            问题 = 题目表[i]
            对的 = 表.get(i, set())
            前几 = 找相关(问题, 块们, 取名次)
            命中 = [块 for 块 in 前几 if (块["文件"], 块["行号"]) in 对的]
            总命中 += len(命中)
            总应有 += len(对的)
            if 对的 and 命中:
                题命中 += 1
            逐题.append(f"{i}:{len(命中)}/{len(对的)}")
    except NotImplementedError as 错:
        print(f"  ⚠️ 【{名}】还没填完：{错}")
        return None
    except TypeError as 错:
        print(f"  ⚠️ 【{名}】跑到一半炸了（多半是某个 `<<< 填这里` 还是 None）：{错}")
        return None

    print(f"  【{名}】题级 {题命中}/{len(有答案的题)}   块级 {总命中}/{总应有}")
    print(f"          逐题 {' '.join(逐题)}")
    return 总命中, 题命中


def main() -> None:
    题目表, 表 = 读答案表()
    块们 = 检索.可用块()
    有答案 = [i for i in sorted(题目表) if 表.get(i)]
    总应有 = sum(len(表[i]) for i in 有答案)

    print(f"可用块 {len(块们)} 个；标准答案表 {len(题目表)} 道题，"
          f"{len(有答案)} 道有答案，共 {总应有} 条对的块。\n")

    结果 = {
        "撞词版": 跑一套("撞词版（对照组）", 撞词版找相关, 块们, 题目表, 表),
        "向量版": 跑一套("向量版（现在线上跑的）", 检索_向量.找相关, 块们, 题目表, 表),
    }

    # 这两个文件可能还没填完 —— 单独 import，方便告诉他是哪个文件
    try:
        import 检索_BM25
        结果["BM25"] = 跑一套("BM25（只按字面）", 检索_BM25.找相关, 块们, 题目表, 表)
    except Exception as 错:
        print(f"  ⚠️ 【BM25】跑不起来：{type(错).__name__}: {错}")
        结果["BM25"] = None

    try:
        import 检索_混合
        结果["混合"] = 跑一套("混合（向量 + BM25 · RRF）", 检索_混合.找相关, 块们, 题目表, 表)
    except Exception as 错:
        print(f"  ⚠️ 【混合】跑不起来：{type(错).__name__}: {错}")
        结果["混合"] = None

    print()
    print("=" * 62)
    print(f"{'找法':<10}{'题级':>10}{'块级':>12}")
    for 名, 值 in 结果.items():
        if 值 is None:
            print(f"{名:<10}{'—':>10}{'还没填完':>12}")
        else:
            块级, 题级 = 值
            print(f"{名:<10}{题级:>6}/{len(有答案)}{块级:>8}/{总应有}")
    print("=" * 62)
    print("先看题级：掉下来 = 真有题答不上；题级满、块级差一点 = 只是少摆了一块。")


if __name__ == "__main__":
    main()
