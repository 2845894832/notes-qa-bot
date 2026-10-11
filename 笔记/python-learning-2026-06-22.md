# Python 学习笔记 — 2026-06-22

## 今日主题：数据结构（列表 & 字典）

---

## 一、列表 (list)

### 基本操作

| 方法 | 作用 | 例子 | 注意 |
|------|------|------|------|
| `append(x)` | 追加到末尾 | `nums.append(7)` | 只加一个元素 |
| `remove(x)` | 按**值**删除 | `nums.remove("橘子")` | 删第一个匹配项 |
| `pop(i)` | 按**索引**删除并返回 | `x = nums.pop(0)` | `i` 是索引不是值 |
| `insert(i, x)` | 在索引 i **之前**插入 | `nums.insert(1, "葡萄")` | 右侧元素全部右移 |
| `list[i:j]` | 切片 | `nums[1:4]` | **含 i 不含 j** |

### 常见坑

- `fruits[1] = "草莓"` 是**替换**，不是插入，原元素消失
- `fruits("橘子")` ❌ — 列表不是函数，要用 `fruits.remove("橘子")`
- `pop[i]` ❌ — 是方法调用，用圆括号：`nums.pop(i)`
- 切片 `[1:4]` 取索引 1,2,3，**不含 4**

### 练习记录

```python
fruits = ["苹果", "香蕉", "橘子"]
fruits.append("西瓜")          # ["苹果", "香蕉", "橘子", "西瓜"]
fruits[1] = "草莓"             # ["苹果", "草莓", "橘子", "西瓜"]
fruits.remove("橘子")          # ["苹果", "草莓", "西瓜"]
deleted = fruits.pop(0)        # deleted='苹果', fruits=['草莓', '西瓜']
fruits.insert(1, "葡萄")       # ['草莓', '葡萄', '西瓜']
nums[1:4]                      # [1, 2, 3] — 含头不含尾
```

---

## 二、字典 (dict)

### 基本操作

| 操作 | 写法 | 说明 |
|------|------|------|
| 定义 | `d = {"a": 1, "b": 2}` | 花括号，键值用冒号 |
| 取值（硬）| `d["a"]` | 键不存在 → 💥 KeyError |
| 取值（软）| `d.get("a", 默认)` | 键不存在 → 返回默认值 |
| 改/加 | `d["c"] = 3` | 键存在=改，不存在=加 |
| 删除 | `del d["a"]` | 键不存在也报错 |

### 遍历

```python
for k in d:              # 遍历键（默认）
for v in d.values():     # 遍历值
for k, v in d.items():   # 键值一起
```

**坑：** `for key in dict` 遍历的是**键**，不是值！

### `.get()` vs 方括号

```python
d = {"a": 1}

d["b"]          # 💥 KeyError
d.get("b")      # None（不报错）
d.get("b", 0)   # 0（返回默认值）
```

### 列表 + 字典组合

```python
students = [
    {"name": "小明", "score": 95},
    {"name": "小红", "score": 87},
]

for s in students:        # s 是整个字典
    print(s["name"])      # 从字典取值
    # s["score"] 取分数
```

**注意：** `s` 是字典不是字符串，`students` 是列表没有 `.score` 属性。

---

## 三、今日易错点

| 错误 | 正确 | 原因 |
|------|------|------|
| `fruits(0)` | `fruits[0]` | 列表用方括号索引 |
| `fruits.remove = "橘子"` | `fruits.remove("橘子")` | 方法是调用不是赋值 |
| `pop[5]` | `nums.pop(5)` | 方法用圆括号 |
| `insert(nums[3]) = 35` | `nums.insert(3, 35)` | insert 是方法，参数在括号里 |
| `d.get["k"]` | `d.get("k")` | 方法用圆括号 |
| `for k,v in list:` | `for s in list: s["k"]` | 列表只吐一个元素 |
| `students.score` | `s["score"]` | 列表没有属性，字典用键访问 |
| 中文括号 `（）` | 英文括号 `()` | Python 只认英文标点 |

---

## 进度

- ✅ 列表 (list) — 已掌握
- ✅ 字典 (dict) — 已掌握
- ⬜ 元组 (tuple) — 待学
- ⬜ 集合 (set) — 待学
