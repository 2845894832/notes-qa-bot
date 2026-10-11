# Python 学习总结 — 2026-08-12

## 今日主题：继承与多态 + 魔术方法（OOP 收官）

---

## 一、继承与多态（RPG 角色系统）

### 学了什么

用 `Character` 父类 + 三个子类（战士/法师/弓箭手）练透继承、方法重写、多态、鸭子类型：

| 概念 | 代码 | 一句话 |
|------|------|--------|
| 继承 | `class Warrior(Character)` | 子类继承父类的属性和方法 |
| super() | `super().__init__(name, hp=150, attack=20)` | 调用父类的 `__init__` |
| 方法重写 | 子类重写 `special_skill` | 同名方法，子类自定义行为 |
| 多态 | `for hero in party: hero.special_skill(enemy)` | 同一调用，不同类不同表现 |
| 鸭子类型 | `Sword`/`Staff`/`Bow` 只要有 `use_bonus` | 不看类型，只看有没有方法 |

### 关键收获

- `super().__init__(...)` 让子类复用父类的初始化逻辑，只传自己不同的参数
- 父类先定义好框架（`special_skill` 默认就是普通攻击），子类按需重写
- 多态的精髓：`party` 列表里放的是不同子类对象，却都用同一个 `hero.special_skill()` 调用，各自干各自的事
- 鸭子类型：装备类（`Sword`/`Staff`/`Bow`）不继承任何"装备基类"，只要实现了 `use_bonus(self)` 就能被 `attack_target` 使用——"走起来像鸭子、叫起来像鸭子，那就是鸭子"

### 踩坑

- 子类重写方法后，如果还想复用父类的实现，用 `super().方法名()`，不要复制粘贴父类代码
- `self.__class__.__name__` 能拿到"当前对象真实属于哪个类"的名字（配合多态打印用）

---

## 二、魔术方法（Magic Methods / Dunder Methods）

### 学了什么

5 个最常用的魔术方法，让自定义类像 Python 内置类型一样自然：

| 魔术方法 | 触发方式 | 作用 | 一句话 |
|---------|---------|------|--------|
| `__str__` | `print(obj)`, `str(obj)` | 给人看的，友好可读 | print() 给人看 |
| `__repr__` | `repr(obj)`, 列表/字典中 | 给开发者看的，精确无歧义 | 调试用，争取能复制重建 |
| `__eq__` | `obj == other` | 自定义"相等"的逻辑 | 什么算相等？ |
| `__len__` | `len(obj)` | 让对象有"长度" | 你的对象有多长？ |
| `__getitem__` | `obj[0]`, `obj["key"]` | 支持 `[]` 索引 | [] 访问，送 for 循环 |

### 关键收获

- `__repr__` vs `__str__`：对象在列表里会用 `__repr__`，不是 `__str__`
- `__eq__` 要先用 `isinstance` 检查类型，不对返回 `NotImplemented`（不是抛异常）
- 有 `__len__` 后 `bool(obj)` 自动生效（空→False）
- 有 `__getitem__` 后 for 循环和 `in` 操作符自动支持，切片也能用
- `!r` 在 f-string 中让字符串带上引号：`{self.name!r}`

### 踩坑

- Windows 终端 GBK 编码下 emoji（如 ✅）会报 `UnicodeEncodeError`，用纯文本替代

### 练习文件

- `inheritance_practice.py` — RPG 角色系统（继承/多态/鸭子类型）
- `magic_methods_practice.py` — 6 个练习，全部通过

### 进度

- OOP 四大模块全部完成 ✅
- 下一站：待定（文件操作进阶 / 异常处理 / 迭代器生成器 / 装饰器 等）
