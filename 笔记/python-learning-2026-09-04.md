# Python 学习总结 — 2026-09-04

## 今日主题：标准库精选（上）· os / json / csv / datetime

> 状态：四关全部一次跑通 ✅（无 TODO 遗留，无踩坑）
>
> 主题定位：这是「标准库精选」的第一步，选的是最常用、最贴近「处理文件和数据的日常」四个模块。

---

## 一、os 模块 —— 路径 / 目录 / 环境变量

| API | 作用 | 记忆点 |
|-----|------|--------|
| `os.getcwd()` | 当前工作目录 | get **c**urrent **w**orking **d**ir |
| `os.listdir(path)` | 列出目录里的内容 | 返回**字符串列表** |
| `os.path.join(a, b, c)` | 拼路径 | **不要手写 `\` 或 `/`**，交给 join |
| `os.path.isdir(path)` | 是不是目录 | 配合 listdir 做「安全列目录」 |
| `os.makedirs(path, exist_ok=True)` | 建多级目录 | `exist_ok=True` 已存在也不报错 |
| `os.path.exists(path)` | 判断存在 | 建完目录用这个确认 |
| `os.environ.get("键")` | 读环境变量 | `os.environ` 是**字典**，用 `.get()` 安全取 |

**安全列目录模板**（第 3 题）：

```python
def safe_list_dir(path):
    if os.path.isdir(path):
        return os.listdir(path)
    else:
        return []          # 目录不存在不崩溃
