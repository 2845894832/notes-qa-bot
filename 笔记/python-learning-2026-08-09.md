# Python 学习笔记 — 2026-08-09

## 快速复习

今天先快速过了一遍之前学过的所有内容：
- 变量与类型（int/float/str/bool、类型转换）
- 控制流（if/elif/else、for、while True + break）
- 函数（def、return vs print、默认参数、docstring）
- 文件读写（with open、read/write、f-string）
- 四大数据结构（列表、字典、元组、集合）
- enumerate 用法

复习效果：已学内容基本记住，手感还在。

---

## 新学

### f-string 详解

**为什么用 f-string：**
```python
name = "小明"
age = 17

# ❌ + 拼接（麻烦，要手动转类型）
print("我叫" + name + "，今年" + str(age) + "岁")

# ✅ f-string（干净直观）
print(f"我叫{name}，今年{age}岁")
```

**{} 里不只是放变量，还能执行表达式：**
```python
a, b = 10, 3
print(f"和：{a + b}")              # 运算 → 13
print(f"名字长度：{len('小明')}")   # 调函数 → 2
print(f"大写：{'hello'.upper()}")   # 调方法 → HELLO
```

**控制小数位数：**
```python
pi = 3.1415926
print(f"圆周率：{pi:.2f}")    # → 3.14（保留2位，自动四舍五入）
print(f"圆周率：{pi:.0f}")    # → 3（取整）
```

语法：`{变量:.Nf}`，N = 保留几位小数。

**对齐和填充：**
```python
print(f"|{name:<10}|")    # 左对齐，占10格 → |小明        |
print(f"|{name:>10}|")    # 右对齐，占10格 → |        小明|
print(f"|{name:^10}|")    # 居中，占10格   → |    小明    |
print(f"|{name:*^10}|")   # 居中，*填满   → |****小明****|
```

**千位分隔符、百分号：**
```python
money = 1000000
print(f"余额：¥{money:,}")  # → ¥1,000,000
```

### 容易踩的坑

```python
# ❌ 忘了 f，{} 不会被替换
print("你好，{name}")      # 输出 → 你好，{name}

# ✅ 要有 f
print(f"你好，{name}")     # 输出 → 你好，小明
```

---

## 综合练习：通讯录系统（3/5 → 5/5 完成）

**文件：** `D:\CC Switch\contacts.py`  
**状态：** 全部5个功能完成

### 功能1：添加联系人 ✅（之前完成）
```python
def add_contact(name, phone, level):
    person = {"name": name, "phone": phone, "level": level}
    contacts.append(person)
    print(f"[OK] {name} 已添加到通讯录")
```

### 功能2：显示通讯录 ✅（之前完成）
```python
def show_contacts():
    ...
    for i, p in enumerate(contacts, 1):
        print(f"  {i}. {p['name']} | {p['phone']} | {p['level']}")
```

### 功能3：删除联系人 ✅（今天完成）

**核心技能**：`for i, p in enumerate(contacts)` 同时拿到索引和联系人字典。

```python
def delete_contact(name):
    for i, p in enumerate(contacts):   # i=索引, p=联系人字典
        if p['name'] == name:          # 用键 'name' 取值比较
            contacts.pop(i)            # 按索引删除
            print(f"[OK] {name} 已删除")
            return                     # 找到就结束函数
    print(f"[INFO] 未找到 {name}")     # 跑完还没找到
```

**遍历字典值，用 `p['name']` 而不是 `p[name]` 或 `p.name`。**
字典取值用方括号+字符串键名：`p['name']` ✅

### 功能4：查找联系人 ✅（今天完成）

```python
def find_contact(name):
    for i, p in enumerate(contacts):
        if p['name'] == name:
            print(f"[INFO] 找到联系人: {p['name']} | {p['phone']} | {p['level']}")
            return
    print(f"[INFO] 未找到 {name}")
```

和删除的结构一样：遍历 → 匹配 → 找到就 return → 循环结束才说"未找到"。

### 功能5：统计功能 ✅（今天完成）

```python
def show_stats():
    people_count = len(contacts)
    vip_count = 0
    normal_count = 0
    guest_count = 0
    phone_prefixes = set()   # 空集合，准备接号段

    for p in contacts:
        # 等级统计
        if p['level'] == "VIP":
            vip_count += 1
        elif p['level'] == "NORMAL":
            normal_count += 1
        elif p['level'] == "GUEST":
            guest_count += 1

        # 号段去重——取前3位塞进集合
        phone_prefixes.add(p['phone'][:3])

    print(f"[统计] 总人数: {people_count}")
    print(f"VIP: {vip_count}人")
    print(f"NORMAL: {normal_count}人")
    print(f"GUEST: {guest_count}人")
    print(f"涉及号段: {phone_prefixes}")
```

**涉及知识点**：
- `set()` 创建空集合，`.add()` 添加元素，自动去重
- `p['phone'][:3]` 字符串切片，取前3个字符（手机号段）
- 累加器（`count += 1`）统计各等级人数

---

## 🐛 今天踩的坑

### 1. `for i in contacts` 后 `i` 是字典不是索引
```python
# ❌ 以为 i 是数字
for i in contacts:
    contacts[i]  # i 是字典，不能当索引用

# ✅ 用 enumerate 同时拿索引和元素
for i, p in enumerate(contacts):
    p['name']    # p 是字典，i 是数字索引
```

### 2. 集合没创建就使用
```python
# ❌ phone 没定义
phone.add("138")

# ✅ 先创建空集合
phone_prefixes = set()
phone_prefixes.add("138")
```

### 3. f-string 里 {} 外面的代码不执行
```python
# ❌ p['phone'][:3] 没在 {} 里，原样输出
print(f"p['phone'][:3]")    # → p['phone'][:3]（字面文本）

# ✅ 放 {} 里才会执行
print(f"{p['phone'][:3]}")  # → 138
```

### 4. Python 注释用 `#` 不是 `//`
```python
// 这是注释    ❌  // 是 C/Java 的注释
# 这是注释     ✅  Python 用 #
```

### 5. `delete_contact` 初版为什么跑不对
```python
def delete_contact(name):
    name = input("请输入名字：")   # ⚠️ 覆盖了参数
    for i in contacts:            # ⚠️ i 是字典
        i = 0                     # ⚠️ 每轮重置
        if name == contacts[i]:   # ⚠️ 字典和字符串比
            contacts.remove(i)    # ⚠️ remove 按值删
```

总结：`enumerate` + 字典键取值 + `pop(索引)` 是正确路线。

---

## 🧠 核心模式：查找-删除-统计

今天三个功能共享同一个结构：

```
遍历 → 匹配条件 → 做操作 → return
                         ↓
                   循环结束后处理"找不到"的情况
```

| 功能 | 找到了 | 没找到 |
|------|--------|--------|
| 删除 | pop(i)、return | 循环结束，print "未找到" |
| 查找 | print 信息、return | 循环结束，print "未找到" |
| 统计 | 累加器+1、集合.add | 不需要特殊处理 |

---

## 🎯 下一步

通讯录项目全部完成！下一站：**面向对象编程**
- `class` / `self` / 实例属性与方法
