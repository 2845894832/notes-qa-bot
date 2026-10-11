# Python 学习总结 2026-09-16 —— logging 五关精讲 + pathlib 入门 + random/statistics 五关 + re 正则五关

> **今天两个主题**：
> - **一、logging**：把 `logging_practice.py`（5 关，已全部通过）当教材**逐关讲透**，不是查错
> - **二、pathlib**：新知识点，`pathlib_practice.py`（5 关，全部完成）
>
> **形式**：一关一关走，每关先跑代码看现象、再讲原理，每关结束停下来提问。
> **路线图进度**：8 个域全部走完；logging 是「标准库精选」的复习轮，pathlib 是新开的一节。

---

# 第一部分：logging（标准库精选 · 日志）

## 总纲：一句话记住 logging

**logging 是一套"分级、分渠道、分层级"的报表系统。**

```
logger.info("消息")
   │
   ├─ ① 级别够吗（出发 logger 的 effective level）？ 不够 → 扔
   ├─ ② 交给这个 logger 挂着的【每个】handler
   │       ├─ Handler A → 各自判自己的门槛 → Formatter → 控制台
   │       └─ Handler B → 各自判自己的门槛 → Formatter → 文件
   └─ ③ propagate=True → 爬到父 logger → 父的 handler 再来一遍 → 一直到 root
```

- **门槛**决定谁进得来
- **handler** 决定去哪儿（几个出口）
- **propagate** 决定要不要往上递
- **格式串**决定长什么样

---

## 关卡 1：最小的能跑起来的 logging

### 1. 级别根本不是标签，是数字

```
DEBUG=10  INFO=20  WARNING=30  ERROR=40  CRITICAL=50
```

`logging.DEBUG` 这个常量，里面装的就是 10。每收到一条日志，logging 只做一件事：

```
这条消息的数字  >=  门槛的数字  ？
```

成立就打印，不成立就扔掉。没有名单、没有白名单，**就是比大小**。

这顺手解释了为什么 WARNING 排在 INFO 后面、CRITICAL 永远最大——它俩的差就是 30 和 50 的差。

**实验**：`_level_demo.py` 同一个程序只改门槛数字，跑四轮 → 输出条数 4 → 3 → 2 → 1。

### 2. 大写是名词，小写是动词

| 写法 | 是什么 | 干嘛用 |
|---|---|---|
| `logging.ERROR` | 数字 `40` | 当门槛、比大小 |
| `logging.error` | 一个函数 | 喊一嗓子（打一条日志） |

**很阴的坑**（已踩 4 次，见顽固 bug 清单）：

```python
logger = logging.getLogger('demo')
logger = logging.DEBUG         # ← 想"把 logger 的门槛设成 DEBUG"
logger.info('打一条')
# AttributeError: 'int' object has no attribute 'info'
```

`=` 是**覆盖**不是**设置**。这行之后 `logger` 变成了整数 10，原来那个 logger 没人引用了。

正确写法：`logger.setLevel(logging.DEBUG)`

**自查习惯**：写完任何一行赋值，念一遍"**这个名字，现在指的是什么东西**"。念出来发现它变了种类，那就是覆盖 bug。

### 3. basicConfig 只生效一次

**实验**：`_once_demo.py` 连调三次 `basicConfig`（第二次换格式），结果：

```
第一次的格式说: A
第一次的格式说: B        ← 第二次的 basicConfig 被静默无视
第三次的格式说: C        ← 加了 force=True 才换掉
```

**为什么**：`basicConfig` 是"给 root 装一个出口"的快捷方式。每次调用前先探一眼：**root 身上已经挂着出口了吗？** 有 → 直接 return，不报错不警告。`force=True` = 先把旧出口全拆了再装。

**为什么要这么设计**：真实项目里每个第三方库都可能顺手调一次 `basicConfig`，每调一次就追加一个出口的话，一条日志会被打三遍五遍。所以它宁可装聋作哑。

**这正好解释练习文件开头为什么写"一次跑一关"**：同一个进程里，关卡 1 的 `basicConfig` 生效后，关卡 2 的 `basicConfig` 就不生效了，格式会一直是关卡 1 的。（一次跑一关能 work，是因为每次都是新起一个进程，root 是全新的。）

### ⚠️ 本次发现并修正的教材错误

练习文件原来第 50 行写着：

> 再把 level 整行删掉再跑一次 —— 一条都不剩，因为 root 默认是 WARNING。

**这句是错的。** 实测（`_no_basicconfig.py`，五条 `logging.xxx` 一行配置都不写）：

```
WARNING:root:这是 WARNING
ERROR:root:这是 ERROR
CRITICAL:root:这是 CRITICAL
```

**还是 3 条，不是 0 条。** 而且长相完全变了——没时间、没对齐、中间凭空多个 `root`。

两件事同时发生了：

1. **门槛退回 30**：没设门槛，root 出厂自带 WARNING，所以 warning/error/critical 还是过得去（这条注释写对了）
2. **格式退回最原始的样子 `级别:名字:消息`**：连 `format=` 也一起删了，logging 会掏出一个**兜底出口**，用最丑的格式打到屏幕上

**正确说法：删掉整行 → 3 条，但换了个丑格式。** 已修改文件注释。

---

## 关卡 2：格式串 —— 让每条日志自带「出处」

### 1. 格式串是一张填空题

```python
"%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
```

**本质是一张模板纸，上面挖了 6 个空。** `%(字段名)s` 就是一个空，logging 从"这条日志记录"里取对应字段填进去。

| 模板里写的 | 填进去的东西 | 本次的值 |
|---|---|---|
| `%(asctime)s` | 日志产生的时间 | `2026-09-16 09:23:22,518` |
| `%(levelname)-8s` | 级别名 | `INFO` |
| `%(name)s` | 哪个 logger 打的 | `root` |
| `%(funcName)s` | 在哪个函数里打的 | `下单` |
| `%(lineno)d` | 哪一行 | `91` |
| `%(message)s` | 传给 `logging.info(...)` 的那段话 | `下单:A001 \| 用户下单成功 金额=99.9` |

末尾字母是**类型**：`s` = 按字符串填，`d` = 按整数填。

### 2. `%(levelname)-8s` 里的 `-8` 是什么意思

**实验**：`_fmt_demo.py` 三种写法对比：

```
%(levelname)s        %(levelname)-8s       %(levelname)8s
WARNING | 警告        WARNING  | 警告        WARNING | 警告
INFO | 消息           INFO     | 消息           INFO | 消息
  ↑ 竖线不齐              ↑ 竖线齐了              ↑ 也齐，但往右靠
```

