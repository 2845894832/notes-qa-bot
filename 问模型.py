# -*- coding: utf-8 -*-
"""项目第 ③ 步的第一小块：跟模型说话。

这一小块只做一件事：**确认 Key 通了，看看你的账号能用哪些模型名。**

为什么 Key 放在请求头（headers）里，不拼进网址：
    网址会一路被记下来 —— 服务器日志、代理、浏览器历史、报错截图里都有。
    请求头只跟着这一次请求走。所以 Key 一律放 headers，不放 params。
    （这就是 requests 那关讲的 params 改网址 / headers 不改网址）

⚠️ 这个文件里永远不出现 Key 本身，只出现 os.environ.get("DEEPSEEK_API_KEY")。
"""

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


def 真问一次(问题: str) -> str:
    """只负责"发一次、把答案掏出来"。不管重试。"""
    钥匙 = 拿钥匙()
    请求头 = {
        "Authorization": "Bearer " + 钥匙,
        "Content-Type": "application/json",
    }
    请求体 = {
        "model": 模型名,
        "messages": [
            {"role": "user", "content": 问题},
        ],
    }
    r = requests.post(聊天地址, headers=请求头, json=请求体, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


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
