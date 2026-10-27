r"""服务 —— 问答机器人的那扇门（web 版）。

    cd "D:\CC Switch\问答机器人\web"
    python -m uvicorn 服务:app --reload

    → 浏览器打开 http://127.0.0.1:8000

两个柜台：

    GET  /       展示窗   —— 端出 `页面.html`
    POST /问     问事处   —— 递 {"问题": "..."} 进去，回 {"答案": "..."}

⚠️ Key 只在服务端的环境变量里（`问模型.py` 自己读），前端永远碰不到它。
"""
import threading
import queue
import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# 🆕 搬家的作业 ①：让 import 找得到隔壁那四个文件
#
#   这几行原来住在 `FastAPI小服务\`，那会儿写的是**死地址**：
#
#       sys.path.insert(0, r"D:\CC Switch\问答机器人")
#
#   现在搬进仓库里当 `web\` 了 —— 死地址就不能要了：
#   别人把仓库克隆到 D:\下载\notes-qa-bot，这行还指着我这台电脑的 D 盘，
#   在他那儿根本不存在。
#
#   要改成「**跟着这个文件自己走**」：
#
#       D:\CC Switch\问答机器人\web\服务.py      ← 这个文件
#       D:\CC Switch\问答机器人\                 ← 仓库根 = 它的上一层
#
#   `Path(__file__)` = **这个文件自己** —— 不管你现在站在哪个目录、它被搬到哪儿。
#   `.resolve()` = 变成完整的绝对路径。`.parent` = 它的上一层。
#
#   ── 答案：
#
#       这里   = Path(__file__).resolve().parent
#       仓库根 = 这里.parent          ← 再往上一层
#       sys.path.insert(0, str(仓库根))
# ══════════════════════════════════════════════════════════════════

这里 = Path(__file__).resolve().parent        # = …\问答机器人\web
仓库根 = 这里.parent                          # = …\问答机器人
sys.path.insert(0, str(仓库根))

import 检索
import 主程序


app = FastAPI()

块们 = 检索.可用块()          # 开店时读一次，之后每个顾客都用这一份


# ══════════════════════════════════════════════════════════════════
# 🆕 搬家的作业 ②：展示窗端哪个文件
#
#   同一个毛病，第二处。原来写的是：
#
#       return FileResponse("页面.html")
#
#   这是**相对路径** —— 「相对于你启动服务时站在哪个目录」。
#   站在 web\ 里启动就对，站在别处启动（比如仓库根 `python -m uvicorn web.服务:app`）
#   就找不到页面。自己电脑上碰巧对，别人那儿一碰就坏。
#
#   改成「跟着文件走」：`页面.html` 跟这个文件**住在同一个目录**，
#   也就是上面刚算出来的那个 `这里`。
#
#   ── 答案：
#
#       return FileResponse(str(这里 / "页面.html"))
#
#   ⚠️ Path 用 `/` 是「拼一段路径」，不是除法：
#        Path("a") / "b.html"   →   a\b.html
# ══════════════════════════════════════════════════════════════════
@app.get("/")
def 首页():
    return FileResponse(str(这里 / "页面.html"))


class 提问(BaseModel):
    问题: str = Field(min_length=1, max_length=200)


@app.post("/问")
def 问(单子: 提问) -> dict:
    try:
        答案 = 主程序.回答一个问题(单子.问题, 块们)
        return {"答案": 答案.replace("[[无答案]]", "笔记里没有相关内容。")}
    except RuntimeError as 错:
        # 店里出的事，得在门口挂块**有字**的牌子 ——
        # detail 那一栏里的字，会原样发给顾客（前端就靠它显示人话）。
        raise HTTPException(status_code=500, detail=f"店里出事了：{错}")


# ══════════════════════════════════════════════════════════════════
# 🆕 第 13 课 · TODO ②：再加一个柜台 —— GET /问流（一条一条发货）
#
#   材料：`Agent-复习速查.md`「第 13 课」；玩具版在 `web\_SSE网页演示.py`
#   前置：主程序.py 的 TODO ① 先做完（不然 回答一个问题 没有 打印 这个参数）
#
#   一个函数，五步：
#     ① 管子 = queue.Queue()
#     ② def 干活():
#           try:
#               主程序.回答一个问题(问题, 块们, 允许确认=False, 流式=True,
#                                   打印=lambda 段: 管子.put(段))
#           finally:
#               管子.put(None)              ← 出事也要放这个「收工记号」
#     ③ threading.Thread(target=干活, daemon=True).start()
#     ④ def 生成():
#           while True:
#               段 = 管子.get()
#               if 段 is None: break
#               yield "data: " + json.dumps({"字": 段}, ensure_ascii=False) + "\n\n"
#           yield "data: [DONE]\n\n"
#     ⑤ return StreamingResponse(生成(), media_type="text/event-stream",
#              headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
#
#   ⚠️ 流式=True 和 打印= 必须**一起**给：只给 打印 的话，模型那边整箱回来，
#      回调一次都不响 —— 网页一片空白，而且**不报错**
#   ⚠️ 那个 put(None) 是收工记号：少了它 生成() 里的 get() 永远等，请求永不结束
#   ⚠️ 这个柜台只收 GET（浏览器 EventSource 只会发 GET），问题只能用 ?问题=... 传
#   ⚠️ 要补的 import：json / queue / threading
#      ＋ from fastapi.responses import StreamingResponse
# ══════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════
# 🆕 第 16 课 · TODO ①：开一扇小窗 —— GET /状态
#
#   为什么要有它：线上隔壁（MCP 服务器）起不来时，你的代码**会自动退回本地**，
#   答案一模一样（262.00 一分不差）。所以"答得对"证明不了隔壁活着。
#   这扇小窗只回一件事：隔壁那两只手，在这个进程里有没有登记上。
#
#   就三行：
#     @app.get("/状态")
#     def 状态():
#         return {"隔壁": sorted(主程序.隔壁)}
#
#   ⚠️ 顺序：先问一个账本问题（那时才会去起隔壁），再查这个接口。
#   ⚠️ 别在这扇窗里调用 起隔壁() —— 它只负责"看一眼"，不负责"叫起来"。
# ══════════════════════════════════════════════════════════════════
@app.get("/状态")
def 状态():
    return {"隔壁": sorted(主程序.隔壁)}

@app.get("/问流")
def 问流(问题: str):
    管子 = queue.Queue()
    def 干活():
        try:
            主程序.回答一个问题(问题,块们,允许确认=False,流式=True,打印=lambda 段:管子.put(段))
        finally:
            管子.put(None)
    def 生成():
        while True:
            段 = 管子.get()
            if 段 is None:
                break
            yield "data: " + json.dumps({"字": 段},ensure_ascii=False) + "\n\n"
        yield "data: [DONE]\n\n"
    threading.Thread(target=干活, daemon=True).start()
    return StreamingResponse(生成(), media_type="text/event-stream",    
                         headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})