- **`8`** = 这个空**至少**占 8 格，不够用空格补
- **`-`** = 补的空格放**右边**（内容靠左）；不写 `-` 就补左边（内容靠右）
- 内容超过 8 格（比如 `CRITICAL`）→ **照原样撑出去，不会被砍**。宽度是最低要求，不是上限

### 3. name 列为什么是 root

关卡 2 写的是 `logging.info(...)`——**模块级函数**。它不是"某个 logger 的方法"，是**"替 root 喊一嗓子"**的快捷方式，等于 `logging.getLogger("root").info(...)`。

所以这一列永远是 `root`。关卡 4 换成 `getLogger` 之后就变成自己的名字了。

### 4. `下单:91` —— print 给不了的东西

`funcName` = `下单`，`lineno` = **91**，也就是 `logging.info(...)` 那一行在文件里的**行号**。

**日志自带坐标。** 线上出问题看到一条 ERROR，不用猜，直接按 `文件名 + 行号` 跳过去就是出事那行。print 只会告诉你"说了什么"，不会告诉你"在哪说的"。

---

## 关卡 3：双通道 —— 控制台看大概，文件里存全量

**现象**：控制台 2 条（INFO/WARNING），`debug.log` 3 条（多一条 DEBUG）。同一句 `logger.debug("这条只进文件")`，屏幕看不见、文件里有。

### 1. 两道闸门，而且是**串联**的

**第一道在门口——`logger.setLevel(...)`**

日志先问："我的级别 >= logger 的门槛吗？"不够，掉头扔了，**后面所有通道都收不到**。

**第二道在每个通道口——`handler.setLevel(...)`**

放行之后，logger 把它**抄送给自己挂着的每一个通道**。每个通道再各自判一次："够格吗？"不够这条通道不收，但**别的通道照收**。

**实验**：`_two_gates_demo.py` 三个场景——

```
A 三道全开              B 只把控制台抬到 INFO      C 只把 logger 抬到 INFO
[控制台] DEBUG ✅        [文件]   DEBUG ✅          [控制台] INFO  ✅
[文件]   DEBUG ✅        [控制台] INFO  ✅          [文件]   INFO  ✅
[控制台] INFO  ✅        [文件]   INFO  ✅          （DEBUG 消失了）
[文件]   INFO  ✅
```

**C 是重点**：控制台的门槛明明是最宽松的 DEBUG，可 DEBUG 那条**压根没出现**——它**走不到控制台面前**，在第一道闸门就被 logger 拦掉了，连"抄送给各通道"这一步都没发生。

**所以"缺一不可"的准确含义**：不是"任意一道通过就行"，是**串联、都得过**。而且顺序固定：

```
logger 先判 → 通过了才抄送给各 handler → 各 handler 再各自判
```

### 2. 为什么必须一个角色一个名字

**实验**：`_names_demo.py` "一个名字扛所有角色"的版本：

```python
logger = logging.getLogger("坏例子")
logger.setLevel(logging.DEBUG)

控制台 = logging.StreamHandler()
控制台.setLevel(logging.INFO)

logger = 控制台                     # ← 想"挂上去"，写成了赋值
logger.setFormatter(...)            # ← 居然没报错！
logger.info("还能打吗？")            # ← 崩在这
# AttributeError: 'StreamHandler' object has no attribute 'info'
```

**`=` 不是"设置"，是"贴标签"。** `logger = 控制台` 的意思是：把 `logger` 这个标签从 Logger 身上撕下来，贴到那个 StreamHandler 身上。从此 `logger` 指的是 handler，**原来那个 Logger 没标签了**。

**最阴的地方**：`setFormatter` 那行**没报错**，因为此时 logger 确实是个 handler，而 handler 恰好有这个方法。**报错位置和犯错误的位置隔了两行**——你会盯着 `logger.info` 看，怎么看都对，真正的凶手在上面。

**这关一共 5 个不同的东西，就要 5 个名字**：

| 名字 | 是什么 | 它自己有的方法 |
|---|---|---|
| `logger` | 日志本 | `.setLevel()` `.addHandler()` `.info()` |
| `控制台` | 一个出口 | `.setLevel()` `.setFormatter()` |
| `控制台格式` | 一张模板 | （没有 set 方法，只被塞进 handler） |
| `文件` | 另一个出口 | `.setLevel()` `.setFormatter()` |
| `文件格式` | 另一张模板 | （同上） |

⚠️ **`控制台.setLevel()` 和 `logger.setLevel()` 方法名一模一样，但是两个人的方法**——就是前面的两道闸门。只有一个名字扛的话，第二次 `setLevel` 你以为是"再设一遍日志本的门槛"，实际设的是某个出口的。**程序不报错，只是输出跟想的不一样**——比崩溃难查十倍。

### 3. 顺序是死的：创建 → 配置 → 挂载

```python
logger = logging.getLogger("双通道")    # ① 先创建出来
logger.setLevel(logging.DEBUG)          # ② 才能配置它
控制台 = logging.StreamHandler()        # ① 创建
控制台.setLevel(logging.INFO)           # ② 配置
控制台.setFormatter(控制台格式)          # ② 配置
logger.addHandler(控制台)               # ③ 最后挂载
```

跳过①直接 `logger.setLevel(...)` → `UnboundLocalError: cannot access local variable 'logger'`（"这个名字我还没见过就在用了"）。

---

## 关卡 4：模块级 logger + 层级继承

**现象**：只给 `shop` 设了级别、挂了 handler，打出来这两条的却是从没配置过的 `shop.service` / `shop.storage`。

### 1. 名字里的点号 = 层级分隔符，树是自动搭的

```
root
 └── shop
      ├── shop.service
      └── shop.storage
```

跑一下 `logger.parent.name`：

```
shop                 的爸爸是 -> root
shop.service         的爸爸是 -> shop
shop.storage         的爸爸是 -> shop
shop.service.db      的爸爸是 -> shop.service      ← 注意不是 shop
随便一个没提过的名字   的爸爸是 -> root
```

**你只说个名字，爸爸早就挂好了。点号分几段，就是几层。**（公司层级：`shop` 是总公司，`shop.service` 是下面的部门。）

### 2. Q1 答案：级别会"往上问"

**实验**：`_inherit_demo.py` 只改爸爸的级别，孩子的代码一个字不改：

```
爸爸 = DEBUG     爸爸 = INFO      爸爸 = WARNING
  INFO  ✅          INFO  ✅          INFO  ❌   ← 没了
  WARNING ✅        WARNING ✅        WARNING ✅
```

