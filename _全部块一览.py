# -*- coding: utf-8 -*-
"""把语料里所有块导出成一张一览表，供人工挑"哪块答得上这道题"。

只读，不改任何东西。跑完生成 _全部块一览.txt。

跑法：
    cd "D:/CC Switch/问答机器人"
    python _全部块一览.py
"""

from pathlib import Path

import 切块

输出文件 = Path(__file__).resolve().parent / "_全部块一览.txt"

五个问题 = [
    "1) 闭包是什么",
    "2) 装饰器是干嘛的",
    "3) with 语句怎么用",
    "4) 字典怎么按值排序",
    "5) 虚拟环境是干嘛的",
]


def 摘要(正文: str, 几字: int = 70) -> str:
    """取正文头一行，太长的掐掉。"""
    头一行 = ""
    for 行 in 正文.splitlines():
        剥 = 行.strip()
        if 剥 and not 剥.startswith("```"):
            头一行 = 剥
            break
    if len(头一行) > 几字:
        头一行 = 头一行[:几字] + "…"
    return 头一行


def main() -> None:
    块们 = 切块.切全部()

    行们: list[str] = []
    行们.append("语料里所有块 · 一览表")
    行们.append("=" * 70)
    行们.append("")
    行们.append("这是给 `标准答案表.txt` 用的。别去翻 28 篇笔记了，")
    行们.append("在这一份里 Ctrl+F 搜关键词就行。")
    行们.append("")
    行们.append("要标的 5 道题：")
    for 题 in 五个问题:
        行们.append(f"    {题}")
    行们.append("")
    行们.append("判断标准（就一句）：**只读这一块，能不能答上那道题。**")
    行们.append("")
    行们.append("=" * 70)
    行们.append("")

    当前文件 = ""
    有正文的 = 0
    for 块 in 块们:
        if not 块["正文"].strip():
            continue                       # 空壳块不列，省得吵
        有正文的 += 1

        if 块["文件"] != 当前文件:
            当前文件 = 块["文件"]
            行们.append("")
            行们.append("─" * 70)
            行们.append(f"■ {当前文件}")
            行们.append("─" * 70)

        标题 = 块["标题"]
        字数 = len(块["正文"])
        行们.append(f"  [{有正文的:3d}] 行{块['行号']:<4d} {标题}   «{字数} 字»")
        行们.append(f"        {摘要(块['正文'])}")

    头部 = "\n".join(行们)
    输出文件.write_text(头部 + "\n", encoding="utf-8")

    print(f"总共 {len(块们)} 块，其中 {有正文的} 块有正文（空壳块没列进来）")
    print(f"写到：{输出文件}")


if __name__ == "__main__":
    main()
