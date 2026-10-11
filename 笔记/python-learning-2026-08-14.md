# Python 学习总结 — 2026-08-14

## 今日主题：异常处理 + 文件与上下文管理器

---

## 一、异常处理（Exception Handling）

### 学了什么

5 个核心技能，让程序出错时不崩溃、能补救：

| 语法 | 作用 | 一句话 |
|------|------|--------|
| `try/except` | 接住运行时错误 | 出错不崩溃，走补救 |
| `except (A, B)` | 一个 try 接多种错误 | 用元组一次接多个 |
| `except ... as e` | 读取错误细节 | 把错误对象存到 e |
| `else` / `finally` | 成功才走 / 无论如何走 | 分离成功逻辑 + 兜底清理 |
| `raise` + 自定义异常 | 主动抛错 | 自己判定不合理就报错 |

### 关键收获

- 异常是"运行时"错误，和语法错误不同
- `except` 从上到下匹配，匹配到一个就停止 → 具体放前、宽泛放后
- `finally` 即使 `return` 了也会先执行（在真正返回之前）
- 自定义异常继承 `Exception`，`raise Xxx("消息")` 时消息自动成为异常内容

### 踩坑 / 注意点

- `except Exception` 放在具体异常之后 = 死代码（具体异常已接走）
- `int()` 只能转整数，"3.14" 会失败；要小数用 `float()`
- 自定义异常类其实 `class X(Exception): pass` 就够，`raise` 传入的字符串自动成为消息
- Windows 终端中文乱码 → 运行前加 `PYTHONIOENCODING=utf-8` 解决

### 练习文件

- `exception_practice.py` — 5 道题，全部通过 ✅

---

## 二、文件与上下文管理器

### 学了什么

5 个核心技能：

| 概念 | 代码 | 一句话 |
|------|------|--------|
| 文件模式 | `open(name, "r"/"w"/"a", encoding="utf-8")` | w 覆盖、a 追加，编码必写 |
| with 语句 | `with open(...) as f` | 自动 close，出错也关 |
| 逐行读 | `for line in f` | 比 read() 省内存 |
| 自定义上下文管理器 | `__enter__` / `__exit__` | 自己写的类也能用 with |
| pathlib | `Path(".").glob("*.py")` | 用 / 拼路径，现代写法 |

### 关键收获

- `with` 是 `try/finally` 的语法糖，文件在 `__exit__` 里自动 close
- `"w"` 会先清空文件，`"a"` 在末尾追加；用 `"x"` 可防止误覆盖
- `for line in f` 逐行迭代，配 `strip()` 去换行
- 自定义上下文管理器：`__enter__` 返回值给 `as` 后面的变量，`__exit__` 里做清理
- `sum(1 for _ in f)` 数行数 —— 这是生成器表达式，下一站"迭代器/生成器"的伏笔
- 练习里用了列表推导式 `[line.strip() for line in f]`，提前掌握了后续内容

### 踩坑 / 注意点

- 文本文件不写 `encoding="utf-8"`，Windows 默认 GBK，中文会乱码
- `return` 之后的 `pass` 是死代码，永远执行不到，应删掉
- `Timer.__enter__` 要 `return self`，外部才能通过 `as t` 拿到实例、读 `t.elapsed`

### 练习文件

- `file_context_practice.py` — 5 道题，全部通过 ✅

### 进度

- 异常处理 ✅ 完成
- 文件与上下文管理器 ✅ 完成
- 下一站：迭代器与生成器