孩子自己的级别是 **`NOTSET`**——不是"门槛设成 0 了"，它的意思是**"我没意见，去问我爸爸"**。拿着这条日志一路往上问，问到一个设了级别的长辈为止。

**两个 API 说的不是一回事**：

```
孩子 .level               = NOTSET     ← 我自己填的那个
孩子 .getEffectiveLevel() = INFO       ← 一层层问出来的、真正生效的那个
```

- `.level` 是**你自己写的**，没写过就是 NOTSET
- `.getEffectiveLevel()` 是**真正管用的**，一路往上问到 root 为止

**这解释了关卡 1 的悬案**：`logging.info(...)` 是替 root 打的，root 自己没设过级别（`.level` 也是 NOTSET），但 **root 是树根，没有爸爸可问**，所以到它这儿就停，用出厂默认的 WARNING(30)。这就是"删掉 basicConfig 后 DEBUG 和 INFO 一条都出不来"的完整原因。

**你配的那一行 `shop.setLevel(INFO)` 管的不只是 shop 自己，管的是它和它下面所有没表态的子孙。**

### 3. Q2 答案 + propagate

**实验**：`_propagate_demo.py` 三幕——

```
第 1 幕：孩子挂着 0 个 handler，日志照样出来了
    [爸爸的出口] a1.service | 这条是谁打出来的？      ← 是爸爸的 handler 打的

第 2 幕：同一个孩子 propagate=False
    （下面什么都没有，静默消失）

第 3 幕：孩子自己挂一个 + 爸爸也挂 + root 也有
    [孩子的出口] a3.service | 数一数这条打了几遍
    [爸爸的出口] a3.service | 数一数这条打了几遍
    [root 的出口]  a3.service | 数一数这条打了几遍    ← 一条打了三遍
```

**机制**：日志没停在孩子身上，它沿着树**往上一层层爬**，爬到哪个祖先挂着 handler 就用那个打。这叫 **propagate（传播）**，默认 `True`。（部门没打印机，文件就送总公司印。）

**关掉 propagate 会静默消失**——不报错不警告。以后打了一条日志什么都没看见，第一反应是查**两道门槛 + 有没有 handler 收**。

⚠️ **第 3 幕就是真实项目里最常见的"日志重复打印"bug**：
- 你自己 `getLogger("ai.client")` 挂了 handler
- 同时某个库（或另一处代码）调了 `basicConfig` 给 **root** 也挂了
- 结果每条日志打两遍——一遍出自你的 handler，一遍出自 root 的

**修法一行**：`logger.propagate = False`

**（关卡 3 的"双通道"能那么干净地打出 2+3 条，是因为那个进程里 root 身上一个 handler 都没有，爬到 root 就自然停住了。）**

### 4. 完整流程

```
① 在出发的 logger 上判门槛（用 effective level，会往上问）
   ↓ 通过
② 用自己挂的 handler 打
   ↓ propagate=True?
③ 爬到父 logger，用父挂的 handler 打
   ↓ 还是 True?
④ 一直爬到 root
```

**门槛只判一次**（在出发的 logger 上）；放行之后，路上经过的**每个 handler 各自再判自己的门槛**。

---

## 关卡 5：实战 —— 给「调用大模型」加日志

**输出**：3 次调用 = 7 行（DEBUG 准备 ×3、INFO 成功 ×2、ERROR 失败 ×1 + 完整 traceback）

### 1. `exc_info=True` —— 那段堆栈是怎么冒出来的

```
2026-09-16 11:22:54,972 | ERROR | ai.client | 调用失败 问题=解释RAG
Traceback (most recent call last):
  File "D:\CC Switch\logging_practice.py", line 266, in 关卡5
    回答 = 调用模型(问题, 会失败)
  File "D:\CC Switch\logging_practice.py", line 245, in 调用模型
    raise RuntimeError("模型服务返回 503")
RuntimeError: 模型服务返回 503
```

**实验**：`_exc_info_demo.py` 三组对照——

**组 1**：`print(e)` 只能给你 → `模型服务返回 503`（一句话，不知道哪一行炸的）

**组 2**：不在 `except` 里却写 `exc_info=True` →
```
ERROR    | 我不在 except 里
NoneType: None          ← "没有异常可取"
```

**组 3**：在 `except` 里写 `exc_info=True` → **完整堆栈，一行行告诉你谁调了谁**（第 25 行调了 `炸()`，`炸()` 在第 9 行抛的）。线上排错全靠这个。

**机制**：`exc_info=True` 做的事是——**调一下 `sys.exc_info()`，把"当前正在被处理的异常"捞出来打印**。

问题是：**Python 只在 `except` 块执行期间，才把异常放进那个槽里**；`except` 块一结束，槽就清空了。

- 在 `except` 里 → 槽里有货 → 打出完整堆栈 ✅
- 不在 `except` 里 → 槽是空的 → `NoneType: None` ❌

**一句话：`exc_info=True` 只管"当前正在被处理的异常"，而"正在被处理"这个状态只有 `except` 块里才有——所以它必须写在 `except` 块里。**

**更常用的简写**：`logger.exception(...)` **完全等于** `logger.error(..., exc_info=True)`。它只在 `except` 里有意义，所以名字叫 exception 而不叫 error——看到它就知道"这行一定在 except 里"。

### 2. 惰性格式化：为什么只有 DEBUG 非用 `%s` 不可

**一句话**：`%s` 和 f-string 打出来的东西**一模一样**，区别只有一个——**字符串在什么时刻被拼出来**。

```python
logger.debug(f"准备调用: {问题}")       # Python 执行到这行时【先拼好】，再交给
logger.debug("准备调用: %s", 问题)      # 交给的是【模板 + 参数】，logging 拿到手先看门槛
                                        # 门槛不够 → 模板参数一起扔，根本不去拼
```

**实验**：`_lazy_demo.py` 让 DEBUG 一律被门槛拦下，跑 20 万次：

```
f-string      0.057 秒
%s 惰性         0.033 秒
```

**f-string 白拼了 20 万次字符串。** 单次只省约 **0.1 微秒**，摊开看微不足道——但日志往往写在最热的地方（循环里、每次请求里），一个服务一天几亿次，而且 DEBUG 日志带的常是最长的数据（完整请求体、中间变量）。

**为什么只对 DEBUG 有意义**：

- **DEBUG**：生产环境门槛一般是 INFO，DEBUG 日志 **100% 不会打印** → 每次调用都是白拼 → 惰性收益拉满
- **INFO**：门槛设成 INFO 就**一定会打** → 既然一定要打，字符串无论如何都得拼，`%s` 一分钱省不下来 → f-string 更好读

