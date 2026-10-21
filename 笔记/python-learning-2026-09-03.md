# Python 学习总结 — 2026-09-03

## 今日主题一：模块与工具域 · 综合复习

> 状态：知识点回顾 ✅ + 综合练习**进行中**（7 题首次作答暴露多处错误，待重做）+ 概念澄清 ✅
>
> （同日主题二：Lambda 与高阶函数 + sorted 精讲，见文末「六~九」）

---

## 一、回顾的 4 块知识点（模块与工具域）

### 1. 模块与导入

| 写法 | 效果 |
|------|------|
| `import mt_utils` | 搬进整个模块，`mt_utils.clamp()` 带门牌 |
| `from mt_utils import clamp` | 只抓一个名字，`clamp()` 不带门牌 |
| `import mt_utils as mu` | 起别名 |
| `from mt_utils import PI as p` | 名字起别名 |

- `__name__`：直接运行 = `"__main__"`；被 import = 模块名
- `__all__ = [...]`：控制 `from 包 import *` 导出哪些名字

### 2. 异常处理

- `try / except / else / finally`
- `except (A, B)` 接多种错；`except ... as e` 拿错误细节
- `raise XxxError(...)` 主动抛；自定义异常 `class XxxError(Exception): pass`

### 3. 文件与上下文管理器

- `with open(path, mode, encoding="utf-8") as f` 自动关闭
- mode：`"r"` 读 / `"w"` 覆盖写 / `"a"` 追加写
- 逐行读 `for line in f`，`strip()` 去换行
- 自定义上下文管理器：`__enter__`（进入）+ `__exit__`（退出）
- pathlib：`[str(p) for p in Path(dir).glob("*.py")]`

### 4. venv · 包管理

| 操作 | 命令 |
|------|------|
| 创建 | `python -m venv myenv` |
| 激活 | `source myenv/Scripts/activate` |
| 导出 | `pip freeze > requirements.txt` |
| 还原 | `pip install -r requirements.txt` |

---

## 二、综合练习（module_tools_review.py，7 题）

| 题 | 考点 | 首次作答 |
|---|---|---|
| 0 | 示范：安全读文件 | ✅ 参考 |
| 1 | 读数字列表跳过坏行 | ❌ 4 处错 |
| 2 | import 并调用工具函数 | ❌ 3 处错 |
| 3 | 自定义异常 + raise | ❌ 4 处错 |
| 4 | `"w"/"a"` 写文件 | ❌ 3 处错 |
| 5 | 自定义上下文管理器 Timer | ❌ 结构错 |
| 6 | pathlib 找文件兜底 | ❌ 3 处错 |
| 7 | venv/包管理文字题 | 5/6 对 |

---

## 三、⚠️ 踩坑大全（本次暴露，重点记）

### 1. 缩进层级错 —— 谁管谁（最高频，3 题栽在这）

```python
# ❌ continue 缩进到 for 外面 → SyntaxError: 'continue' not properly in loop
for line in f:
    line = line.strip()
if not line:        # 这行跑到了 for 外面
    continue

# ❌ set_score 缩进到 InvalidScoreError 函数里面 → 外面找不到 set_score
def InvalidScoreError(Exception):
    def set_score(score): ...

# ❌ with 写进 class 体里 → class 里只能放方法定义
class Timer:
    with Timer() as t: ...
```

**规则**：`for` / `if` / `try` 靠缩进认「谁管谁」；`continue`、`except` 必须和它们所属的 `for`/`try` 同层级。

### 2. 硬编码 —— 该用参数却写死

```python
# ❌ 用 path 参数，却写死 "scores.txt" → read_numbers("没有.txt") 也去读 scores.txt
with open("scores.txt", ...)
# ✅
with open(path, ...)

# ❌ Path("direction") 写死 → 应该 Path(directory)
```

### 3. 语法张冠李戴

| 错误 | 正确 | 原因 |
|------|------|------|
| `average[80,90,100]` | `average([80,90,100])` | 调用函数用 `()`，`[]` 是下标 |
| `def InvalidScoreError(Exception)` | `class InvalidScoreError(Exception)` | 异常是类不是函数 |
| `f.read(line + "\n")` | `f.write(r + "\n")` | 写文件用 write |
| `time.time`（漏括号） | `time.time()` | 调用要带括号 |
| `line.append(float(line))` | `result.append(float(line))` | 字符串没 append；该存进 result |
| `for line in f`（写时） | `for r in records` | 遍历错对象：要写的是 records |

### 4. 逻辑错误

- `if score < 0 and score > 100` → 永远 False，要 `or`（一个数不可能同时 <0 又 >100）
- 缺 `return`：函数末尾漏 `return result` / `return [...]`，函数返回 None

### 5. 调用函数 vs 访问属性（一条口诀）

- 调用函数 → `()`：`average(...)`、`time.time()`
- 访问下标/索引 → `[]`：`data[0]`、`d["key"]`

---

## 四、概念澄清：`__exit__` 的 return 值与「吞异常」

### 异常会「传播」（球比喻）

- 代码出错 → 抛出一个异常（扔出一个球）
- 球一层层往外飞，直到被 `except` 接住
- 没人接 → 球砸穿屋顶，程序崩（红字 Traceback）

### `__exit__` 的返回值决定球的下场

| 返回值 | 效果 |
|---|---|
| `return False` | 放行，球继续往外飞（正常行为，Timer 用这个） |
| `return True` | 吞掉，把球装进口袋，外面以为没事 |

**一句话**：`__exit__` 是 with 块结束时自动调用的「值班员」；出异常时它有权「上报」（False）或「压下」（True）。Timer 只计时不揽事，所以 `return False`。

