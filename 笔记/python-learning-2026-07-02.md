# Python 复习笔记 — 2026-07-02

## 复习范围

基础入门（4个概念全部重温）：变量与数据类型、控制流、函数基础、输入输出

---

## 复习的基础入门知识点

### 变量与数据类型
- `str` 和 `int` 是不同类型，不能直接运算，要用 `str()` 或 `int()` 转换

```python
a = "5" + str(5)   # "55"
b = 10 + int("3")  # 13
```

- `True + 1` 等于 `2`，因为 `True` 就是 `1`，`False` 就是 `0`

```python
print(True + 1)   # 2
print(True + False)  # 1
```

- `/` 除法永远返回 float

```python
print(10 / 3)   # 3.3333333333333335
```

- `//` 整除，向下取整

```python
print(10 // 3)  # 3
```

### 控制流
- `while True:` 创建死循环，配合 `break` 退出

```python
while True:
    x = input("输入 quit 退出: ")
    if x == "quit":
        break
```

- `if` 后面跟条件，`elif` 加额外条件，`else` 兜底

```python
score = 85
if score >= 90:
    print("A")
elif score >= 60:
    print("B")
else:
    print("C")
```

- `break` 只能在循环（`while`/`for`）里面用

```python
for i in range(10):
    if i == 5:
        break   # 到第5个就停
```

### 函数基础
- `def 函数名(参数):` 定义函数

```python
def add(a, b):
    return a + b
```

- 参数可以有默认值

```python
def greet(name, msg="你好"):
    print(f"{msg}，{name}")

greet("小明")           # 你好，小明
greet("小红", "早上好")  # 早上好，小红
```

- `return` 返回值，函数遇到 `return` 立刻结束

```python
def check(n):
    if n < 0:
        return "负数"    # 这里直接结束，后面的代码不跑
    return "非负数"

print(check(-5))  # 负数
```

### 输入输出
- `open("文件名", "w")` 写模式（覆盖），`"a"` 追加模式

```python
f = open("test.txt", "w")
f.write("hello")
f.close()
```

- `with open(...) as f:` 自动关闭文件，不用手动 `f.close()`

```python
with open("test.txt", "a") as f:
    f.write("第二行\n")
```

- `f.write(内容)` 写入，换行要手动加 `\n`

```python
f.write("第一行\n")
f.write("第二行\n")
```

- `f.read()` 读取全部内容

```python
with open("test.txt", "r") as f:
    content = f.read()
    print(content)
```

- `f-string`：把变量嵌入字符串

```python
name = "小明"
age = 17
print(f"{name}今年{age}岁")  # 小明今年17岁
```

---

## 出错的方面

### 1. 缩进（3次）
`if` 写在 `while` 里面要缩进4格，`def` 下面的代码也要缩进4格，`with` 下面的代码再缩进4格。最后一次练习已经全部改正，零错误。

```python
# ❌ 错误
def foo():
print("hello")    # 没缩进

# ✅ 正确
def foo():
    print("hello")   # 缩进4格
```

### 2. input() 返回的是字符串（2次）
`input()` 拿到的东西永远都是字符串。跟数字比较大小时要先 `int()` 转换，做加法也一样，否则 `"10" + "5"` 结果是 `"105"` 而不是 `15`。

```python
# ❌ 错误
age = input("年龄: ")
if age > 18:        # 字符串不能跟数字比

# ✅ 正确
age = int(input("年龄: "))
if age > 18:
```

### 3. 变量名写到一半换了（2次）
定义了叫 `target` 的变量，后面写成了 `truth`，Python 找不到。定义了参数 `msg`，却在函数里写死了字符串，没用参数。一个名字用到底，别中途换。

```python
# ❌ 错误
target = 42
if guess == truth:   # truth 是啥？没定义过

# ✅ 正确
target = 42
if guess == target:
```

### 4. 语法关键字记错了（2次）
Python 没有 `else if`，要写 `elif`。也不能把字符串当成运算符用，比如 `op = "+"` 然后写 `a op b`，Python 看不懂，要用 `if op == "+":` 分支判断。

```python
# ❌ 错误
else if x > 5:    # Python 不认 else if

# ✅ 正确
elif x > 5:

# ❌ 错误
a op b            # op 是字符串，不能当运算符

# ✅ 正确
if op == "+":
    result = a + b
```

### 5. 函数逻辑（5次）
- `break` 只能在 `while` 或 `for` 里面，不能写在循环外面
- `append()` 只是往列表加东西，返回值是 `None`，不需要 `return` 它
- 每个分支都有 `return` 会导致后面的代码永远跑不到
- `if a,b,op == "quit"` 不能一次比多个变量，要一个个比
- 题目要求循环但忘了写 `while True`

```python
# ❌ 错误：break 在循环外面
def foo():
    print("hello")
    break   # 没循环，break 往哪跳？

# ❌ 错误：return append()
def add_item(lst, x):
    return lst.append(x)   # 总是返回 None

# ✅ 正确
def add_item(lst, x):
    lst.append(x)   # 加进去就行，不用 return
```

### 6. 用了没学过的知识（1次）
用了 `try/except` 做错误处理，但这个阶段还没学。应该用学过的 `if` 加 `.isdigit()` 来判断输入是否有效。

```python
# ❌ 现阶段不要用
try:
    num = int(input("输入数字: "))
except ValueError:
    print("无效")

# ✅ 用学过的
x = input("输入数字: ")
if x.isdigit():
    num = int(x)
else:
    print("无效")
```

---

## 验收结果

最后一次练习（score_manager），五个之前的弱项全部清零：
- 缩进 → 全对
- 变量命名 → 一致
- input() 类型转换 → 正确
- elif 语法 → 正确
- 函数逻辑 → 正确

---

## 新学了两个东西

- `.isdigit()`：判断字符串是否纯数字

```python
"95".isdigit()    # True
"abc".isdigit()   # False
```

- `sum(列表)`：求列表里所有元素的和

```python
scores = [95, 87, 92]
print(sum(scores))  # 274
```

---

## 相关文件

- `D:\CC Switch\72e1.py` — mini_calc 练习
- `D:\CC Switch\72e2.py` — score_manager 练习
- `D:\CC Switch\contacts.py` — 通讯录项目（待继续）
