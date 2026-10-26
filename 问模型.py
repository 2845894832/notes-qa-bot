# -*- coding: utf-8 -*-
"""项目第 ③ 步的第一小块：跟模型说话。

这一小块只做一件事：**确认 Key 通了，看看你的账号能用哪些模型名。**

为什么 Key 放在请求头（headers）里，不拼进网址：
    网址会一路被记下来 —— 服务器日志、代理、浏览器历史、报错截图里都有。
    请求头只跟着这一次请求走。所以 Key 一律放 headers，不放 params。
    （这就是 requests 那关讲的 params 改网址 / headers 不改网址）

⚠️ 这个文件里永远不出现 Key 本身，只出现 os.environ.get("DEEPSEEK_API_KEY")。
"""

import json
import os
import time
import requests

接口 = "https://api.deepseek.com"
钥匙名 = "DEEPSEEK_API_KEY"


def 拿钥匙() -> str:
    """从环境变量里取 Key。取不到就直接报错，别带着空 Key 去请求。"""
    钥匙 = os.environ.get(钥匙名)
    if not 钥匙:
        raise RuntimeError(
            f"环境变量 {钥匙名} 没拿到。先 setx 一遍，然后**开一个新终端**再跑。"
        )
    return 钥匙


def 列模型() -> dict:
    """问接口：我这个账号能用哪些模型。返回它给的原话。"""
    # TODO 1 —— 用 requests.get 打这个地址：接口 + "/models"
    #   请求头里要有两样东西：
    #       "Authorization": "Bearer " + 钥匙      ← 注意 Bearer 后面有个空格
    #       "Content-Type": "application/json"      ← 这次可以不加，先试试不加会不会通
    #   GET 请求的参数用 headers= 传进去
    钥匙 = 拿钥匙()
    请求头 = {"Authorization": "Bearer " + 钥匙, "Content-Type": "application/json"}
    r = requests.get(接口 + "/models", headers=请求头, timeout=30)
    # TODO 2 —— 先别急着掏里面的东西。把拿到的 r.json() 原样 return 出去，
    #   我们看一眼它到底长什么样，再决定怎么掏。
    #   （顺手加上 raise_for_status()，Key 错的时候它会比现在报得清楚）
    r.raise_for_status()
    return r.json()


模型名 = "deepseek-flash"  # 从刚才那张列表里挑的，便宜的那个
聊天地址 = 接口 + "/chat/completions"  # 注意不是 /models 了

