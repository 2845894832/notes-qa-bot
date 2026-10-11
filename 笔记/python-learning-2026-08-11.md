# Python 学习笔记 — 2026-08-11

## 新学：面向对象编程（上）

---

## 一、类与对象基础

### class / __init__ / self 三件套

```python
class Contact:
    def __init__(self, name, phone, level):
        self.name = name      # self.xxx = 参数 → 挂到实例上
        self.phone = phone
        self.level = level

    def introduce(self):
        return f"{self.name} | {self.phone} | {self.level}"

# 创建对象
c1 = Contact("小明", "13800138000", "VIP")
print(c1.name)              # . 访问，替代 ["name"]
print(c1.introduce())       # 调用方法
```

### 字典 vs 类

| | 字典写法 | 类写法 |
|------|----------|--------|
| 创建 | `{"name": "小明", ...}` | `Contact("小明", ...)` |
| 访问 | `p["name"]` | `p.name` |
| 操作 | 外部函数 | 自己的方法 |
| 数据+行为 | 分离 | **绑定在一起** |

### 易错点

- `__init__` 不是 `_init_`（双下划线，前后各两个）
- `self` 是第一个参数，调用时不用传（Python 自动处理）
- 方法里访问自己的属性必须用 `self.xxx`

---

## 二、实例属性 vs 类属性

```python
class Contact:
    total = 0          # 类属性——写在 class 下，所有对象共享

    def __init__(self, name, phone, level):
        self.name = name        # 实例属性——每个对象各有一份
        self.phone = phone
        self.level = level
        Contact.total += 1      # 用类名访问类属性
```

| | 实例属性 | 类属性 |
|------|----------|--------|
| 写法 | `self.xxx` | 直接写在 `class` 下 |
| 属于 | 每个对象 | 整个类 |
| 访问 | `obj.xxx` | `ClassName.xxx` |
| 用途 | 各不相同的值 | 共享的统计/配置 |

### 🐛 踩坑：`total += 1` → 报错

```python
# ❌ __init__ 里写
total += 1       # Python：total 是什么？没定义

# ✅ 必须加类名
Contact.total += 1
```

---

## 三、三种方法

```python
class Contact:
    # 实例方法——操作自己的数据
    def introduce(self):          # self = 当前对象
        return f"{self.name}"

    # 类方法——操作类属性 / 另一种创建方式
    @classmethod
    def from_string(cls, text):   # cls = Contact 类本身
        name, phone, level = text.split(",")
        return cls(name, phone, level)

    # 静态方法——纯工具函数，不碰 self 也不碰 cls
    @staticmethod
    def is_valid_phone(phone):
        return len(phone) == 11 and phone.isdigit()
```

| | 实例方法 | 类方法 | 静态方法 |
|------|---------|--------|---------|
| 装饰器 | 无 | `@classmethod` | `@staticmethod` |
| 第一个参数 | `self`（对象） | `cls`（类） | 无 |
| 调用 | `obj.method()` | `Class.method()` | `Class.method()` |

---

## 四、@dataclass — 偷懒神器

手写版：
```python
class Contact:
    def __init__(self, name, phone, level):
        self.name = name
        self.phone = phone
        self.level = level
```

dataclass 版（效果完全一样）：
```python
from dataclasses import dataclass

@dataclass
class Contact:
    name: str
    phone: str
    level: str
```

额外福利：自动生成 `__repr__`，打印对象不再是 `<object at 0x...>`，而是 `Contact(name='小明', ...)`。

---

## 五、ContactBook 组合模式

一个类管理一堆对象（"组合"）：

```python
class ContactBook:
    def __init__(self):
        self.contacts = []          # 装 Contact 对象

    def add(self, contact):
        self.contacts.append(contact)

    def show_all(self):
        for contact in self.contacts:
            print(contact.introduce())

    def find(self, name):
        for contact in self.contacts:
            if contact.name == name:
                return contact       # 找到了返回对象
        return None                  # 没找到返回 None
```

---

## 🐛 今天踩的坑

### 1. 测试代码塞进了 `__init__` 里
```python
# ❌ if __name__ == "__main__" 写在了 __init__ 里面
# 每次创建对象都执行测试 → 死循环 💥
```
**正确：** `if __name__ == "__main__":` 必须**顶格写**（0缩进），在所有 class/def 外面。

### 2. 类之间是并列的
```python
# ❌ 把 ContactSimple 写在 Contact 里面
class Contact:
    @dataclass
    class ContactSimple:   # 嵌套了
        ...

# ✅ 两个并列的类
class Contact:
    ...

@dataclass
class ContactSimple:
    ...
```

### 3. `total += 1` 没写类名
在方法里修改类属性必须 `ClassName.xxx`，否则当局部变量处理。

### 4. `is_valid_phone` 只检查了长度
```python
# ❌ 只检查长度，"abcdefghijk" 也能过
len(phone) == 11

# ✅ 同时检查长度和纯数字
len(phone) == 11 and phone.isdigit()
```

---

## 📊 进度更新

```
基础入门  ████████████████ 4/4 ✅
数据结构  ████████████████ 4/4 ✅
面向对象  ████████░░░░░░░░ 2/4 🟠（类与对象 ✅、类属性/方法 ✅）
```

**下一步：** 继承与多态（子类、super()、鸭子类型）
