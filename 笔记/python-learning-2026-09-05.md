# Python 学习总结 2026-09-05 —— 类型注解

## 今天学了什么
工程实践领域开篇：**类型注解（Type Hints）**

## 核心知识点
1. **是什么**：给变量/函数贴「类型标签」，运行时**不强制**，只供人和工具（IDE / mypy）用
2. **变量注解**：`name: str = "小明"`
3. **函数注解**：`def add(a: int, b: int) -> int:`
   - 关键：箭头 `->` 在括号后、冒号前，**冒号永远最后**
4. **容器泛型**：`list[int]` / `dict[str, int]` / `tuple[int, str]` / `set[str]`
5. **Optional / Union**：`int | None`、`int | str`（旧写法 `Optional[X]`、`Union[X, Y]`）
6. **Any**：任意类型；**类型别名**：`UserId = int`

## 踩坑记录（都是跑出来的）
- 箭头位置：`): ->int` ❌ → `) -> int:` ✅
- 方括号装类型：`list(float)` ❌ → `list[float]` ✅（又是括号混淆）
- `max(dict, key=...)` 返回的是**键**（名字 str），不是值（分数 int）
- `split` 要作用在**每一项**上，不是整个列表；结果要**解包接住**：`name, score = item.split(":")`
- 变量 vs 字符串字面量：`name`（盒子，装的是 "小明"）≠ `"name"`（字面量本身）
- 空行判断：`if not i:`（空字符串是假值），不是 `i == " "`
- return 拼写：`result` 不是 `reult`

## 练习文件
`type_hints_practice.py`（5 题通关，含综合题 `process_students`）
`unittest_practice.py`（11 测试全过）

## 单元测试（同日续学）
1. 核心思想：把「验证」写成代码，改代码后一键回归
2. 结构三铁律：继承 `TestCase`、方法名 `test_` 开头、`unittest.main()`
3. 断言：`assertEqual` / `assertTrue` / `assertIsNone` / `assertIn` / `assertRaises`
4. 测异常：`with self.assertRaises(ValueError):` 块里放会抛异常的调用
5. `__name__ == "__main__"`：区分「直接运行」vs「被 import」
6. 读结果：`.`=通过、`E`=ERROR(测试代码错)、`F`=FAIL(断言不成立)
踩坑：`text` vs `test` 拼写、同名方法互相覆盖、`average[..]` 方括号调函数（第二次犯）、期望值写错

## 下一步
工程实践还剩：**PEP8 / 调试**（待学）