**你关卡 5 的搭配是对的**：两条 DEBUG 用 `%s`，INFO 那条用 f-string。

⚠️ **诚实补充：惰性不是万能的**。`%s` 推迟的只是**拼字符串**，**参数本身求值还是在原地**：

```python
logger.debug("耗时明细: %s", 拿很贵的数据())   # ← 拿很贵的数据() 照样每次都执行

if logger.isEnabledFor(logging.DEBUG):        # 参数本身贵，得用这招
    logger.debug("耗时明细: %s", 拿很贵的数据())
```

### 3. 这个模式在真实 AI 应用里长什么样

```python
logger.debug("准备调用: %s", 问题)                          # 每次请求都记，但不进生产日志
logger.info("调用成功 耗时=%.2fs tokens=%d", 耗时, tokens)   # 上线后靠这个看成本和延迟
logger.exception("调用失败 问题=%s", 问题)                   # 失败必须带堆栈
```

**第 2 条尤其关键**——AI 应用里**耗时和 token 数就是钱**，这两个数字进日志，你才能回答"哪个功能最烧钱"。

---

# 第二部分：pathlib（新知识点）

> 练习：`D:\CC Switch\pathlib_practice.py`（5 关，**全部完成**）
> 形式：仿 `logging_practice.py`，每关先跑代码看现象、再讲原理。

## 总纲：路径是个**对象**，不是字符串

`os.path` 把路径当字符串——拼接要调函数，问信息也要调函数。
`pathlib` 把路径当对象——拼接用 `/`，问信息用属性。

**老新对照**（实测输出）：

```
=== 老办法: os.path ===
  拼出来的东西: D:/CC Switch\logs\debug.log     ← 正反斜杠混着来
  它是什么类型: str
  文件名? os.path.basename(老)                  后缀? os.path.splitext(老)[1]

=== 新办法: pathlib ===
  拼出来的东西: D:\CC Switch\logs\debug.log     ← 统一成反斜杠
  它是什么类型: WindowsPath
  文件名? 新.name                               后缀? 新.suffix
```

两个变化：**① `Path(...) / "a" / "b.txt"`**（`/` 不是除法，是 `Path` 给斜杠赋予的新含义，自动加分隔符、自动统一格式）；**② 全是属性，点号取**。

---

## 关卡 1：拆解一个路径

拿 `Path("D:/CC Switch/expense_tracker/models.py")` 拆：

| 属性 | 值 | 意思 |
|---|---|---|
| `.name` | `models.py` | 带后缀的完整文件名 |
| `.stem` | `models` | 去掉后缀的主干 |
| `.suffix` | `.py` | 后缀（**带点**） |
| `.parent` | `D:\CC Switch\expense_tracker` | 上一级 |
| `.parts` | `('D:\\', 'CC Switch', 'expense_tracker', 'models.py')` | 按层级切块（元组） |
| `.drive` | `D:` | 盘符 |
| `.anchor` | `D:\` | 盘符 + 根分隔符 |

⚠️ **`.parts` 里的 `'D:\\'` 和 `.anchor` 的 `D:\` 是同一个值**，不是"一个两个反斜杠、一个是一个"。区别只在打印方式：**元组打印时每个元素按"代码里该怎么写"显示**（一个反斜杠写成 `\\`）。`parts[0] == anchor` 是 `True`。

**TODO 4 的答案**：普通字符串没有 `.name` —— `AttributeError: 'str' object has no attribute 'name'`。这就是"对象"和"字符串"的分水岭。

---

## 关卡 2：拼路径与改造 —— **不可变**是重点

```python
报告 = 基础 / "pathlib_demo" / "report.txt"
新报告 = 报告.with_suffix(".md")     # 报告 一点没变，新报告 是另一个对象
```

实测四行输出验证：

```
D:\CC Switch\pathlib_demo\report.txt
D:\CC Switch\pathlib_demo\report.md
D:\CC Switch\pathlib_demo\report.txt      ← 报告 本体，没被改
D:\CC Switch\pathlib_demo\summary.md
```

**`with_xxx` 系列全都不改原对象，返回新对象。** 跟字符串的 `.upper()` 一个脾气。这样设计是因为不可变的东西可以放心传来传去，不用担心某个函数偷偷把路径改了。

⚠️ `with_suffix` 的参数**要带点**：`.with_suffix(".md")` ✅，`.with_suffix("md")` 报错。

---

## 关卡 3：读写与判断

### `mkdir` 的两个参数（四次实验）

```
第 1 次  目标.mkdir()                → FileNotFoundError（中间目录不存在）
第 2 次  目标.mkdir(parents=True)    → 成功，一次把三层全建出来
第 3 次  再跑一次同样的               → FileExistsError
第 4 次  ...exist_ok=True            → 静默通过
```

- **`parents=True`** = 上面缺的目录，顺手一起建了
- **`exist_ok=True`** = 如果已经有了，就当没事发生

**为什么真实项目里两个几乎总是一起出现**：因为代码会被跑很多次。第一次跑要建，第二次跑目录已经在了，只写 `mkdir()` 就当场崩。加上 `exist_ok=True` 才是**幂等**的。

> **幂等**：同一个操作，执行一次和执行一百次，效果完全一样。看到"建目录、写文件、注册"这类操作，先想"这行被跑第二次会怎样"。

⚠️ **两个参数必须写名字**：`mkdir(True, True)` 是错的——第一个位置参数是 `mode`（权限位），会把 `True` 静默当权限传进去。**参数一多，一律写名字。**

### `read_text` / `write_text`

```python
文件.write_text("第一行\n第二行\n第三行\n", encoding="utf-8")
print(文件.read_text(encoding="utf-8"))
```

这俩就是你已经学过的 `with open(...) as f: f.read()` 的简写，只是挂在 Path 对象上了。**`encoding="utf-8"` 不能忘**——跟 `FileHandler` 忘写 encoding 是同一个病。

实测：`目录.exists()` / `目录.is_dir()` / `文件.is_file()` → `True True True`。
**TODO 14 答案**：不带参数的 `mkdir()` 再跑一次 → `FileExistsError`。

---

## 关卡 4：遍历目录

**三个工具，区别只在"往下钻多深"**（三个都是看"自己里面"）：

```
iterdir()         列【直接子项】，不递归
glob("*.py")      按通配符找【直接子项】
rglob("*.py")     按通配符找【所有子孙】   r = recursive   （等价于 glob("**/*.py")）
```

对着 `expense_tracker` 实测：

```
iterdir()       8 项（含 __pycache__、tests 两个【目录】）
glob("*.py")    6 项
rglob("*.py")   9 项   ← 多出的 3 个是 tests\__init__.py / test_service.py / test_storage.py
```

⚠️ **`iterdir()` / `glob()` 的顺序是随机的**，想稳定输出要自己套 `sorted()`。

### 卡住过的一个点：**子项 ≠ 同层**

```
项目.iterdir()         → 装在项目【里面】的东西  = 子项 = 下一层
项目.parent.iterdir()  → 住在项目【旁边】的东西  = 同层（149 项，含 expense_tracker 自己）
```

**记法：看谁 `.iterdir()`，就看谁的里面。** "项目的同层"换个说法就是"项目爸爸的子项"——同一件事，只是站在谁的位置看。

（当时是"只往下钻一层"这句话里的"层"跟"同层"撞车了，容易误读。）

### 最值钱的一点：给的是 **Path 对象**，不是字符串

```python
for f in sorted(项目.rglob("*.py")):
    print(f.relative_to(项目))     # tests\test_service.py  ← 一眼看出层级
