r"""服务 —— 问答机器人的那扇门（web 版）。

    cd "D:\CC Switch\问答机器人\web"
    python -m uvicorn 服务:app --reload

    → 浏览器打开 http://127.0.0.1:8000

两个柜台：

    GET  /       展示窗   —— 端出 `页面.html`
    POST /问     问事处   —— 递 {"问题": "..."} 进去，回 {"答案": "..."}

⚠️ Key 只在服务端的环境变量里（`问模型.py` 自己读），前端永远碰不到它。
"""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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
