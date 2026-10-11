# Python 学习笔记 · 2026-09-22

## 新知识点：requests 网络请求（第三方库）

练习文件：`D:\CC Switch\requests_practice.py` —— **五关全部通过**（关 3 一次因 httpbin 超时，重跑即过）

环境：Python 3.14.6 (32位) + requests 2.34.2（09-16 已装好，本次直接用）

练习用站点：
- `jsonplaceholder.typicode.com` —— 假数据 API，快（0.6~0.8 秒），首选
- `httpbin.org` —— 回显你发的请求，慢（1~3 秒），偶尔抽风（本次实测一次 ReadTimeout 后重跑正常）

---

## 一、五关内容与实测输出

### 关卡 1：发第一个请求 —— 拿到的是一个「响应对象」

```python
resp = requests.get(网址, timeout=10)
print(type(resp))        # <class 'requests.models.Response'>
print(resp)              # <Response [200]>
print(resp.status_code)  # 200
print(len(resp.text))    # 292
print(resp.text[:30])    # 正文开头 30 个字符
```

**核心概念**：`requests.get()` 交给你的不是字符串，是一个 **Response 对象**。字符串只是它身上的一格（`.text`）。

外卖比喻（本轮全程沿用）：`get()` = 下单+等+收到袋子；`resp` = 外卖袋；`status_code` = 袋子外面贴的单号（200 顺利送到 / 404 没这东西 / 500 对面崩了）；`.text` = 袋子里的饭。

`resp.text` 的点号 = 对象取属性，和 `路径.name`、`Counter.most_common()` 同一语法。

### 关卡 2：把正文变成 Python 数据

```python
数据 = resp.json()
print(数据.keys())     # dict_keys(['userId', 'id', 'title', 'body'])
print(数据["title"])
print(len(requests.get(列表网址).json()))   # 100
```

**核心概念**：两层。
- `resp.text` —— 一串**字符**，Python 不认识里面的结构
- `resp.json()` —— **已经 loads 好**的 dict / list，可以直接下标取

`.json()` 就是 requests 帮你调了一次 `json.loads`（接上已学的 json 模块）。对面回的不是 JSON 会抛 `JSONDecodeError`。

嵌套字典逐层取：`用户["address"]["city"]`（关卡 5 用到）。

### 关卡 3：传参数

```python
resp = requests.get(网址, params={"userId": 1}, timeout=10)
print(len(resp.json()), resp.json()[0]["userId"])   # 10 1

resp = requests.get(网址, params={"userId": 1, "id": 3}, timeout=10)
print(len(resp.json()), resp.json()[0]["id"])       # 1 3
print(resp.url)   # https://jsonplaceholder.typicode.com/posts?userId=1&id=3

resp = requests.get("https://httpbin.org/get", headers={"User-Agent": "MyStudyBot/1.0"}, timeout=10)
print(resp.json()["headers"]["User-Agent"])   # MyStudyBot/1.0
```

**核心概念**：两种参数塞法
- `params={...}` —— 拼到网址问号后面，**看得见**（`?userId=1&id=3`）
- `headers={...}` —— 塞进请求头，网址上看不见

不自己拼字符串的原因：特殊字符要转义（空格、中文、`&`），`params` 会自己处理。

`httpbin.org` 的价值 = **把你发的请求原样回显**，所以能"看见对面收到了什么"。默认 UA 是 `python-requests/2.34.2`。

实测坑：**请求头里写中文直接崩** → `UnicodeEncodeError: 'latin-1' codec can't encode ...`（HTTP 头只认 latin-1）。

### 关卡 4：出错了怎么办

**关 4 的实证输出**：

```
404
{}
HTTPError
404 Client Error: Not Found for url: https://jsonplaceholder.typicode.com/posts/9999
ConnectionError
HTTPSConnectionPool(host='no-such-site-abcxyz-123.com', port=443): Max retries exceeded ...
ReadTimeout
HTTPSConnectionPool(host='httpbin.org', port=443): Read timed out. (read timeout=2)
```