```

老办法 `os.listdir()` 给字符串，想拿相对路径得 `os.path.relpath(绝对路径, 根目录)` 喂两个字符串。pathlib 里 `f.relative_to(项目)` 就够了——**它本来就知道自己在哪**。

遍历时**优先用 `relative_to` 而不是 `.name`**，否则 9 个名字混在一起分不清谁在子目录里。

---

## 关卡 5：实战 —— 扫目录按后缀统计

### 概念一：`rglob("*")` 会把**目录**也塞给你

```
rglob('*') 一共给了 21 项    其中目录 3、文件 18

不过滤直接统计:  '.py' 9   '.pyc' 9   '' 3      ← 那 3 个目录
过滤 is_file():  '.py' 9   '.pyc' 9
```

**因为目录没有后缀，`.suffix` 返回 `""`（空字符串），不报错、不返回 None**，于是悄无声息凑成一行 `''`。**程序照跑，报表是错的**——这就是"统计完先看一眼结果合不合理"的价值。（没有后缀的普通文件如 `LICENSE`、`Makefile` 也会落到 `""` 这一类，真实项目里很多。）

实战里还要再排掉 `.git\`、`node_modules\`、`.venv\`、`__pycache__\` 这些噪音目录。

### 概念二：`Counter` 回顾

```python
Counter("aabbc")                  → Counter({'a': 2, 'b': 2, 'c': 1})
Counter(["苹果","苹果","香蕉"])     → Counter({'苹果': 2, '香蕉': 1})
字母["z"]                          → 0     ← 取不存在的键不报 KeyError，给 0
字母.most_common()                 → [('a', 2), ('b', 2), ('c', 1)]  按次数从多到少
统计.most_common(2)                → 只要前两名（取 Top N）
```

### 概念三：为什么可以没有方括号

```python
Counter(x for x in 全部)        # 生成器表达式：圆括号被函数调用的圆括号"兼任"了
Counter([x for x in 全部])      # 列表推导式：有方括号
```

两者结果一样。**生成器表达式的完整写法是 `(x for x in ...)`**，当它作为函数**唯一参数**时，外层圆括号可以省。还有别的参数就得写回来：`Counter((x for x in ...), 别的)`。

**真正的差别**：

```
流水线 = (x.upper() for x in ["a","b","c"])
第一次取: ['A','B','C']
再取一次: []            ← 生成器只能消费一次
```

**生成器不存东西，要一个算一个；代价是一次性。** 给 `Counter` 用两种都行（它当场走完），但选生成器省一层列表内存。

### 概念四：`most_common()` 和解包

`most_common()` 返回**排好序的列表**，每项是**二元组** `(东西, 次数)` —— 类型是 `list`，元素类型是 `tuple`。

```python
for 后缀, 个数 in 统计.most_common():
```

**"谁是谁"由位置决定，不是名字。**

```
名字起对照:  后缀=.py   个数=4
名字起反了:  后缀=4     个数=.py     ← 不报错！程序照跑，输出悄悄错位
变量个数对不上: ValueError: not enough values to unpack (expected 3, got 2)
只写一个变量:   拿到整个元组 ('.py', 4)
```

这个机制叫**解包**，跟 `a, b = "x,y".split(",")` 是同一个东西。**变量个数不对会报错，名字起错一个字都不报**——跟 Lambda practice3 那个"变量名/字段名跟踪"的坑是同一类。

**习惯：解包写完，念一遍"这个变量现在装的是什么"。**

⚠️ **平局规则**：`most_common()` 次数相同时**按谁先出现排**，不是字母序。所以关卡 5 里 `.py` 和 `.pyc` 都是 9，`.py` 排前面（rglob 先遇到它）。**数字一样时顺序不唯一，不是 bug。**

### 最终输出

```
.py      9
.pyc     9
```

---

# 第三部分：random + statistics（新知识点）

练习文件：`D:\CC Switch\random_statistics_practice.py` —— **五关全部通过**（2026-09-16）

## 总纲：一句话

**电脑里的"随机"是算出来的（伪随机），起点定了结果就定了；抽样分"放不放回去"；统计量各管一段，平均数最容易被极端值带飞。**

## 关卡 1：边界 —— 到不到头

类比（这一部分一直用）：**一排人站着报数**。

```
randint(1, 6)      "1 号到 6 号，都叫"                  → 1 2 3 4 5 6   （两端都含）
randrange(1, 6)    "从 1 号开始，到 6 号为止，但不叫他"    → 1 2 3 4 5     （不含右端）
random()           永远 < 1.0，取不到 1.0
```

**一句话：`randint` 头尾都算，`randrange` 只算头。** 名字里带 `range` 的都跟 `range()` 一个脾气。

实测（各抽 20 次）：

```
randint(1, 3)     → 20 次里出现了 6 次 3
randrange(1, 3)   → 一次 3 都没有（不是运气差，是压根抽不到）
```

**要掷骰子又想用 randrange，上界必须写 7。**

## 关卡 2：种子 —— 可复现

**种子就是"起点"**：起点相同 → 推出来的那一串完全相同。

实测（**关掉重开、跑了两次独立进程**）：

```
不设种子 第1次： [47, 24, 92]      每次跑都不一样
不设种子 第2次： [78, 74, 70]

seed(42) 第1次： [82, 15, 4]      ⎫ 两次进程完全一样
seed(42) 第2次： [82, 15, 4]      ⎭