---

## 五、关键文件

- `module_tools_review.py` — 综合练习题目（**待重做**，首次作答未改对）
- `module_tools_review_answer.py` — 参考答案（已跑通）
- `mt_utils.py` — 配套工具模块（题 2 导入用）

## 遗留 / 下一步

- **模块与工具综合练习待重做**：首次 7 题只对了文字题大半，代码题 6 道全需改
- 回顾时发现概念还记得，但「动手写」时缩进层级、参数硬编码、语法混淆三类问题高频复发 → 重做时重点盯这三类
- 重做完后，再决定：回炉 Lambda/属性管理，还是开新主题（标准库精选）

---

## 学习方法小结

- 这次「回顾 → 练习 → 批改」跑下来，最大的收获是暴露了「**概念懂 ≠ 写得对**」：缩进、参数、语法这三类属于「手感」问题，光看会了不够，必须靠重做长出来。
- 后续练习优先「重做改对」，而不是急着开新题。

---

## 【主题二】Lambda 与高阶函数 · 专项强化 + sorted 精讲

> 状态：第 3 版练习完成 ✅ + sorted 精讲 ✅ + 题 3/5/8 待改

### 六、练习结果（lambda_hof_practice3.py，8 题）

| 题 | 考点 | 钉住的坑 | 结果 |
|----|------|---------|------|
| 1 | filter + 取余 | ① % vs / | ✅ |
| 2 | map + 指数 | ① ** 后面数字 | ✅ |
| 3 | reduce 累乘 + 最大值 | ① 运算符号 + 返回布尔 | ⚠️ 结果对、变量用错 |
| 4 | sorted 按长度升降序 | ①③ len 作用对象 + reverse | ✅ |
| 5 | sorted 字典字段 | ② 字段名用错 | ❌ 蒙对 |
| 6 | partial 关键字名 | ② 关键字 = 原参数名 | ✅ |
| 7 | strip+filter+map 链 | ③ x.strip() 挂 x + 分步 | ✅ |
| 8 | 三层嵌套 | ③ 从内往外写 | ❌ 多处错 |

### 七、sorted 知识点精讲（本次重点）

**① `sorted()` vs `list.sort()`**

```python
a = sorted(nums)   # 返回新列表，原列表不动
nums.sort()        # 原地改，返回 None
```

**② `key` 的核心：拿「元素的什么」来比**

- 没有 `key` → 直接比元素本身
- 有 `key` → 先对每个元素调 `key` 算出「代表值」，再比代表值

| 原元素 | `key=len` 算出 | 排序 |
|--------|--------------|------|
| `"dog"` | 3 | 第 1 |
| `"elephant"` | 8 | 第 3 |
| `"cat"` | 3 | 第 2 |
| `"hippopotamus"` | 12 | 第 4 |

**一句话：`key` 是「排序依据的转换器」，不是「怎么比」。**

**③ lambda 做 key：参数 = 元素，返回值 = 排序依据**

```python
sorted(students, key=lambda s: s["score"])
#                     ↑ 参数（每个元素）  ↑ 返回值（拿它排）
# 等价于：def 取分数(s): return s["score"]
```

**④ reverse 升降序**：默认 `False` 升序（小→大），`True` 降序。

**⑤ 稳定性**：代表值相同的元素保持原顺序（`"dog"`/`"cat"` 都长度 3，dog 在前保持在前）。

#### 字典按值排序

`sorted()` 直接比字典时比的是**键**；要按**值**排，先用 `.items()` 把字典拆成
`(键, 值)` 元组，再用 `key` 取每一对的第 2 项：

```python
d = {"苹果": 3, "香蕉": 1, "橘子": 2}

按值升序 = sorted(d.items(), key=lambda kv: kv[1])
# [('香蕉', 1), ('橘子', 2), ('苹果', 3)]

按值降序 = sorted(d.items(), key=lambda kv: kv[1], reverse=True)
# [('苹果', 3), ('橘子', 2), ('香蕉', 1)]
```

**两个坑**：
- `kv` 是 `(键, 值)` 元组，`kv[1]` 才是值；写成 `kv[0]` 就变成按键排。
- 想保留成字典，排完再 `dict(...)`：`dict(sorted(d.items(), key=lambda kv: kv[1]))`。

### 八、三道待改的题（本次新暴露，顽固坑 = 变量名/字段名跟踪）

**题 3**：数据是 `data`，却写了 `nums`（`reduce(..., nums)`）→ 碰巧 `nums=[2,3,4]` 累乘也是 24、最大值也 4，蒙对但错。

**题 5 `by_name`**：要求按 `name` 排，却写了 `s["score"]` → 三人 score 顺序恰好和 name 顺序一致，结果看着对、实则错（换数据就露馅）。

**题 8**：四处错——
1. `reduce` 前漏写 `total =`（结果没存）
2. `x.["price"]` 语法错（`.` 和 `["price"]` 不能连用 → `x["price"]`）
3. `map(lambda x:["price"], ...)` 应为 `x["price"]`（取字段值，不是返回 `["price"]` 列表）
4. `order` 应为 `orders`（变量名少个 s）

### 九、Lambda 遗留 / 下一步

- 题 3 / 5 / 8 待改（本次先写总结，暂不改）
- 改完这 3 题，Lambda 高阶函数可判定掌握
- 顽固坑仍是「变量名/字段名跟踪」：`data`↔`nums`、`name`↔`score`、`order`↔`orders` —— 与主题一「硬编码 / 语法混淆」同根，靠重做长手感
