# -*- coding: utf-8 -*-
"""拿"标准答案表"当尺子，量检索到底行不行。

用同一批题、同一批块，跑两套算法，看"对的块"进没进前 3：

    cd "D:/CC Switch/问答机器人"
    python _标准答案体检.py

只读，不改任何东西。答案表里写 `对的块 = xxx.md 行NNN` 的行会被自动读进来。
"""

import re
from pathlib import Path

import 检索
import 检索_向量

答案表 = Path(__file__).resolve().parent / "标准答案表.txt"

# 表里一行长这样：   对的块 = python-learning-2026-09-01.md 行99
对的块样式 = re.compile(r"^对的块\s*=\s*(\S+\.md)\s+行(\d+)")
题号样式 = re.compile(r"^(\d+)\)")


def 读答案表() -> tuple[dict[int, str], dict[int, set[tuple[str, int]]]]:
    """把标准答案表读成两份：题目本身、以及每题的 {(文件, 行号), ...}。

    2026-10-17 改：题目不再写死在代码里，**以表为准** —— 表里加一题，
    这里自动多量一题，不用改代码。
    """
    题目表: dict[int, str] = {}
    表: dict[int, set[tuple[str, int]]] = {}
    当前题 = 0
    for 行 in 答案表.read_text(encoding="utf-8").splitlines():
        剥 = 行.strip()
        号 = 题号样式.match(剥)
        # 只有顶格写的 `1)` 才算题号。缩进的 `1)` 是题下的说明，
        # 文件末尾「标错的 6 条（存档）」也长这样，别把它们当题目。
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
    """老算法（数撞了几个字）—— `检索.py` 里那几个零件还在，拿来当对照。"""
    权重 = 检索.建权重表(块们)
    return sorted(块们, key=lambda 块: 检索.打分(问题, 块, 权重), reverse=True)[:取几块]


def 跑一套(名: str, 找相关, 块们, 题目表, 表) -> tuple[int, int]:
    print("=" * 74)
    print(f"【{名}】")
    总命中 = 0       # 块级：对的块进了几个
    总应有 = 0
    题命中 = 0       # 题级：有几道题至少进了一个对的块
    for i in sorted(题目表):
        问题 = 题目表[i]
        对的 = 表.get(i, set())
        前几 = 找相关(问题, 块们, 3)
        命中 = [块 for 块 in 前几 if (块["文件"], 块["行号"]) in 对的]
        总命中 += len(命中)
        总应有 += len(对的)
        if 对的 and 命中:
            题命中 += 1

        if 对的:
            标记 = "✅" if 命中 else "❌"
            明细 = "、".join(f"{块['文件'].replace('python-learning-','')}:{块['行号']}" for 块 in 命中)
            print(f"  {标记} {i}) {问题}    对的块 {len(对的)} 个，进了 {len(命中)} 个  {明细}")
        else:
            print(f"  ⚠️ {i}) {问题}    —— 表里没标对的块（语料里没有）")

        for 名次, 块 in enumerate(前几, 1):
            勾 = "✓" if (块["文件"], 块["行号"]) in 对的 else " "
            短名 = 块["文件"].replace("python-learning-", "").replace(".md", "")
            print(f"         {勾} 第{名次}  {短名}:{块['行号']:<4d} {块['标题'][:44]}")
        print()

    有答案的题 = [i for i in sorted(题目表) if 表.get(i)]
    print(f"  ── {名}小结：题级 {题命中}/{len(有答案的题)} 道至少进了一个对的块；"
          f"块级 {总命中}/{总应有} 个对的块进了前 3 ──")
    return 总命中, 题命中


def main() -> None:
    题目表, 表 = 读答案表()
    块们 = 检索.可用块()

    print(f"可用块 {len(块们)} 个（已扔掉空壳和台账）")
    有答案 = [i for i in sorted(题目表) if 表.get(i)]
    print(f"标准答案表：{len(题目表)} 道题，其中 {len(有答案)} 道标了答案，"
          f"共 {sum(len(v) for v in 表.values())} 条对的块")
    没答案 = [f"{i}) {题目表[i]}" for i in sorted(题目表) if not 表.get(i)]
    if 没答案:
        print("还没标答案的题：" + "；".join(没答案))
    print()

    甲块, 甲题 = 跑一套("撞词版（老算法·对照组）", 撞词版找相关, 块们, 题目表, 表)
    乙块, 乙题 = 跑一套("向量版（现在线上跑的）", 检索_向量.找相关, 块们, 题目表, 表)

    print("=" * 74)
    print(f"块级：撞词版 {甲块} 个  →  向量版 {乙块} 个")
    print(f"题级：撞词版 {甲题} 题  →  向量版 {乙题} 题")
    print("⚠️ 没标答案的题（比如语料里压根没有的）只能贡献 0。")


if __name__ == "__main__":
    main()
