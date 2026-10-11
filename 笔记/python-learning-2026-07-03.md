# Python 学习笔记 — 2026-07-03

## 新学

### enumerate()（被动接触）
```python
# enumerate 自动给每个元素配序号
for i, item in enumerate(fruits):
    print(i + 1, item)

# 等价写法（用已学的 for + 计数器）
i = 1
for item in fruits:
    print(i, item)
    i = i + 1
```

## 复习：数据结构四大件

### 列表 `[]` — 有序、可改
```python
fruits.append("苹果")   # 末尾加
fruits.remove("香蕉")   # 按值删
fruits.pop(0)           # 按位置删
fruits.insert(1, "西瓜") # 指定位置插
"苹果" in fruits         # 判断存在
fruits[0:2]              # 切片
```

### 字典 `{键: 值}` — 键值对
```python
stu["name"]              # 取值，键不存在报错
stu.get("name")          # 取值，键不存在返回 None
stu.get("score", "无")   # 取不到用默认值
stu["score"] = 95        # 加新键值对
del stu["age"]           # 删键值对

# 遍历
for k in stu.keys()      # 所有键
for v in stu.values()    # 所有值
for k, v in stu.items()  # 键值一起

# 列表 + 字典组合
students = [{"name": "小明"}, {"name": "小红"}]
```

### 元组 `()` — 不可变
```python
x, y = (3, 4)            # 解包
a, b = b, a              # 交换（本质是元组解包）
return "小明", 17         # 返回多个值，就是个元组
```

### 集合 `{}` — 无序、去重
```python
a & b     # 交集
a | b     # 并集
a - b     # 差集
s.add(5)       # 加
s.remove(3)    # 删（不存在报错）
s.discard(10)  # 删（不存在不报错）
set([1,1,2,3]) # 去重 → {1, 2, 3}
```

## 常犯错误（今天出现的）

### 1. `int(input())` 没保护（再现）
输入字母直接崩。先 `.isdigit()` 再转。

### 2. 字典/列表取值混（新出现）
```python
# ❌ books 是列表
books["库存"]

# ✅ book 是字典
book["库存"]
```
`books` 是列表用 `[]` 取位置，`book` 是字典用 `["键"]` 取值。

### 3. 累加器每轮重置（新出现）
```python
# ❌ 循环里写 z = 0 + x，每次归零
# ✅ z 初始化为 0 放循环外面，循环里 z = z + x
```

### 4. 集合每轮重建（新出现）
```python
# ❌ 循环里每轮 set(x)，上一轮丢了
# ✅ set() 放循环外面，循环里 .add(x)
```

### 5. `==` 当 `=` 用（再现）
```python
# ❌ big == book   这是比较，不是赋值
# ✅ big = book    赋值用单等号
```

### 6. `print[...]` 用错括号（新出现）
`print` 是函数，用 `()` 不是 `[]`。

### 7. 字典和字符串直接比（新出现）
```python
# ❌ if book == "张三":   book 是字典，永远不等于字符串
# ✅ if book["作者"] == "张三":
```

### 8. `...` 不是占位符（新出现）
```python
# ❌ {"书名": ...}   存的是 Ellipsis 对象
# ✅ {"书名": name}   用 input() 获取的变量
```

## 相关文件

- `D:\CC Switch\73e1.py` — 日记本练习
- `D:\CC Switch\73e3.py` — 图书管理系统（初版，8类错误）
- `D:\CC Switch\73e3_correct.py` — 图书管理系统（修正版，逐行对比）
