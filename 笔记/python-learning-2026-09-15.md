# Python 学习总结 2026-09-15 —— 并发综合题精讲 + logging 日志

> **路线图进度**：8 个域全部走完，无荒地。本次新开「标准库精选 · logging」。
> 讲解：`D:\CC Switch\concurrency_review.py`（6 题，本轮**逐题精讲**，不是查错）
> 练习：`D:\CC Switch\logging_practice.py`（5 关，**全部通过**）
> 产出：`D:\CC Switch\debug.log`（关卡 3 的日志文件，可删）

---

# 第一部分：concurrency_review.py 逐题精讲

## 一、题 1 武器选择 —— 决策三问

```
第 1 问：在等还是在算？
   等（网络/磁盘/DB）→ IO 密集
       ├─ 有异步库？   → D 协程
       └─ 只有同步库？ → E 协程 + to_thread
   算（纯 Python 循环）→ CPU 密集 → C 多进程

第 2 问：要不要返回值？
   协程 → await（顺序有保证）
   线程 → append / args 传容器 / ThreadPoolExecutor.submit
   进程 → Queue 或 Pool.map（注意 pickle 成本）

第 3 问：有没有卡住事件循环？
   有 → asyncio.to_thread 兜底
```

**六个场景的答案**：1=D 2=C 3=D 4=E 5=C 6=A

题里最值的两个点：

- **场景 6 选 A（串行）**——并发有起步价。20 个小文件共 2MB，串行几十毫秒；起 4 个进程光启动就 0.4 秒。**量小就别上并发。**
- **场景 5 特意写了"结果是 10MB 数组"**——暗桩是"跨进程要 pickle 传输，10MB×8 的通信成本要算进账"。

## 二、题 2 线程 —— 收返回值 + 锁

**收集返回值的三种写法**

| 写法 | 代码 | 什么时候用 |
|---|---|---|
| 闭包 append | `results.append(干活(name))` | 纯线程、一次性脚本 |
| **传容器进 args** | `Thread(target=抓取, args=(u, 桶))` | 干活函数是**模块级的**，或以后要换进程 |
| `ThreadPoolExecutor` | `ex.submit(...)` → `f.result()` | 工业界标准，顺序也有保证 |

- **闭包为什么不用 nonlocal**：`results.append(...)` 只是"调用方法"，没有给 `results` 重新赋值。写成 `results = results + [x]` 才会 `UnboundLocalError`。
- **传容器进 args 的硬理由**：闭包 pickle 不了。子进程报
  `PicklingError: Can't pickle local object '<locals>.套壳'`。
  而 `queue.Queue` 和 `multiprocessing.Queue` 接口一模一样（都有 `put`/`get`，鸭子类型），所以**同一个模块级函数线程版进程版通吃**。

**为什么 `+= 1` 会丢数**

```python
SHARED["count"] += 1     # 底层是三步：LOAD → BINARY_OP → STORE
```

GIL 只保证"单条字节码不被打断"，不保证"这三条连起来不被打断"。切换恰好落在 LOAD 和 STORE 中间 → 一次加法蒸发。

⚠️ **反直觉但极重要**：09-11 实测，不加锁 + 不加 sleep 时**没丢过数**（概率极低），加了 `time.sleep(0)` 强制让位立刻丢 83%。**"测了一万次没出事"不等于安全。**

**本题最值钱的坑：start 和 join 必须分两个循环**

```python
for t in threads: t.start()     # ✅ 先全部发牌
for t in threads: t.join()      # ✅ 再全部收牌

for t in threads:
    t.start(); t.join()         # ❌ 起一个等一个 → 完全串行，1.00 秒
```

## 三、题 3 多进程 —— 一堵墙，一扇门

**墙（内存隔离）的底层**：`args` 走 pickle → 通过管道 → 子进程 unpickle 出一个**全新对象**。所以父进程看到的永远是 `[]`。

**什么不能 pickle**：lambda、打开的文件对象、`threading.Lock`。这就是为什么进程间不能用锁、只能用 Queue。

**门（Queue）的底层**：一条操作系统管道 + 一把锁 + 一个后台 feeder 线程。**用「传送带 + 编号卡」理解**：你在传送带上放包裹，对面取下来，包裹在传送带上时谁都不拥有它。

三个特性：

1. `get()` 在空队列上**永久阻塞** → 用 `q.get(timeout=5)` 防卡死
2. put/get 自带锁，不用你包 `with LOCK`
3. 只能传给有亲缘关系的进程（父→子）