**核心概念：失败分两类**

| 类别 | 现象 | 处理 |
|---|---|---|
| 对面回话了，但是坏消息（404/500） | **不报错**，resp 照常给你，只是 `status_code != 200` | 主动调 `resp.raise_for_status()` 才变异常 |
| 根本没接上（域名不存在/断网/超时） | **直接抛异常** ConnectionError / ReadTimeout | try/except 接住 |

两类都是 `requests.exceptions.RequestException` 的子孙 → **一个 except 接全部**（因为它连 HTTPError 一起接了）。

`timeout=` 的含义：最多等这么多秒，超了自己放弃并抛异常。不写的话现象是"卡住不动、也不报错"。`timeout=2` 打 `httpbin.org/delay/5` 实测约 3 秒后抛 `ReadTimeout`。

### 关卡 5：实战 —— 拉名单做报告

```python
resp = requests.get("https://jsonplaceholder.typicode.com/users", timeout=10)
print(f"共 {len(resp.json())} 位用户")        # 共 10 位用户
# 姓名 | 邮箱 | 城市（前 3 位）
邮箱后缀 = [re.search(r'(\.[a-z]+)$', u['email']).group(1) for u in resp.json()]
后缀计数 = Counter(邮箱后缀)
most_common_suffix, count = 后缀计数.most_common(1)[0]
print(f"后缀 {most_common_suffix} 出现 {count} 次")   # 后缀 .biz 出现 3 次
```

实测输出：

```
共 10 位用户
Leanne Graham | Sincere@april.biz | Gwenborough
Ervin Howell | Shanna@melissa.tv | Wisokyburgh
Clementine Bauch | Nathan@yesenia.net | McKenziehaven
Counter({'.biz': 3, '.tv': 1, '.net': 1, '.org': 1, '.ca': 1, '.info': 1, '.me': 1, '.io': 1})
后缀 .biz 出现 3 次
```

**核心概念**：这就是 AI 应用里「调模型接口 → 处理返回结果」的简化版流水线：

```
发请求 → resp.json() → 取出要的字段 → 统计 → 给人看
```

串起了已学的 `re`（抠后缀）+ `collections.Counter`（计数）+ f-string。

---

## 二、用户当天问的五个问题（都答了）

1. **`timeout=10` 什么意思** —— `requests.get` 预留的"口子"之一，`名字=值` 塞进去；含义是"最多等 10 秒"。不写的现象是卡住不动。
2. **`resp.status_code` 什么意思** —— 响应对象身上的属性，袋子外面的单号；点号=取属性。
3. **`[:30]` 什么意思** —— 切片，从头取到第 30 个（不含）；不切会刷 292 个字符刷屏。
4. **`print(type(e).__name__)` 和 `print(e)` 有什么区别** —— ⭐ 卡了一次，见下节讲法。
5. **`most_common_suffix, count = 后缀计数.most_common(1)[0]` 怎么写出来的** —— 三层：`most_common(1)` 返回**列表** `[('.biz', 3)]` → `[0]` 取出**元组** → 左边两个名字按位置解包。写法不是背的，是**先只写一半跑出来看它是什么**，一层层试。

## 三、⭐ 讲法记录：`print(e)` vs `print(type(e).__name__)`

用户说"没懂有什么区别"，直接**从头慢讲一遍**，用实跑输出当证据（`_error_demo.py` / `_error_demo_out.txt`）：

- 第一步 `print(e)` → 280 个字符的详细经过
- 第二步 `print(type(e))` → `<class 'requests.exceptions.ConnectionError'>`（还有外壳）
- 第三步 `print(type(e).__name__)` → `ConnectionError`（干净）

**关键分法（用户最后接受的说法）**：`e` 身上装着两样东西 ——
- 一样是**种类**（ConnectionError，一个词，短）
- 另一样是**这次的详细说明**（280 字）