seed(42) → [82, 15, 4]
seed(7)  → [42, 20, 51]           起点不同 → 串不同
```

**真实用法**：写死 `random.seed(42)` 发出去，别人跑你的代码能得到一模一样的结果 —— 实验结果才可核对。

## 关卡 3：抽样与打乱

```
sample(列表, 3)      抽 3 个，不重复（抽走不放回）→ 3 个必定各不相同
choices(列表, k=3)   抽 3 个，可重复（抽完放回，多一个 s）→ 可能同一个中两次
shuffle(列表)        把列表本身就地打乱，返回值是 None
```

**shuffle 的实测（本关重点）：**

```
random.shuffle(名字) 的返回值是： None
可是 名字 本身变成了： ['小明', '小刚', '小红']

random.sample(名字2, 3) 的返回值是： ['小明', '小刚', '小红']
可是 名字2 本身还是： ['小明', '小红', '小刚']
```

类比：**`shuffle` = 让这队人当场重新站队**（它自己不汇报什么，所以给 `None`）；**`sample` = 另抄一份新名单给你**（原来那队人站得好好的）。

⚠️ 所以 `print(random.shuffle(名字))` 屏幕上只有 `None` —— **尴尬的是队伍其实已经被打乱了**，你只是没看到。

**跟 pathlib 正好相反**：pathlib 是"改一下给你个新对象，原来那个不动"（不可变）；`shuffle` 是"就地改，不给你新东西"。这一对对照很有用。

## 关卡 4：statistics —— 谁会被带跑

```
mean      平均数   全加起来除以个数（最容易被极端值带跑）
median    中位数   排好队站正中间那个（不受极端值影响）
mode      众数     出现次数最多的那个
stdev     标准差   数据散得开不开（越大越散）
variance  方差     标准差的平方（和标准差是同一个东西的两种说法）
```

实测（`[88, 92, 76, 95, 88, 61, 100]`，把 100 改成 1000）：

```
              原来        现在
平均数        85.7   →   214.3     ← 被带飞
中位数        88     →   88        ← 一动没动
众数          88     →   88        ← 一动没动
标准差        13.2   →   346.7     ← 暴涨
```

**中位数为什么不动**：那队人按大小站好之后，巨人站到最右边去了，正中间站的还是原来那个 88。
**标准差为什么暴涨**：原来大家挤在 60~100 很紧凑；现在有个人孤零零站在 1000，队伍被拉得极开。

现实版：一个老板年薪千万，全公司人均百万 —— **看中位数就骗不了你**。

## 关卡 5：实战 —— train / test split

**概念**：训练模型不能拿全部数据去喂它，得切一块出来当"考题"，训练时不许看。

```python
数据   = list(range(1, 21))                     # 假装 20 条
测试集 = random.sample(数据, 6)                  # 抽 6 条，不重复
训练集 = [x for x in 数据 if x not in 测试集]     # 剩下的
```

**连跑三次实测（这批数据整体平均值 10.5）：**

```
        训练集均值   测试集均值
