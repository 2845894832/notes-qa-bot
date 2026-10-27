# -*- coding: utf-8 -*-
"""第 13 课 · SSE —— 让浏览器也「边下边播」。

这个文件**不花 API 钱**：回答是假的，只为先看清三件事 ——

  幕一  同一个回答：攒齐了再交 vs 生成一片交一片（量时间，能数出来）
  幕二  网页那条管道上跑的字长什么样：`data: ` 前缀 / 空行 / `[DONE]`
  幕三  回调是「推」、yield 是「拉」，中间得插一根管子（Queue + 线程）
  幕四  正文里有换行会怎样 —— 这就是为什么每片要 JSON 包一层

一句话：终端是 `print(flush=True)`，网页是 SSE。同一个流水线，换了个出水口。
"""

import json
import queue
import threading
import time

真答案 = "闭包就是一个函数记住了它外面的变量"


def 假回答():
    """假装模型在吐字：一片一片、中间有停顿。"""
    for 字 in 真答案:
        time.sleep(0.12)
        yield 字


print("=" * 62)
print("幕一：同一个回答，两种交法")
print("=" * 62)

开始 = time.time()
整句 = "".join(假回答())
用时 = time.time() - 开始
print(f"  攒齐了再交：等了 {用时:.2f} 秒，屏幕上才出现第一行，一下蹦出 {len(整句)} 个字")
print(f"              「{整句}」")

print()
开始 = time.time()
片数 = 0
首片 = None
print("  生成一片交一片：", end="")
for 片 in 假回答():
    片数 += 1
    if 首片 is None:
        首片 = time.time() - 开始
    print(片, end="", flush=True)
用时 = time.time() - 开始
print()
print(f"              → 首片 {首片:.2f} 秒（整块那会儿要 {用时:.2f} 秒），一共 {片数} 片")
print()
print("  ★ 两次总耗时一样 —— 流式不是让模型变快，是让你早 {:.1f} 秒看见东西。".format(用时 - 首片))


print()
print("=" * 62)
print("幕二：网页上跑的字，长这样")
print("=" * 62)
print("  服务端发出去的原文（每片一行，行尾两个换行）：")
print("  " + "-" * 56)
原文 = (
    'data: {"字": "闭"}\n\n'
    'data: {"字": "包"}\n\n'
    'data: [DONE]\n\n'
)
for 行 in 原文.splitlines():
    print("    " + (行 if 行 else "（空行）"))
print("  " + "-" * 56)
print()
print("  浏览器收到之后，只做三件事：")
print("    ① 只认 `data: ` 开头的行 —— 前面那 6 个字符切掉，剩下的才是货")
print("    ② 空行跳过 —— 它只是「这一节到此为止」的切口")
print("    ③ `[DONE]` 就收工 —— 它不是 JSON，硬塞给 JSON.parse 会当场炸")
print()
收到 = []
for 行 in 原文.splitlines():
    if not 行.startswith("data: "):
        continue
    正文 = 行[len("data: "):]
    if 正文 == "[DONE]":
        break
    收到.append(json.loads(正文)["字"])
print(f"  照这三条规则收一遍：收到 {len(收到)} 片 → 「{''.join(收到)}」")


print()
print("=" * 62)
print("幕三：推 vs 拉 —— 中间那根管子")
print("=" * 62)
print("  干活的那位只会「往里放」（回调），FastAPI 要的是「自己往外拿」（yield）。")
print("  一个往里倒、一个往外舀，中间必须有个桶 —— queue.Queue。")
print()

管子: queue.Queue = queue.Queue()


def 干活的():
    """形态跟 `问模型.发消息` 的 打印 回调一模一样：拿到一段就交出去。"""
    for 片 in 假回答():
        管子.put(片)
    管子.put(None)          # ★ 最后一件事：往管子里放一个「没了」的记号


def 生成器():
    """形态跟 web 那条路由里 `生成()` 一模一样：拿到一个就吐一个。"""
    while True:
        片 = 管子.get()      # 管子里没有就等着（不会空转烧 CPU）
        if 片 is None:
            break
        yield 片


线程 = threading.Thread(target=干活的, daemon=True)
线程.start()

开始 = time.time()
收 = []
for 片 in 生成器():
    收.append(片)
    print(f"    第 {len(收):2d} 片  {time.time() - 开始:.2f} 秒   {片}")
print()
print(f"  ★ {len(收)} 片一片不少、顺序没乱：「{''.join(收)}」")
print("    干活的那位自己跑完了就退出；生成器靠那个 None 知道该收工。")
print("    注意：少了那个 None，for 循环会一直挂在 get() 上 —— 请求永远不结束。")


print()
print("=" * 62)
print("幕四：正文里有换行，直接塞进 data: 会怎样")
print("=" * 62)
含换行 = "第一行\n第二行"
坏原文 = f"data: {含换行}\n\n"
print("  服务端发出去（看起来挺正常）：")
print("    " + repr(坏原文))
print()

坏收 = []
for 行 in 坏原文.splitlines():
    if not 行.startswith("data: "):
        continue
    坏收.append(行[len("data: "):])
print(f"  浏览器收到：{坏收}")
print(f"  → 只剩 {len(坏收)} 行，「第二行」凭空消失：它没带 `data: ` 前缀，被当成废行扔了。")
print()

好原文 = "data: " + json.dumps({"字": 含换行}, ensure_ascii=False) + "\n\n"
好收 = []
for 行 in 好原文.splitlines():
    if not 行.startswith("data: "):
        continue
    好收.append(json.loads(行[len("data: "):])["字"])
print("  JSON 包一层之后：")
print("    " + repr(好原文))
print(f"  → 收到 {len(好收)} 条，拼回来：{''.join(好收)!r} —— 换行变成了 \\n 这两个字符，跑不出去了。")
print()
print("  ★ 每片都用 json.dumps 包一层：换行、引号、emoji 这些会咬人的东西，全被压成一行。")
print("    （不包也能做，但得自己给每个换行补一个 `data: ` 前缀 —— 那是给自己挖坑。）")
print()
print("=" * 62)
print("跑完了。下一步：`web\\_SSE网页演示.py`，在浏览器里看同一件事。")
print("=" * 62)