> **分界线**：共享内存模型（线程，靠锁）vs 消息传递模型（进程，靠 Queue）。
> 锁只在"共享同一块内存"时有意义。

**Pool.map vs 手动 Process**：`map` 是数据并行（同一函数作用在一批数据上），手动 `Process` 是任务并行（每个进程干不同的事）。`Pool` 记得用 `with` 包住，否则进程回收靠运气。

**Windows 的 spawn**：全新解释器进程，**重新 import 模块** → 所以创建进程必须放在 `if __name__ == "__main__":` 里，否则无限套娃。推论：**子进程里的模块级变量永远是初始状态**。

## 四、题 4 asyncio —— gather 的顺序陷阱

- **卡片模型**：调用 `async def` 只开票，`await` / `gather` / `create_task` 才算递进后厨。
- **串行 0.93 秒 vs 并发 0.31 秒**：串行是 `await` 把循环钉住；并发是列表推导先开好 3 张票，`*` 摊开，一起递进去。
- **`gather` 返回的顺序 = 传入顺序，不是完成顺序**。内部给每个协程编了号，结果放回原格子。对比题 2 的线程：进度条谁先进谁排前面，顺序不可预测。
- **`await` 底层是 `yield`**：协程就是用生成器把异步 IO 写得像同步代码。
- ⚠️ **`gather` 遇到异常不会取消其他协程**（要自动取消用 `asyncio.TaskGroup`）。

## 五、题 5 to_thread —— 最贴求职方向的一题

**为什么"坏版本"是 3.00 秒**：`坏包装` 是 `async def` 但里面没有 `await`，`time.sleep` 把**整个操作系统线程**按睡了，而事件循环就在这个线程上 → 另外两个协程连被看一眼的机会都没有。

**判断口诀**

```
函数签名是 async def？
├─ 是 → 直接 await（顺便检查它内部真的 await 了 IO）
└─ 否 → 且会阻塞 → asyncio.to_thread(函数名, 参数...)
```

**`to_thread` 背后是 `ThreadPoolExecutor`**，默认 `min(32, cpu_count()+4)` 个线程。所以"我以为并发 100"，实际可能"并发 8，排队 92"。

**为什么不直接全用线程**：

| 方案 | 1000 个并发请求 |
|---|---|
| 全线程 | 1000 × 8MB 栈 ≈ 8GB，爆 |
| 全协程 | 几百 KB，但同步库堵事件循环 |
| **协程 + 小线程池** | 协程扛并发量，同时只有 8 个真占线程 |

## 六、题 6 决策闭环 —— 实测数据

```
6A IO 密集（4 个任务各 0.5 秒）
  串行 2.00s   线程 0.50s   协程 0.50s   → 4 倍

6B CPU 密集（4 个任务各 500 万次）
  串行 3.97s   线程 3.88s   进程 0.62s
                       ↑ 0.98 倍，基本白干（GIL 实锤）
                                   ↑ 6.4 倍
```

线程在 6A 和协程并列第一，因为 **`time.sleep` 会主动释放 GIL，GIL 挡的是"算"不挡"等"**。

---

# 第二部分：logging 日志（标准库精选 · 新知识点）

## 一、print 的四个死穴

关不掉 / 没上下文 / 不能分流 / 没法分级。

> `print` 是喊一嗓子，`logging` 是写工作日报。

## 二、五大件

```
logger.info("消息")
   ├─ ① 级别够吗（logger.level）？ 不够 → 扔
   ├─ ② 交给这个 logger 挂着的【每个】handler
   │       ├─ Handler A → Formatter → 控制台
   │       └─ Handler B → Formatter → 文件
   └─ ③ 传播给父 logger（propagate=True）→ 父的 handler 再来一遍 ⚠️ 重复打印的元凶
```

**两道闸门**：`logger.setLevel()` 决定"要不要放行"，`handler.setLevel()` 决定"这个渠道收不收"。**都得过。**

**Formatter 挂在 Handler 上，不在 Logger 上**（控制台和文件可以有不同格式）。

## 三、级别 + 最大的坑

`DEBUG 10 / INFO 20 / WARNING 30 / ERROR 40 / CRITICAL 50`。设了 N，只有 `>= N` 的放行。

⚠️ **root logger 默认是 WARNING** —— 这就是 `logging.info("hi")` 什么都不打印的原因。

⚠️ **大小写**：

```python
logging.debug("hi")     # 小写 = 函数（动作）
level=logging.DEBUG     # 大写 = 常量（名词，整数 10）
logging.INFO(...)       # ❌ 20(...) → TypeError: 'int' object is not callable
```