第1次     9.43        13.0
第2次     10.93        9.5
第3次     10.29        11.0
```

**规律：训练集那列很稳（9.4~10.9），测试集那列晃得厉害（9.5 ↔ 13）。**

**样本越少，越容易被抽偏。** 训练集 14 个数，抽到几个大的会被摊平；测试集只有 6 个，正好抽中 15/16/19/18 就窜到 13。**不是抽得差，是 6 个样本本来就容易偏。**

⚠️ **现实里必须配 `random.seed(42)`** —— 否则每次划分都不一样，换个时间跑一遍结论就变了。**这就是关卡 2 的种子在这里的用处。**

## 本轮踩坑 / 提醒

1. **用 `randrange` 掷骰子，上界要写 7**（写成 6 永远掷不出 6）—— 关卡 1 的考点
2. **两处「回答」注释一直空着**（第 148 行 shuffle 那句、第 185 行平均数那句）—— 用户说了"补完了"但文件里没落笔。**老坑重现：改完要 Ctrl+S，写完念一遍"文件里真有这行字吗"**
3. 关卡 4 的 TODO 3 让改 10000，实际改成了 1000 —— 效果一样，不算错
4. **`round(random.random(), 3)` 用户一开始没看懂** → 拆成三步跑（先单跑 `random.random()` → 再单跑 `round(它, 3)` → 再合起来）就通了。**结论：嵌套函数要从里往外读**；这个讲法有效，以后复用
5. 用户中途说"没太听明白"时的处理（照 [[teaching-style-plain]]）：**别追问，直接拆小步重讲一遍**，最后问"卡在哪个词上"—— 本次这招奏效

## 本轮实验脚本（`D:\CC Switch\`，看完可删）

| 文件 | 演示什么 |
|---|---|
| `_random_demo.py` | randint / randrange / random / uniform 四组对照 |
| `_round_demo.py` | `round(random.random(), 3)` 拆成三步 |
| `_shuffle_demo.py` | shuffle 返回 None 但就地改 / sample 给新列表 |
| `_stats_demo.py` | 100 → 1000 后平均数 vs 中位数 |

---

# 第四部分：re 正则（新知识点）

练习文件：`D:\CC Switch\re_practice.py` —— **五关全部通过**（2026-09-16）

## 总纲：一句话

**正则是一张"通缉令"：描述"那东西长什么样"，而不是"那东西叫什么"。**

```
字符串查找： "388" in 文本   —— 得先知道具体是哪个字，一字不差
正则：       r"\d+"          —— 只知道"那儿有一串数字"，照样全抓出来
```

**写正则必加 `r`**（`r"\d+"` 而不是 `"\d+"`）：不然 `\d` 会被 Python 的转义规则先啃一遍。

## 关卡 1：字符类 —— 怎么描述"一类字符"

```
\d      一个数字             \w      一个词字符（字母/数字/下划线，中文也算）
\s      一个空白             .       任意一个字符（换行除外）
[A-Z]   一个 A~Z 大写字母     [一-龥]  一个中文
```

实测（文本 `"订单 A1024 金额 388 元"`）：

```
\d       -> ['1', '0', '2', '4', '3', '8', '8']     7 个单字符
\d+      -> ['1024', '388']                          2 个数
[A-Z]    -> ['A']
[一-龥]+  -> ['订单', '金额', '元']
\w+      -> ['订单', 'A1024', '金额', '388', '元']    ← 中文也算"词字符"
```

**本关唯一要记的：只差一个 `+`，"一个"就变成"一串"。**

## 关卡 2：量词 —— 怎么描述"要几个"

```
*      0 个或多个（有没有都行）     +      1 个或多个（至少一个）
?      0 个或 1 个（最多一个）       {2,3}  2 到 3 个（说死）
```

实测（文本 `"a ab abb abbb abbbb"`）：

```
ab*      -> ['a', 'ab', 'abb', 'abbb', 'abbbb']    5 个（光秃秃的 a 也算）
ab+      -> ['ab', 'abb', 'abbb', 'abbbb']         4 个（a 被刷掉）
ab?      -> ['a', 'ab', 'ab', 'ab', 'ab']          5 个（最多只吃 1 个 b）
ab{2,3}  -> ['abb', 'abbb', 'abbb']                3 个
```

**量词只管它前面那一个东西** —— `ab*` 里的 `*` 只管 `b`，不管 `a`。

**贪婪**：量词默认"能吃就尽量多吃"。`ab{2,3}` 碰上 4 个 b，规矩说最多 3 个，就只抓 `abbb`。

## 关卡 3：锚点 —— 卡住位置

```
^    卡在【文本开头】那一个位置        $    卡在【文本结尾】那一个位置
\b   卡在【词边界】—— 每个词前后各有一道门
```

实测（文本 `"cat category dog cat"`）：

```
cat      -> ['cat', 'cat', 'cat']    全城搜捕，category 里的也算
^cat     -> ['cat']                  只认位置 0
cat$     -> ['cat']                  只认最后一个位置
\bcat\b  -> ['cat', 'cat']           category 里的被刷掉
```

### ⚠️ 用户在这里卡住过（本次讲得最透的一个点）

> 用户问："城门口只有一个，所以 `^cat` 最多抓 1 个 —— **为什么只抓一个，不应该是两个吗**"

**答案：因为"位置 0"全篇只有一个。**

文本里 `c-a-t` 一共出现 **3 处**（位置 0、位置 4、位置 17），但 `^` 只认**位置 0 这一处**。`^cat` 从位置 0 读：0 是 `c`、1 是 `a`、2 是 `t` → 抓 1 个。抓完继续往后走，位置 1、2、3、4…**哪儿都不是"位置 0"了**，`^` 这条规矩再也不成立。

**不是"城门口有两个"，是"城门口这个地点全城只有一个"。**

用户想要的那"两个"（位置 0 和位置 17），是 `\b` 的活：

- 位置 0 的 cat：左边是文本开头（边界），右边是空格（边界）→ **抓**
- 位置 4 的 cat：右边是 `e`（字母，**不是**边界）→ **不抓**
- 位置 17 的 cat：左边是空格，右边是文本结尾 → **抓**

→ 正好 2 个。

**口诀：`^` 是一处，`\b` 是处处。**

### 讲法（有效，可复用）

拿 `enumerate(文本)` 打出**逐字位置编号表**，让"位置 0 只有一个"变成看得见的东西。再补一段"城门口站的不是 cat"（`"a cat"` 上 `^cat` → `[]`）和"城门口站的是 category"（`^cat` 也能匹配前 3 个字母）两个反例。

## 关卡 4：分组 —— 把想要的那部分圈出来

```
不加括号    ->  ['tom@example.com']         给我整段
加一个括号  ->  ['tom']                     只给我括号里的
加两个括号  ->  [('tom', 'example')]        一个括号一份，装成元组
```

```
m = re.search(r"(\w+)@(\w+)\.com", 文本)
m.group(0) = tom@example.com     整个匹配
m.group(1) = tom                 第 1 个括号
m.group(2) = example             第 2 个括号
```

**`0` 号位是留给"整体"的，括号从 `1` 开始编号。**

`search` vs `findall`：`search` 只找**第一个**，返回"匹配对象"（不是字符串，得用 `.group()` 取）；`findall` 找**全部**，直接给列表。

### 用户问过：`r"(\w+)@(\w+)\.com"` 这个格式有什么说法

逐块拆：

```
r" ( \w+ ) @ ( \w+ ) \. com "
    `--v--'   `--v--'  │   `-v-'
    括号圈块   括号圈块  压住  普通字符
```

**规矩：大部分字符直接写自己（`@`、`com`），只有元字符要拿 `\` 压住。**

正则里的元字符就这 13 个：`. ^ $ * + ? { } [ ] ( ) | \`

实测（文本含 `tom@example.com` 和 `tom@exampleXcom`）：

```
不加反斜杠 (\w+)@(\w+).com   -> [('tom','example'), ('tom','example')]   假邮箱也抓了
加了反斜杠 (\w+)@(\w+)\.com  -> [('tom','example')]                     只抓真的点
```

**`+` 也不能省**：`\w` 只吃一个字符，`(\w)@(\w)\.com` 对 `tom@example.com` 直接返回 `[]`。

### 方括号是"安全屋"

| | `.` 的含义 |
|---|---|
| 方括号**外面** | 任意一个字符 —— 想要真点必须写 `\.` |
| 方括号**里面** | 就是点 —— 写 `.` 就行，进安全屋后元字符失去特殊身份 |

所以 `[\d.]` 不用写成 `[\d\.]`。

## 关卡 5：实战 —— 从日志里抠字段

```python
日志 = """2026-09-16 10:23:45 INFO 用户 u1024 登录成功，耗时 0.35 秒
2026-09-16 10:23:47 ERROR 用户 u2048 登录失败，耗时 1.20 秒"""

结果 = re.findall(r"u(\d+).*?([\d.]+) 秒", 日志)
# [('1024', '0.35'), ('2048', '1.20')]
```

模式逐块拆：

```
u    (  \d+  )   .*?   (  [\d.]+  )   ␣秒
│    `--┬---'   `─┬─'   `----┬----'   `┬'
普通字母  一串数字  尽量少吃  一串"数字或点"  字面量
```

### `?` 的两个身份（容易混）

- **单独用**（`ab?`）= "0 个或 1 个"
- **跟在别的量词后面**（`.*?`、`\d+?`）= "把它前面那个量词改成**非贪婪**"

实测（文本 `"<a> <b> <c>"`）：

```
<(.*)>   贪婪   -> ['a> <b> <c']      一口气吃到最后一个 >
<(.*?)>  非贪婪 -> ['a', 'b', 'c']    每次只吃到最近的那个 >
```

### findall 的返回值跟括号数挂钩

```
整体：  [('1024', '0.35'), ('2048', '1.20')]     类型 <class 'list'>
第一项：('1024', '0.35')                         类型 <class 'tuple'>
```

- 0 个括号 → 字符串列表
- 1 个括号 → 字符串列表（内容是括号里的）
- **2 个及以上括号 → 元组的列表**（每匹配一次，每个括号各产出一份）