```

一句话：`os` 管「文件系统的事」——在哪、有什么、建不建、环境变量是啥。

---

## 二、json 模块 —— 装箱（dump）/ 拆箱（load）

**核心比喻**：把 Python 对象「装箱」成文字（方便存文件 / 发网络），用时再「拆箱」变回对象。

| 操作 | 函数 | 方向 |
|------|------|------|
| 对象 → 字符串 | `json.dumps(obj)` | 装箱 |
| 对象 → 文件 | `json.dump(obj, f)` | 装箱到文件 |
| 字符串 → 对象 | `json.loads(s)` | 拆箱 |
| 文件 → 对象 | `json.load(f)` | 从文件拆箱 |

**两条口诀：**

1. **带 s 是字符串，不带 s 是文件**：`dump`**s** / `load`**s** 处理字符串，`dump` / `load` 处理文件。
2. **中文乱码**：`dumps(obj, ensure_ascii=False)` 让中文原样显示；否则变 `\uXXXX`。

**类型对照（装箱时自动转）**：

| Python | JSON |
|--------|------|
| `True` / `False` | `true` / `false` |
| `None` | `null` |
| `dict` | 对象 `{...}` |
| `str` | 字符串（双引号） |

**拆箱取值的套路**（第 3 题）：

```python
r = json.loads('{"code":200, "data":{"user":"小明","score":88}}')
score = r["data"]["score"]   # 先 loads 得字典，再一层层取
```

一句话：json 是「对象 ↔ 文字」的翻译官，存文件 / 读文件都靠它。

---

## 三、csv 模块 —— 读写「表格」（Excel 能打开）

**最大的坑（务必记）**：写 csv 时 `open(..., newline="")` **必须加**，否则 Windows 上每行之间多空行。

### 两种读写方式

| 方式 | 写 | 读 | 每行类型 |
|------|----|----|---------|
| 列表版 | `csv.writer(f)` + `writerow([...])` | `csv.reader(f)` | **列表** |
| 字典版 | `csv.DictWriter(f, fieldnames=[...])` | `csv.DictReader(f)` | **字典**（表头当键） |

### DictWriter 三步（第 0 题示范）

```python
with open("demo.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["姓名", "分数"])
    writer.writeheader()          # ① 先写表头
    writer.writerows(students)    # ② 再写数据行
```

### 读回来（DictReader）

```python
for row in csv.DictReader(f):
    print(row["分数"])   # 每行是 {表头: 值}，按列名取值
```

### 综合题踩坑提醒（第 5 题）

> csv 读出来的分数是**字符串 `"78"`**，要 `float(row["分数"])` 转成数字再算平均分。

一句话：csv 是「表格 ↔ 文本」的翻译官，字典版最顺手（能按列名取值）。

---

## 四、datetime 模块 —— 拿现在 / 格式化 / 解析 / 算时间差

| 操作 | 写法 | 方向 |
|------|------|------|
| 现在 | `datetime.now()` | — |
| 格式化 | `now.strftime("%Y-%m-%d %H:%M")` | 对象 → 字符串 |
| 解析 | `datetime.strptime("2026-09-04", "%Y-%m-%d")` | 字符串 → 对象 |
| 造日期 | `datetime(2026, 9, 4)` | — |
| 算差 | `(end - start).days` | 相减得 timedelta |

**strftime vs strptime 别搞反**（一条记忆钩子）：

- **strf**time → **f**ormat，把对象**格式成**字符串（f = format）
- **strp**time → **p**arse，把字符串**解析成**对象（p = parse）

**常用格式符：**

| 符 | 含义 | 例 |
|----|------|-----|
| `%Y` | 年（四位） | 2026 |
| `%m` | 月 | 09 |
| `%d` | 日 | 04 |
| `%H` / `%M` | 时 / 分 | 16:50 |
| `%A` | 星期几全称 | Friday |

**综合题（第 5 题）**：`(datetime.now() - datetime(出生年,月,日)).days` 算自己活了多少天。

一句话：datetime 管「时间的事」——现在是几点、日期长啥样、过了几天。

---

## 五、四个模块一句话对照

| 模块 | 一句话 |
|------|--------|
| `os` | 管文件系统：路径、目录、环境变量 |
| `json` | 对象 ↔ 文字（装箱/拆箱） |
| `csv` | 表格 ↔ 文本（字典版最顺手） |
| `datetime` | 时间：现在、格式化、解析、时间差 |

---

## 六、关键文件

- `stdlib_os_practice.py` — 第 1 关 os（5 题，全对）
- `stdlib_json_practice.py` — 第 2 关 json（5 题，全对）
- `stdlib_csv_practice.py` — 第 3 关 csv（5 题，全对）
- `stdlib_datetime_practice.py` — 第 4 关 datetime（5 题，全对）
- 练习产物：`stdlib_test/`、`score.json`、`students.json`、`demo.csv`、`scores2.csv`、`report.csv`

## 下一步

- **标准库精选（下）**：还差 `sys`、`collections` 两个常用模块没学
- 之前遗留的回炉项（排队中）：
  - 模块与工具综合练习 `module_tools_review.py`（首次未改对，三类高频错：缩进/硬编码/语法混淆）
  - Lambda `lambda_hof_practice3.py` 题 3/5/8（变量名/字段名跟踪）
  - 属性管理 `property_practice2.py`（3 处待改）

---

## 学习方法小结

- 今天四关「一次跑通、零踩坑」，和前几天「综合练习反复出错」形成对比 —— 说明**单个新模块上手快**，难点在**多个知识点串联**（如 module_tools_review 那种混合题）。
- 所以后续节奏可以：**新模块单独练 → 每学一段就做一次「串联综合」**，把单个会写的动作，练成能互相配合的本事。

---

## 【下篇】标准库精选（下）· sys / collections

> 状态：两关练习完成 ✅（首次 3 处小错，改后全绿）
> 说明：学完这俩，「标准库精选」整体收官。

### 七、sys 模块 —— 和「解释器自己」对话

| API | 作用 |
|-----|------|
| `sys.argv` | 命令行参数列表：`[0]` 是脚本名，后面是运行时敲的参数 |
| `sys.exit(消息)` | 主动退出程序（可带提示） |
| `sys.path` | 模块搜索路径列表（Python 去这找 import） |
| `sys.version` / `sys.platform` | Python 版本 / 平台（`win32`） |
| `sys.stdout.write(...)` | 输出文字，**不自动换行**（要自己加 `\n`） |

**关键套路**：读命令行参数要「先判断 `len(sys.argv) >= 2`，再取 `sys.argv[1]`」，否则没传参数时取 `[1]` 会 `IndexError`。

### 八、collections 模块 —— 强化版容器

| 容器 | 解决什么 | 关键点 |
|------|---------|--------|
| `Counter` | 统计出现次数 | 传列表/字符串直接数 |
| `.most_common(n)` | 取前 n 名 | 返回 `[(元素, 次数), ...]` |
| `defaultdict(工厂)` | 新键自动造默认值 | 工厂如 `list` |
| `namedtuple("名", [字段])` | 元组元素起名字 | 用 `.x` 取值，不是 `[0]` |
| `deque` | 双端队列 | `popleft()` 先进先出 |

### 九、两个关键概念（本次真正搞懂）

**① 链式调用**：`Counter(fruits).most_common(2)`
「点」前面要先算出一个对象。`fruits` 是 list，没有 `.most_common`；`Counter(fruits)` 的结果是 Counter，才有。等价两步：`c = Counter(fruits)` → `c.most_common(2)`。

**② defaultdict 分组**：
```python
d = defaultdict(list)      # 工厂 list，新键自动造 []
for w in words:
    d[w[0]].append(w)      # w[0]=首字母
```
普通 dict 要「先查键在不在再放」，defaultdict 把「查」自动化了。

### 十、popleft 的「返回值 + 副作用」

`x = Tasks.popleft()` 做两件事：① 删掉队首（队列变短）② 把删掉的元素「返回」给你。
- 接住：`x = Tasks.popleft()`；不接住直接打印：`print(Tasks.popleft())`
- `while Tasks:` 循环取完，取空后空 deque 是 `False`，自动停。

### 十一、⚠️ 踩坑（本次暴露，和前几天的老坑同根）

1. **`{sys.argv[1]}` 花括号是「集合」，不是占位符** —— 题目「`你好, {参数}`」的 `{参数}` 只是记号，实际写 `sys.argv[1]` 不加花括号。
2. **调用函数漏括号**：`sys.exit` 只是「提到」函数，`sys.exit("...")` 才「调用」。← 和之前 `time.time` 漏括号同坑。
3. **变量名前后不一致**：`a = defaultdict(list)` 后面却写 `d[...]` → NameError。← 顽固坑「变量名跟踪」。
4. **类型搞错**：`fruits.most_common(2)`，list 没这方法，要先 `Counter(fruits)`。
5. **工厂 vs 调用**：`defaultdict(list(words))` 错，应传工厂 `list`（函数本身），不是 `list(words)` 的结果。

### 十二、关键文件

- `stdlib_sys_practice.py` — 第 5 关 sys（5 题，全对）
- `stdlib_collections_practice.py` — 第 6 关 collections（5 题，全对）

## 标准库精选 · 收官

六个模块学完：`os` / `json` / `csv` / `datetime` / `sys` / `collections` ✅，「常用标准库」知识点整体完成。

## 下一步（更新）

- 回炉（排队中，优先）：
  - 模块与工具综合练习 `module_tools_review.py`
  - Lambda `lambda_hof_practice3.py` 题 3/5/8
  - 属性管理 `property_practice2.py`（3 处）
- 之后可开「工程实践」：类型注解 / 测试 / PEP8 / 调试