## 四、两条路

| | 写法 | 脾气 |
|---|---|---|
| 快通道 | `logging.basicConfig(...)` | 只配 root；**只在 root 没有 handler 时生效**，第二次静默忽略 |
| 工程路 | `logger = logging.getLogger(__name__)` | 每个模块一行，配置只做一次 |

同进程想重配：`basicConfig(..., force=True)`。

## 五、层级树

`getLogger("shop.service")` 自动是 `getLogger("shop")` 的子节点。三个好处：名字自带出处、级别会继承、可按模块单独调级别。

⚠️ 给父和子**都**挂 handler → 同一条日志打两遍。解法：只挂一处，或 `propagate = False`。

## 六、Handler 与 Formatter

`StreamHandler`（控制台）/ `FileHandler` / `RotatingFileHandler`（按大小切，生产标配）/ `TimedRotatingFileHandler`（按时间切）。

格式串常用字段：`%(asctime)s` `%(levelname)-8s` `%(name)s` `%(funcName)s` `%(lineno)d` `%(message)s` `%(threadName)s`。

`-8s` = 左对齐补到 8 格，让列整齐。

⚠️ **Windows 写文件必须 `encoding="utf-8"`**，否则中文乱码。

## 七、惰性格式化（面试会问）

```python
logger.debug(f"耗时 {耗时}")       # ❌ f-string 先算出来，不管级别够不够
logger.debug("耗时 %s", 耗时)      # ✅ 级别不够时字符串根本不构造
```

真实写法：`logger.info("模型调用完成 model=%s 耗时=%.2fs tokens=%d", model, 耗时, n)`

## 八、logging_practice.py 五关（全部通过）

| 关 | 练什么 | 结果 |
|---|---|---|
| 1 | basicConfig + 级别门槛 | ✅ 5 条 |
| 2 | Formatter 格式串（自带出处） | ✅ `下单:89` |
| 3 | 双通道（控制台 INFO / 文件 DEBUG） | ✅ 控制台 2 条，文件 3 条 |
| 4 | getLogger 层级继承 | ✅ `shop.service` / `shop.storage` |
| 5 | 实战：调模型加日志（堆栈 + 惰性格式化） | ✅ 7 行含 traceback |

**关卡 4 的两道思考题答案**：

- Q1 没给 `shop.service` 设级别，为什么能打？→ **继承**父 logger `"shop"` 的 INFO。
- Q2 没给它挂 handler，日志怎么出来的？→ **propagate**，把记录往上递给父 `"shop"`，父的 handler 打了。

---

# 第三部分：讲解风格约定（2026-09-15 明确要求，以后一律照办）

用户原话："把这个死死记住，以后都这样。"

1. **一次只讲一个概念**，短句，不堆料
2. **先跑一小段代码看到现象，再解释为什么**
3. **少用表格和表情**，一个类比贯穿到底
4. **查错只说"哪一行、改成什么"**，不顺便讲原理

**起因**：讲 logging 时一次性灌了五大件 + 级别 + 两条路 + 层级树 + Handler + Formatter + 惰性格式化，每条消息几百行，满屏加粗表格和 ⚠️🧠💼 表情，三套类比互相打架。用户反馈"一头雾水""不知道你在说什么"。

**核心教训：满屏都是重点 = 没有重点。**

---

# 第四部分：本日踩坑记录

## 反复出现的顽固模式

**① 大小写当反了（logging 专属）**
`logging.debug` 当级别用、`logging.INFO(...)` 当函数用——**一头一尾两种错同时出现**，说明"小写=函数 / 大写=常量"的对照还没建立。

**② 「对象.方法 = 值」（第 4 次）**

```python
logger = logging.DEBUG          # ❌ 把 Logger 变量换成了整数
logger.setLevel(logging.DEBUG)  # ✅
```

前三次：`threads.append = ...`、`results.append = 队列.get()`、`[results.append for t.await in tasks]`。
**这次的判别信号变了**：不是"方法名没跟括号"，而是"**这个变量名刚还是 A 类型，现在被赋值成 B 类型了**"。
新对策：写完一行赋值，念一遍"**这个名字现在指的是什么东西？**"

**③ 一个变量名扛四个角色（本次新发现）**

```python
logger = logging.getLogger("shop")      # Logger
logger = logging.StreamHandler()        # 覆盖成 Handler
logger = logging.Formatter("...")       # 又覆盖成 Formatter
logger.addHandler(...)                  # 现在是 Formatter，没有这个方法
```