def 拼碎片(碎片们: list[dict]) -> dict:
    """把一串 delta 拼成一条 message（跟非流式拿到的那条形状一样）。

    返回：{"role": "assistant", "content": "拼好的正文"}
          有申请就再加一条 "tool_calls": [{"id":..., "type":"function",
                                          "function": {"name":..., "arguments":...}}, ...]
    """
    正文 = ""
    申请们: dict[int, dict] = {}
    for 片 in 碎片们:
        if 片.get("content") is not None:
            正文 += 片["content"]
        for 申 in 片.get("tool_calls") or []:
            壳 = 申请们.setdefault(
                申["index"],
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if 申.get("id"):
                壳["id"] = 申["id"]
            函数 = 申.get("function") or {}
            if 函数.get("name"):
                壳["function"]["name"] = 函数["name"]
            壳["function"]["arguments"] += 函数.get("arguments") or ""
    消息 = {"role": "assistant", "content": 正文}
    if 申请们:
        消息["tool_calls"] = [申请们[序] for 序 in sorted(申请们)]
    return 消息
def 发消息(
    本子: list[dict],
    菜单: list[dict] | None = None,
    流式: bool = False,
    打印=None,
    计时: dict | None = None,
) -> dict:
    """把**一整本**消息发过去（可以带工具清单），返回 choices[0]。

    跟 真问一次 的区别只有一个：真问一次只塞一条 user；
    这里本子里有什么就发什么 —— system、user、assistant（带申请单）、tool 回音，一条不落。
    第 7 课那句话在这儿：模型没有记性，它看到的永远只有这一本。

    ⚠️ 这一只没套重试壳子。网络抽风就重跑；要套，照下面 问一句 那五步。

    ── 第 12 课加的两个开关（都有默认值，外面三个调用点一个字不用改）──
    流式=True   : 正文边收边打，**返回的形状跟非流式一模一样**（{"message":…, "finish_reason":…}）
    打印=某个函数: 流式时每来一段正文就调它一次。不传 = 不打到屏幕上
    计时=某个dict : 传了就往里写 {"首包": 秒, "首字": 秒}，给记录仪用
    """
    请求头 = {
        "Authorization": "Bearer " + 拿钥匙(),
        "Content-Type": "application/json",
    }
    请求体: dict = {"model": 模型名, "messages": 本子}
    if 菜单:
        请求体["tools"] = 菜单

    if not 流式:
        r = requests.post(聊天地址, headers=请求头, json=请求体, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]

    # ══════════════ 流式分支（第 12 课）· TODO 流式 ① ══════════════
    # 做完返回的东西，必须跟上面那句 return 长得一模一样：
    #   {"message": 拼好的那条, "finish_reason": 最后一次看到的值}
    #
    #   ① 先跟服务器说"要流"：请求体["stream"] = True
    #      再给 requests.post 加一个 stream=True（两个都要，少一个都不流）
    #   ② 准备好四样：开始 = time.time() / 首包 = 首字 = None
    #                  碎片们 = [] / 最后原因 = None
    #   ③ for 行 in r.iter_lines(decode_unicode=True):
    #         空行 或 不是 "data: " 开头 → continue
    #         正文行 == "[DONE]" → break
    #         整片 = json.loads(正文行)["choices"][0]
    #         片   = 整片.get("delta") or {}
    #         碎片们.append(片)
    #         首包：`if 首包 is None` 才记 time.time() - 开始
    #         最后原因 = 整片.get("finish_reason") or 最后原因
    #         段 = 片.get("content")；有正文就：首字 第一次记下，然后 `if 打印: 打印(段)`
    #   ④ 计时 不是 None 就 计时["首包"] = 首包 / 计时["首字"] = 首字
    #      return {"message": 拼碎片(碎片们), "finish_reason": 最后原因}
    #
    # ⚠️ 拼碎片 就是你自己在 _流式练习.py 里写的那只 ——
    #    整个函数复制到本文件里（放在 发消息 上面），一行都不用改。
    # ═══════════════════════════════════════════════════════════════
    请求体 ["stream"] = True
    r = requests.post(聊天地址, headers=请求头, json=请求体, stream=True, timeout=60)
    r.raise_for_status()

    开始 = time.time()
    首包 = 首字 = None
    碎片们: list[dict] = [] 
    最后原因 = None
    for 行 in r.iter_lines(decode_unicode=True):
        if not 行 or not 行.startswith("data: "):
            continue
        正文行 = 行[len("data: "):]
        if 正文行 == "[DONE]":
            break
        整片 = json.loads(正文行)["choices"][0]
        片 = 整片.get("delta") or {}
        碎片们.append(片)
        if 首包 is None:
            首包 = time.time() - 开始
        最后原因 = 整片.get("finish_reason") or 最后原因
        段 = 片.get("content")
        if 段:
            if 首字 is None:
                首字 = time.time() - 开始
            if 打印:
                打印(段)
    if 计时 is not None:
        计时["首包"] = 首包
        计时["首字"] = 首字
    return {"message": 拼碎片(碎片们), "finish_reason": 最后原因}


def 真问一次(问题: str) -> str:
    """只负责"发一次、把答案掏出来"。不管重试。"""
    选 = 发消息([{"role": "user", "content": 问题}])
    return 选["message"]["content"]


def 问一句(问题: str, 试几次: int = 3) -> str:
    """外面这层只管一件事：失败了再试，试够次数还不行才认输。"""
    # TODO —— 照下面五步写（这是"重试壳子"的标准形状）：
    #
    #   ① for 第几次 in range(1, 试几次 + 1):      ← 从 1 数到 试几次
    #
    #   ② try 里面只放一句：return 真问一次(问题)
    #       成了就直接从函数里跳出去，后面所有代码都不再走
    #
    #   ③ 第一个 except：接"网络抽风"—— ConnectionError 和 Timeout 两种
    #       （两个写一个括号里就行：except (A, B) as 错:）
    #       里面：打印一句"第 {第几次} 次没成（{type(错).__name__}）"
    #             然后 if 第几次 < 试几次:  time.sleep(2)     ← 没到最后一次才歇
    #
    #   ④ 第二个 except：接剩下的 RequestException
    #       这种再试也没用（比如 Key 错了、404），直接：
    #           raise RuntimeError(f"这个错误再试也没用：{错}")
    #
    #   ⑤ 循环跑完还没 return —— 说明每次都被 except 接走了，
    #       在循环外面 raise RuntimeError(f"试了 {试几次} 次都没成，先别问了。")
    for 第几次 in range(1, 试几次 + 1):
        try:
            return 真问一次(问题)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as 错:
            print(f"第 {第几次} 次没成（{type(错).__name__}），再试一次…")
            if 第几次 < 试几次:
                time.sleep(2)
        except requests.exceptions.RequestException as 错:
            raise RuntimeError(f"这个错误再试也没用：{错}")

    raise RuntimeError(f"试了 {试几次} 次都没成，先别问了。")


if __name__ == "__main__":
    原话 = 问一句("用一句话说你是谁")
    print(原话)
