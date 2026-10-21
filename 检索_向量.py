# -*- coding: utf-8 -*-
"""跟 检索.py 干同一件事：从笔记里挑出跟问题最相关的几块。

**函数名、参数、吐出来的东西，跟 检索.py 一模一样** —— 只把中间那个"怎么算分"换了：

    老版（撞词）：分数 = 问题里的词，在块里撞上了几个
    新版（向量）：分数 = 夹角(问题向量, 块向量)        ← 只看意思，不看字

只读笔记，另外会写一个 `_向量缓存.json`（存算过的向量，省得每次重问一遍）。

跑法（先 cd 进来）：
    cd "D:/CC Switch/问答机器人"
    python 检索_向量.py

⚠️ cd 后面**必须带引号** —— 路径里有个空格（`CC Switch`）。不带引号在 cmd 里还能凑合，
   在 PowerShell 里直接报「找不到接受实际参数"Switch/问答机器人"的位置形式参数」。

规矩：**只改标着 `<<< 填这里` 的地方，别的一个字都别动。一共 3 处。**
⚠️ 标点一律英文半角（逗号 , 括号 () 引号 ""）。
"""

import json
import math
import os
import sys
from pathlib import Path

import requests

import 切块

sys.stdout.reconfigure(errors="replace")  # 笔记标题里有 ⭐ 这种怪符号，输出重定向到文件时不炸

接口 = "https://api.siliconflow.cn/v1/embeddings"
钥匙名 = "SILICONFLOW_API_KEY"
模型名 = "BAAI/bge-m3"
缓存文件 = Path(__file__).parent / "_向量缓存.json"
每批几条 = 32
最短正文 = 20


def 变成向量们(文字们: list[str]) -> list[list[float]]:
    """一次问一批，拿回一串向量 —— 就是 `_向量练习.py` 里 变成向量 的"批发版"。

    跟一对一那版比，只有两处不一样：
      身      input 传的是"一串文字"（列表），不是一句话
      捞数字  回来也是一串：[x["embedding"] for x in 回.json()["data"]]
    """
    钥匙 = os.environ.get(钥匙名)
    if not 钥匙:
        raise SystemExit("没找到环境变量 " + 钥匙名 + "，去 向量检索-复习速查.md 设好、重开终端。")

    头 = {"Authorization": "Bearer " + 钥匙}
    身 = {"model": 模型名, "input": 文字们}

    # <<< 填这里（1/3）：把上面三样交给 requests.post。
    #     提示：跟 _向量练习.py 里那行一模一样，只有 timeout 从 30 改成 60。
    回 = requests.post(接口,headers=头,json=身,timeout=60)

    if 回.status_code != 200:
        print("接口报错", 回.status_code)
        print(回.text[:300])
        回.raise_for_status()

    return [x["embedding"] for x in 回.json()["data"]]


def 夹角(甲: list[float], 乙: list[float]) -> float:
    """余弦相似度 —— 跟 _向量练习.py 里你写的那三行一模一样，直接搬过来的。

    1 = 方向一样，0 = 没关系。这里只用来当"分数"使。
    """
    点积 = sum(a * b for a, b in zip(甲, 乙))
    长度甲 = math.sqrt(sum(a * a for a in 甲))
    长度乙 = math.sqrt(sum(b * b for b in 乙))
    return 点积 / (长度甲 * 长度乙)


def 取块文字(块: dict) -> str:
    """一块笔记 → 要拿去变成向量的那段文字：标题 + 正文。"""
    return 块["标题"] + "\n" + 块["正文"]


def 建块向量(块们: list[dict]) -> list[list[float]]:
    """给每块算一个向量。**算过的存硬盘**，第二次跑直接读回来，不再重问一遍。

    ⚠️ 这段不用你填，先看它在干嘛 —— 它办的就是进度文件里那句：
       "同一句话的向量是定死的" → 所以能"算一次、存起来"。
       （474 块要问 15 批，约 20 秒；存下来以后是 0 秒。）
    """
    缓存: dict[str, list[float]] = {}
    if 缓存文件.exists():
        缓存 = json.loads(缓存文件.read_text(encoding="utf-8"))

    文字们 = [取块文字(块) for 块 in 块们]
    缺的 = [文 for 文 in 文字们 if 文 not in 缓存]
    if 缺的:
        print(f"  有 {len(缺的)} 块没算过，去问接口（每批 {每批几条} 条）……")
        for i in range(0, len(缺的), 每批几条):
            小批 = 缺的[i : i + 每批几条]
            for 文, 向量 in zip(小批, 变成向量们(小批)):
                缓存[文] = [round(数, 6) for 数 in 向量]
            print(f"    {min(i + 每批几条, len(缺的))}/{len(缺的)}")
        缓存文件.write_text(json.dumps(缓存, ensure_ascii=False), encoding="utf-8")
        print(f"  存好了：{缓存文件.name}（下次跑就不用再算了）")
    return [缓存[文] for 文 in 文字们]


def 找相关(问题: str, 块们: list[dict], 取几块: int = 3) -> list[dict]:
    """**跟 检索.py 里那个同名函数长一样、吐出来的东西也一样** —— 只换了中间两行。

    老版那边是：撞上几个词 × 词值多少钱，标题里的再乘 3。
    这里不用权重表了 —— 向量自己就带着"哪个字重要"。
    """
    块向量们 = 建块向量(块们)

    # <<< 填这里（2/3）：把问题也变成向量。
    #     提示：变成向量们 收"一串文字"、回"一串向量"；你只问了一句，取第 [0] 个。
    问题向量 = 变成向量们([问题])[0]

    带分的 = []
    for 块, 块向量 in zip(块们, 块向量们):
        # <<< 填这里（3/3）：这一块得几分 = 问题向量 和 这一块的向量 的夹角。
        #     提示：调用上面那个 夹角(...)，想想两个参数该传谁。
        得分 = 夹角(问题向量,块向量)
        带分的.append((得分, 块))

    带分的.sort(key=lambda 对: 对[0], reverse=True)
    return [对[1] for 对 in 带分的[:取几块]]


def 可用块() -> list[dict]:
    """跟 检索.py 里那个一模一样：切全部，扔掉光杆标题。"""
    return [块 for 块 in 切块.切全部() if len(块["正文"]) >= 最短正文]


if __name__ == "__main__":
    块们 = 可用块()
    print(f"可用块：{len(块们)}")
    print()
    for 问题 in ["闭包是什么", "asyncio 和线程池怎么选"]:
        print(f"===== 问：{问题} =====")
        for 块 in 找相关(问题, 块们):
            print(f"  {块['文件']}:{块['行号']}  {块['标题']}")
        print()