关卡 3 和 4 都栽在这。**四个角色要四个名字**：

| 角色 | 名字 | 长什么样 |
|---|---|---|
| 谁在记 | `logger` | `logging.getLogger("shop")` |
| 去哪（甲） | `控制台` | `logging.StreamHandler()` |
| 甲长什么样 | `控制台格式` | `logging.Formatter("...")` |
| 去哪（乙） | `文件` | `logging.FileHandler(..., encoding="utf-8")` |
| 乙长什么样 | `文件格式` | `logging.Formatter("...")` |

装配顺序：**创建 → 配置 → 挂载**。跳过"创建"直接 `setLevel` → `UnboundLocalError`。

**④ 改了新写法，旧的没删（新）**

关卡 2 里 `logging.info(下单(...), 下单(...))` 没删，又在下面加了两行绕路的。
**以前是"删了不该删的"，这次是"该删的没删"——同一个根因：改代码时没把旧内容当成需要清理的东西。**
对策：改完一处，回头看"**这附近还有没有别的行在干同一件事？**"

**⑤ 并列的东西塞进一个容器里**
关卡 2 的 `logging.info(下单("A001"), 下单("A002"))`——两次独立调用被套进一次调用。
前几轮：`("A")("B")`（除法）、`blocking_call(笨重1", 1.0)`。

**⑥ 全角逗号（第 N 次）**
`logger.info("... %s", 耗时，回答)` → `SyntaxError: invalid character '，' (U+FF0C)`。

**⑦ 参数放错函数**
关卡 5 把 `会失败=True`（`调用模型` 的参数）塞进了 `logger.debug(...)`。**根本没调用 `调用模型`**，全在打日志。

## 新学会的 API

`logging.getLogger` / `setLevel` / `StreamHandler` / `FileHandler(encoding=)` / `Formatter` / `setFormatter` / `addHandler` / `propagate` / `exc_info=True` / `basicConfig(force=True)`

---

# 第五部分：下一步

## 下次开场任务（用户 2026-09-15 明确指定）

> **从头到尾、一关一关精讲 `D:\CC Switch\logging_practice.py`**（5 关已全部通过）。
> 形式同本轮对 `concurrency_review.py` 的做法：**当教材讲透，不是查错**。
> ⚠️ 讲解必须遵守第三部分的四条风格约定。

各关的讲解重点：

| 关 | 讲什么 |
|---|---|
| 1 | 为什么 `basicConfig` 只生效一次；`logging.debug` 和 `logging.DEBUG` 是两回事；级别门槛的"三次实验" |
| 2 | 格式串每个占位符对应什么；`funcName:lineno` 怎么帮定位；为什么关卡 2 的 name 列是 root |
| 3 | **两道闸门**（logger.level vs handler.level）；四个角色为什么必须分开；同一记录两个出口两套格式 |
| 4 | 层级树；`propagate` 的机制；父没设 level 会怎样；重讲 Q1/Q2 |
| 5 | `exc_info=True` 的机制；惰性格式化为什么只对 DEBUG 有意义；这个模式在真实 AI 应用里的样子 |

## 其他待办

- ⏳ **刷路线表**：`knowledge-map.md` / `state.json` 停在 8 月中，标着 10/28（**而且文件自己算错了，按 state.json 逐条数是 9**），线程/多进程/asyncio 还写着 `unexplored`。真实是 **28 项：18 项过关 / 10 项有尾巴 / 0 项没碰**。
- ⏳ 补 `concurrency_asyncio_practice.py` 题 2b 漏掉的 `await`
- ⏳ 回炉：`module_tools_review.py` 6 题 / Lambda `practice3` 的 3·5·8 / 属性管理 3 处
- ⏳ 下一步知识点候选：**`pytest`**（只有 unittest 底子，面试默认问 pytest）、`pathlib`、`random + statistics`

## 路线图的真实缺口（这 5 块才是有价值的空白）

| 缺口 | 现状 | 求职价值 |
|---|---|---|
| **logging** | ✅ **本次已补** | ⭐⭐⭐⭐⭐ |
| **pytest** | 🟡 只会 unittest | ⭐⭐⭐⭐⭐ |
| **正则 re** | 🔴 完全没学 | ⭐⭐⭐⭐ |
| **TypedDict / Protocol / mypy** | 🟡 只有基础注解 | ⭐⭐⭐⭐ |
| **cProfile / timeit** | 🔴 完全没学 | ⭐⭐⭐ |
