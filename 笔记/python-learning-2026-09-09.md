# Python 学习总结 2026-09-09 —— 记账本 5 层逐层精讲

> 项目已跑通，今天不写新功能，而是把 5 层架构一层层重抠，把「能跑但没真正懂」的底层概念补牢。

## 今天学了什么
逐层精讲 service.py（第3层）→ cli.py（第4层）→ main.py（第5层）。models/storage 前两次已讲过。重点不是写代码，而是把卡壳的概念一个个解开。

## 核心知识点（这次新搞懂的）
1. `max(生成器)`：max 直接吃生成器表达式，不建中间列表；空列表要特判
2. `str.startswith()`：字符串前缀匹配，用它筛月份（日期 `"YYYY-MM-DD"` 前 7 位就是月份）
3. 返回类型注解 `-> dict` vs `-> list[Transaction]`：跟着「函数吐什么」走
4. dict 的 `.items()`：把字典拆成 `(键, 值)` 元组，sorted 排序要键值都拿到
5. **argparse 底层三连**：parser 是对象不是函数（要记住状态）；build_parser 造模板 / parse_args 填值；位置参数靠站位、可选参数靠点名
6. **对象 vs 工具**：两个角度不冲突。Python 里需要「记住状态」的都是对象
7. `str(date.today())`：date 对象 → `"YYYY-MM-DD"` 字符串
8. **None 对齐**：cli 和 service 用同一个 None 当「用户没指定」的信号，约定一致才能传值
9. main.py 的「读→改→存」：内存和文件两码事，改了内存必须 save 才落盘
10. dispatch（分发）= if/elif 按 command 分派执行

## 踩坑 / 卡点回顾
- 最卡的三个：parser 为什么是对象（不是工具）、位置参数 vs 可选参数、读改写为什么不能直接改文件
- 反复确认才通的：链式调用 `build_parser().parse_args()` = 先造模板再填值

## 下一步
5 层精讲全部完成。接下来二选一：回炉清待改练习（module_tools_review 6 题 / Lambda practice3 题3/5/8 / 属性管理 3 处），或换新知识点（pathlib / logging / random+statistics）。