**for 怎么接住**：就是**解包**，跟 `for 后缀, 个数 in 统计.most_common():` 同一个机制。**谁是谁由位置决定，名字起反了不报错。**

## 本轮踩坑 / 提醒

1. **关卡 3 说了"写完了"但 TODO 3、4 还是 `...`**（第 159、167 行）—— 「说了改完但文件里没动」这个老坑又出现一次。**对策：跟他说"写完了"之前先自己跑一遍看输出。**
2. 关卡 1 问的"`\w` 含不含中文"，他在对话里答对了，但**没写进注释** —— 提醒补
3. 关卡 2 TODO 4 的「贪婪」回答也一度空着

## 本轮实验脚本（`D:\CC Switch\`，看完可删）

| 文件 | 演示什么 |
|---|---|
| `_re_demo.py` | 字符串查找 vs 正则；`\d+` / `[A-Z]\d+` / `[一-龥]+` |
| `_re_verify.py` | 五关「预期输出」的实跑验证（写教材前必做） |
| `_anchor_demo.py` | `^` `$` `\b` 三组对照 + 两个反例 |
| `_anchor2_demo.py` | **逐字位置编号表** —— 讲透「位置 0 只有一个」 |
| `_group_demo.py` | 括号 / findall / group(0..2) |
| `_fmt_demo.py` | `.` vs `\.`、`\w` vs `\w+` |
| `_lazy_demo.py` | 贪婪 vs 非贪婪、findall 返回元组、for 解包 |

---

# 教学侧 / 环境侧记录

## 本次修正

1. **`logging_practice.py` 第 50 行注释写错**（原说"删掉整行一条都不剩"）——已实跑验证并改成正确说法（还是 3 条，但换丑格式）
2. **我自己写 demo 时踩了个坑**：`"[%s 家的出口] %(levelname)-8s ..." % 级别名` →
   `TypeError: format requires a mapping`
   **原因**：外层想用 `%` 拼标牌，可字符串里还躺着 `%(levelname)s`，Python 把它当成自己的占位符了。
   **修法**：先把标牌单独拼好 `"[%s 家的出口]" % 级别名`，再和格式串用 `+` 接起来。

## 本次产出的实验脚本（`D:\CC Switch\`，看完可删）

| 文件 | 演示什么 |
|---|---|
| `_level_demo.py` | 改门槛数字 → 输出条数 4/3/2/1 |
| `_no_basicconfig.py` | 一行配置都不写 → 还是 3 条，但格式变丑 |
| `_once_demo.py` | basicConfig 只生效一次 / `force=True` 破法 |
| `_fmt_demo.py` | `-8s` / `8s` / 不写宽度的对齐差异 |
| `_two_gates_demo.py` | 两道闸门串联，C 场景实锤"走不到面前" |
| `_names_demo.py` | 一个名字扛多角色 → 报错位置隔了两行 |
| `_inherit_demo.py` | 级别往上问 + `.level` vs `.getEffectiveLevel()` |
| `_propagate_demo.py` | 0 handler 也能打 / 关掉静默消失 / 一条打三遍 |
| `_exc_info_demo.py` | print(e) vs except 外 vs except 内 |
| `_lazy_demo.py` | 20 万次 f-string vs `%s` 实测计时 |

外加一堆 `_xxx_out.txt` 输出快照、`_k2~_k5.txt`、`debug.log`。

> ✅ **以上这批已于 2026-09-16 全部删除**（用户要求清理）。演示内容和真实输出都抄在本篇里，要重跑照着抄即可。
> 更早的并发实验脚本**还在**：`_race_demo.py`、`_process_scale_demo.py`、`_coroutine_object_demo.py`。

## pathlib 留下的东西

- `D:\CC Switch\pathlib_practice.py` —— 5 关全过，**留着**（复习用）
- `D:\CC Switch\pathlib_demo\笔记.txt` —— 关卡 3 建目录+写文件留下的（33 字节），**可删**

---

# 下一步

- ✅ **pathlib 已完成**（2026-09-16），五关全过
- ✅ **`random + statistics` 已完成**（2026-09-16），五关全过 —— 见 `random_statistics_practice.py`，要点在本文「第三部分」
- ✅ **`re` 正则已完成**（2026-09-16），五关全过 —— 见 `re_practice.py`，要点在本文「第四部分」
- 🔵 **下一次的候选新知识点**（还没定，可挑）：`requests` 网络请求 / `dataclasses` 深入 / `datetime` 深入 / `typing` 进阶 / 用 `pytest` 替代 unittest / `re` 进阶（`sub` `split` `compile` 命名分组）
- ⏳ **回炉待改练习**（老账，用户说过暂时不想做，**别主动提**）：
  - `module_tools_review.py` 6 题（三类高频错：缩进/硬编码/语法混淆）——已备好干净题面 `module_tools_review2.py`
  - Lambda `practice3` 题 3/5/8（变量名/字段名跟踪）
  - 属性管理练习 3 处
- ⏳ **健身记录本收尾**：`bonus.py` 加练 3 题（C 的 `strptime + isocalendar` 最陌生）
- ⏳ **刷路线表**：`knowledge-map.md` / `state.json` 停在 8 月中，需按真实进度重写

## 本轮反复强调的自查习惯

1. **写完一行赋值，念一遍"这个名字现在指的是什么东西"**——变了种类就是覆盖 bug（`logger = logging.DEBUG` 型）
2. **一个角色一个名字**，写日志时固定 5 个：`logger` / `控制台` / `控制台格式` / `文件` / `文件格式`；顺序是**创建 → 配置 → 挂载**
3. **打了一条日志什么都没看见** → 先查两道门槛和 handler，别怀疑代码
4. **看到并列的元素先问**："这是两次独立操作，还是一个容器里的两个元素？"（漏分隔符的老坑，换了四张脸）
5. **解包写完，念一遍"这个变量现在装的是什么"**——`for 后缀, 个数 in ...` 名字起反了**一个字都不报**，输出悄悄错位（跟 Lambda practice3 那个坑同类）
6. **参数一多就一律写名字**：`mkdir(parents=True, exist_ok=True)` 不能写成 `mkdir(True, True)`
7. **凡是"建目录/写文件/注册"这类操作，先想"这行被跑第二次会怎样"**——要么幂等，要么显式处理已存在的情况
8. **统计/报表跑完先看一眼结果合不合理**——目录混进后缀统计变成 `'' 3`、缓存文件混进 `.pyc`，都是不报错的错
