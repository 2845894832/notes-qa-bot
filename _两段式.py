# -*- coding: utf-8 -*-
"""两段式：粗筛 + 精排（rerank）。

【它解决的是哪个毛病】

向量算分有个特点：**分数挤在一起**。看这几个真实输出 ——

    问「装饰器是干嘛的」  向量前 3：0.615 / 0.562 / 0.541     ← 第1和第3只差 0.07
    问「with 语句怎么用」  向量前 3：0.617 / 0.538 / 0.525     ← 第1和第3只差 0.09

挤在一起的意思是：**分不出谁真谁假。** 第 1 名和第 3 名几乎并列，
你取前 3 拿到的就是"三个差不多像的"，里面混着真答案和陪跑的。

【两段式怎么治它】

像招聘：

  第一段「粗筛」= HR 看简历。快、便宜、**宁可多放几个进来**，取前 20。
                     （用向量，475 块全扫一遍也不贵）
  第二段「精排」= 面试官。慢、贵，只对这 20 个，但**能把分拉开**。
                     （用 rerank 模型，问题是"这条和问题到底多相关"）

⭐ 精排的价值**不是"分更高"，是"分拉开"** —— 第 1 名和第 2 名之间出现断崖，
   一眼就知道该信谁。下面两个数并排看就是这个。

跑法（先进这个文件夹）：
    cd "D:/CC Switch/问答机器人"
    python _两段式.py
"""

import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(errors="replace")

import 检索_向量

粗筛取几块 = 20
精排取几块 = 3
重排模型 = "BAAI/bge-reranker-v2-m3"
重排网址 = "https://api.siliconflow.cn/v1/rerank"

问题们 = ["闭包是什么", "装饰器是干嘛的", "with 语句怎么用"]


def 精排(问题, 候选):
    """拿问题 + 这 20 块，问 rerank 模型：谁最相关。返回 [(分, 块)] 排好序。"""
    钥匙 = os.environ["SILICONFLOW_API_KEY"]
    正文们 = [块["标题"].strip() + "\n" + 块["正文"] for 块 in 候选]
    请求体 = json.dumps(
        {"model": 重排模型, "query": 问题, "documents": 正文们, "top_n": len(候选)}
    ).encode()
    请求 = urllib.request.Request(
        重排网址,
        data=请求体,
        headers={"Authorization": f"Bearer {钥匙}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(请求, timeout=60) as 回应:
        数据 = json.loads(回应.read())
    return [(项["relevance_score"], 候选[项["index"]]) for 项 in 数据["results"]]


def 打前几(标题, 带分, 取几):
    print(f"  ── {标题} ──")
    for 分, 块 in 带分[:取几]:
        print(f"     {分:.3f}   {块['标题'].strip()}")
    第一名, 第二名 = 带分[0][0], 带分[1][0]
    print(f"     ⭐ 第1名 - 第2名 = {第一名 - 第二名:.3f}   {'← 有断崖' if 第一名 - 第二名 > 0.1 else '← 并列，分不清'}")


def main():
    块们 = 检索_向量.可用块()
    块向量们 = 检索_向量.建块向量(块们)

    for 问题 in 问题们:
        问题向量 = 检索_向量.变成向量们([问题])[0]
        带分 = sorted(
            ((检索_向量.夹角(问题向量, 块向量), 块) for 块, 块向量 in zip(块们, 块向量们)),
            key=lambda 对: 对[0],
            reverse=True,
        )
        候选 = [块 for _, 块 in 带分[:粗筛取几块]]

        print(f"\n══ 问：{问题}")
        打前几(f"第一段 粗筛（向量，从 {len(块们)} 块里取前 {粗筛取几块}，这里只显示前 {精排取几块}）", 带分, 精排取几块)
        打前几(f"第二段 精排（rerank，只对这 {粗筛取几块} 块重算）", 精排(问题, 候选), 精排取几块)


if __name__ == "__main__":
    main()
