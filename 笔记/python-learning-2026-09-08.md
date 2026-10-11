# Python 学习总结 2026-09-08 —— 第三套 + 记账本项目实战

> 一天两个主题：上午标准库×工程实践第三套（自己补全函数体），下午把它升级成真正的多模块项目——命令行记账本。

## 一、标准库×工程实践 第三套（自己补全）

### 今天学了什么
标准库 × 工程实践综合练习**第三套**，6 题 + 3 个测试，全绿。重点不是做题本身，而是弄清了几个之前「会抄但没懂」的概念。

### 核心知识点（这次新搞懂的）
1. **json.load 不用 dict() 包**：`json.load(f)` 本身返回原生类型（对象→dict、数组→list），`dict()` 多余；有 `s` 操作字符串、没 `s` 操作文件
2. **sorted() 为什么要用**：`os.listdir()` 顺序不确定，要稳定排序就用 `sorted()`，它能吃生成器
3. **namedtuple 字段访问**：用点号 `e.name`/`e.department`，比元组下标 `e[0]` 好读
4. **unittest 里的 self**：当前测试类实例，assertEqual 等继承方法靠 `self.` 调
5. **csv.DictReader(f)**：接收文件对象，`list()` 直接收成列表

### 踩坑（第三套跑出来的）
- `text.split` 少括号 → TypeError；`appendEmployee` → `append`；strptime `%Y%M%D` → `%Y-%m-%d`
- 函数忘 return → None；目录不存在忘 `return []`；漏 `os.path.join`
- 测试期望值类型错（拿 list 和 dict 比）
- 终端中文乱码是 GBK 编码，不是代码问题

## 二、项目实战：命令行记账本（expense_tracker）

→ 已单独成笔记，见 [`expense-tracker-project.md`](expense-tracker-project.md)

一句话：CLI 记账本（add/list/stats/delete），5 层架构（models/storage/service/cli/main）+ 3 里程碑 + unittest，端到端跑通、测试全绿。新学 argparse，搞懂了 @dataclass / self / __eq__ / 对象↔dict 互转 / JSON 只认通用类型。

## 下一步
项目实战打通了「分层 + 流水线」骨架。接下来：回炉清掉待改练习（module_tools_review 6 题、Lambda practice3 题3/5/8、属性管理 3 处），或换知识点继续（`pathlib` / `logging` / `random`+`statistics`）。