延续外卖比喻：`e` 像一张**故障单**，上面盖着**类别章**（ConnectionError），下面是**详细经过**。
- `print(e)` = 整张单子念一遍
- `print(type(e).__name__)` = 只看那个章

用法：一眼看"哪类错"用前者（短、好比较），查"具体卡在哪"用后者（详情）。两个都打 = 先盖章再念详情，是标准写法。

**Why 要拐 Type(e)**：种类名不是 `e` 直接的点号属性，得先问"你什么类型"（`type(e)`），类型对象身上才有存名字的格子（`.__name__`）—— 从里往外读。

## 三之二、⭐ 讲法记录：params vs headers 的区别

第一遍用"明信片 / 信封"的比喻讲，用户说**没听懂**（"我怎么没听懂"）。第二遍改成 **三段对照实跑**，讲通了（`_params_headers_demo.py`）：

前提一句话：**一次请求就像一个包裹**，包裹上可以写两样东西 —— 外面贴的**地址**（网址）、里面装的**小纸条**（参数）。

三段输出（全部实跑过）：

```
=== A. 什么都不带 ===
网址变成了: https://httpbin.org/get
对面收到的 args: {}

=== B. 只带 params ===
网址变成了: https://httpbin.org/get?userId=1&id=3
对面收到的 args: {'id': '3', 'userId': '1'}

=== C. 只带 headers ===
网址变成了: https://httpbin.org/get
对面收到的 args: {}
对面收到的 User-Agent: MyStudyBot/1.0
```

讲法关键（有效）：
- A → B：**网址自己变了**（多出 `?userId=1&id=3`）→ params 是拼进网址里的
- B → C：**网址一个字没多**，但对面照样收到了 `MyStudyBot/1.0` → headers 不写进网址，但照样送到
- 一句大白话总结：**两个对面都能收到，区别只有一条 —— 露不露在网址上**
- 外卖比喻改成：params 像写在**快递单面**上的备注，一路都看得见；headers 像**塞在包裹里的小纸条**，路上看不见、收件人开箱就看到

⚠️ 教训：抽象比喻（明信片/信封）替代不了**实跑对照**。以后讲"两种东西的区别"，先跑三段 A/B/C 摆出来再上比喻。

---

## 四、踩坑记录

1. **正则抓宽了**（关卡 5）：`re.search(r'@(\S+)', email).group(1)` 抓出来的是 `april.biz`（从 @ 一路到结尾），不是后缀 `.biz`；改成 `r'(\.[a-z]+)$'`。
   - 第二次改还错一次：把 `@` 留下了写成 `r'@(\.[a-z]+$)'` → 一个都匹配不上 → `re.search` 返回 `None` → `AttributeError: 'NoneType' object has no attribute 'group'`
   - 教训串上了 re 那关的话：**正则是一张通缉令，你描述的长相是"@ 后面的一大串"**，抓出来的自然是那么长。
2. **关卡 3 TODO 1 漏了半行**：只打了 `len(结果)`，忘了 `结果[0]["userId"]`（第 135 行）。
3. **httpbin.org 超时**（不是代码错）：关卡 3 第一次跑 `requests.get(..., timeout=10)` 抛 `ReadTimeout`，重跑就过 —— 这正是 timeout 设计出来要防的情况，现场教材。

## 五、本轮知识点总结（一句话版）

- 网络请求 = 发出去 + 等回来 = 一个 Response 对象
- 对象上按点号取：`.status_code`（单号）/ `.text`（字符）/ `.json()`（转成 dict/list）/ `.url` / `.headers`
- `params` 写在网址上，`headers` 塞在信封里
- 404 不报错，要 `raise_for_status()` 才变异常；接不上直接抛，`RequestException` 一网打尽
- 走网络必带 `timeout=`
- 实战流水线：请求 → json → 取字段 → 统计 → 输出（= AI 调接口的简化版）
