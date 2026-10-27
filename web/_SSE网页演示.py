# -*- coding: utf-8 -*-
r"""第 13 课 · 在浏览器里看「整块到货」和「边收边打」的差别。

    cd "D:\CC Switch\问答机器人\web"
    python _SSE网页演示.py
    → 浏览器打开 http://127.0.0.1:8013

这个文件**不花 API 钱**：回答是假的，一个按钮点下去，左右两栏同时开工。
左边等到最后才有一整句；右边一个字一个字往外蹦。

它跟真服务的关系：这份是玩具，`服务.py` 里那条 `/问流` 就是照着它写的。
两处只不一样：
  ① 玩具的"干活的人"是个普通生成器；真服务里是 `主程序.回答一个问题`
     —— 那一位只会往回调里推，所以中间要垫一根 queue（见 `_SSE演示.py` 幕三）
  ② 玩具返回固定句子；真服务返回模型吐的字

注意：只 listen 127.0.0.1 —— 这是本地玩具，别让它暴露到局域网。
"""

import json
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

app = FastAPI()

假答案 = "闭包就是一个函数记住了它外面的变量，函数跑完了那个变量还在。"
一片几秒 = 0.06


def 假模型():
    """假装模型在吐字。真服务里这个位置是 `主程序.回答一个问题` 的 打印 回调。"""
    for 字 in 假答案:
        time.sleep(一片几秒)
        yield 字


@app.get("/整块")
def 整块() -> JSONResponse:
    """老路子：攒齐了才 return —— 这段时间浏览器那边一片空白。"""
    开始 = time.time()
    整句 = "".join(假模型())
    print(f"  [整块] {time.time() - 开始:.2f} 秒后一次交出 {len(整句)} 个字")
    return JSONResponse({"答案": 整句})


@app.get("/流")
def 流() -> StreamingResponse:
    """新路子：每出来一片就 yield 一片，连接一直开着。"""
    开始 = time.time()
    片数 = 0

    def 生成():
        nonlocal 片数
        for 字 in 假模型():
            片数 += 1
            if 片数 == 1:
                print(f"  [流] 首片 {time.time() - 开始:.2f} 秒就出去了")
            # 就这一行是 SSE 的全部格式：`data: ` + 一行 JSON + 一个空行
            yield "data: " + json.dumps({"字": 字}, ensure_ascii=False) + "\n\n"
        print(f"  [流] {time.time() - 开始:.2f} 秒说完，共 {片数} 片")
        yield "data: [DONE]\n\n"          # 关闸的牌子

    return StreamingResponse(
        生成(),
        media_type="text/event-stream",          # 少了它，浏览器不知道这是"一条一条来的"
        headers={"Cache-Control": "no-cache"},   # 别让中间任何一层把它存下来
    )


@app.get("/", response_class=HTMLResponse)
def 首页() -> HTMLResponse:
    return HTMLResponse(页面)


页面 = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>SSE 演示</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 32px auto; padding: 0 16px; }
  h1 { font-size: 20px; }
  button { padding: 8px 16px; font-size: 16px; }
  .两栏 { display: flex; gap: 16px; margin-top: 16px; }
  .栏 { flex: 1; }
  .栏 h2 { font-size: 15px; color: #555; margin: 0 0 8px; }
  pre { background: #f4f4f4; padding: 12px; white-space: pre-wrap; min-height: 120px; margin: 0; }
  .秒 { color: #888; font-size: 13px; }
</style>
</head>
<body>
  <h1>整块到货 vs 边收边打</h1>
  <button id="开跑">点一下，两边同时开工</button>
  <div class="两栏">
    <div class="栏">
      <h2>左边：/整块（老路）</h2>
      <pre id="左"></pre>
      <p class="秒" id="左秒"></p>
    </div>
    <div class="栏">
      <h2>右边：/流（SSE）</h2>
      <pre id="右"></pre>
      <p class="秒" id="右秒"></p>
    </div>
  </div>

<script>
  // 给学过 Python 的人：EventSource ≈ 一个"一直收"的 requests 响应。
  // 每来一条 data: 行，浏览器替你把前缀切掉，再调一次 onmessage。
  const 开跑 = document.getElementById("开跑");
  const 左 = document.getElementById("左");
  const 右 = document.getElementById("右");
  const 左秒 = document.getElementById("左秒");
  const 右秒 = document.getElementById("右秒");

  开跑.onclick = () => {
    左.textContent = "";   右.textContent = "";
    左秒.textContent = ""; 右秒.textContent = "";
    开跑.disabled = true;

    const 开始 = performance.now();
    let 剩 = 2;                     // 两条路各跑各的，都到齐了才准再按
    const 到齐 = () => { 剩 -= 1; if (剩 === 0) 开跑.disabled = false; };

    // ── 左边：老的 fetch，await 到底才有一句话 ──
    fetch("/整块")
      .then((响应) => 响应.json())
      .then((数据) => {
        左.textContent = 数据.答案;
        左秒.textContent = "整句到手：" + ((performance.now() - 开始) / 1000).toFixed(2) + " 秒";
        到齐();
      });

    // ── 右边：EventSource，来一条收一条 ──
    const 源 = new EventSource("/流");
    let 首字 = null;

    源.onmessage = (事件) => {
      if (事件.data === "[DONE]") {
        源.close();   // 必须关：不关的话它过一会儿会自己重连，把同一个问题再问一遍
        右秒.textContent += " ｜ 说完：" + ((performance.now() - 开始) / 1000).toFixed(2) + " 秒";
        到齐();
        return;
      }
      if (首字 === null) {
        首字 = performance.now();
        右秒.textContent = "首字：" + ((首字 - 开始) / 1000).toFixed(2) + " 秒";
      }
      const 数据 = JSON.parse(事件.data);
      右.textContent += 数据.字;
    };

    源.onerror = () => {
      源.close();
      右秒.textContent += " ｜ 连接断了";
      到齐();
    };
  };
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("浏览器打开 http://127.0.0.1:8013")
    uvicorn.run(app, host="127.0.0.1", port=8013, log_level="warning")
