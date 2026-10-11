# Python 学习笔记 — 2026-06-24

## 📊 当前进度：8/28 概念

基础入门 (4/4 ✅) | 数据结构 (4/4 ✅) | 面向对象 (0/4)

---

## 🧠 今日大事：确立学习方法论

**行动 → 反思 → 理论 → 应用** 四步循环

- 每关一个小任务，先做后讲
- 以练促学，目标拆解，干完复盘
- 不再先灌理论再写代码

---

## 🏗️ 通讯录管理系统

### 第1关：`add_contact()` ✅

```python
def add_contact(name, phone, level):
    person = {"name": name, "phone": phone, "level": level}
    contacts.append(person)
    print(f"[OK] {name} 已添加到通讯录")
```

**踩坑记录：**
- `append()` 只能接受一个参数 → 先拼字典再 append
- `def` 行要加冒号 `:`
- Python 靠缩进识别代码块归属
- Windows 终端 GBK 不支持 emoji（✅ → `[OK]`）
- `contacts = []` 不是 `contacts()`

### 第2关：`show_contacts()` ✅

```python
def show_contacts():
    if len(contacts) == 0:
        print("[INFO] 通讯录为空")
    else:
        print(f"[通讯录] 共 {len(contacts)} 人:")
        for i, p in enumerate(contacts, 1):
            print(f"  {i}. {p['name']} | {p['phone']} | {p['level']}")
```

**进步：缩进一次过！** 已经内化了缩进规则。

### 待完成
- `delete_contact(name)` — 按名字删联系人
- `find_contact(name)` — 按名字查找
- 统计功能（各等级人数）

---

## 📺 今天看的视频

1. **埃隆·马斯克给学生的终极建议**
   - 做一个有用的人
   - 第一性原理思考（回到基本事实推理）
   - 大量阅读
   - 失败是可以的

2. **一个人最顶级的能力：高效学习**
   - 费曼学习法：用最简单的话讲给别人听
   - 烧水思维：持续加热不中断
   - 进步本：记录进步了什么，不是学了什么

---

## 🔑 今日要点

1. `enumerate(iter, start)` — 遍历 + 带序号，第二个参数控制起始数字
2. 缩进规则 — `def/if/for/while` 后面的代码块要缩进4格
3. 学习方法论 — 行动→反思→理论→应用，不是学了→练了→忘了
4. 通讯录进度 — 2/5 功能完成

---

文件：`D:\CC Switch\contacts.py`
