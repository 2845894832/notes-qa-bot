# Python 学习总结 2026-09-07 —— PEP8 + Black + 调试

> 工程实践四件套收官：类型注解 ✅、单元测试 ✅（9/5）→ PEP8 ✅、调试 ✅（9/7）

## 一、PEP8 规范 + Black 工具

### 1. PEP8 命名规范（最重要）
| 东西 | 规则 | 例子 |
|------|------|------|
| 变量/函数/参数 | 全小写 + 下划线（snake_case） | `score_list`、`get_score`、`calculate_average` |
| 类 | 大驼峰（CapWords） | `Student`、`InvalidScoreError` |
| 常量 | 全大写 + 下划线 | `MAX_SCORE` |

**关键：下划线是「分隔符」不是「装饰」，它把两个单词隔开，每个单词保持自己的大小写。**
- 下划线后面**不接大写**：`score_List` ❌ → `score_list` ✅
- 常量多词也要下划线：`MAXSCORE` ❌ → `MAX_SCORE` ✅

### 2. 空格
- 运算符两边空格：`total = total + s`、`__name__ == "__main__"`
- 逗号后空格：`[80, 90, 100]`、`Student("小明", 95)`
- 函数名和 `(` 之间**不能**空格：`def f(...)` 不是 `def f (...)`

### 3. Black 自动格式化
- **安装**：`pip install black`（⚠️ 清华镜像装不上报 "from versions: none"，换官方源 `-i https://pypi.org/simple`）
- **使用**：`python -m black 文件.py`；`--check` 只检查不改、`--diff` 预览
- **边界（重要）**：Black **只改格式，不改命名**，`Get_score` 不会变 `get_score`

### 4. 环境配置（同日）
- 把 Python314-32 和 Scripts 目录加入**用户 PATH**（排在 WindowsApps 之前，解决「假 python 弹商店」问题）
- 新终端后 `python` / `black` 短命令直接可用

## 二、调试

### 1. 核心思路
| 情况 | 特征 | 手段 |
|------|------|------|
| 报错崩溃 | 有 traceback | 读 traceback 定位 |
| 不报错但结果错 | 能跑完但答案不对 | print 中间值 |

### 2. traceback 读法
- **从下往上读**；最后一行 = 错误类型 + 一句话原因；往上找自己代码的 `File ... line N`
- `in <module>` = 顶层代码（不属于任何函数）；`in 函数名` = 在函数里出错
- 报错里的 `~~~~~~~^^^^^` 波浪线 = Python 直接标出问题位置

### 3. 常见错误类型速查
| 错误 | 含义 |
|------|------|
| `NameError` | 名字没定义（拼错、没赋值就用） |
| `TypeError` | 类型错（方括号调函数、list 当函数调用） |
| `ValueError` | 值不合适（`int("abc")`） |
| `IndexError` | 索引越界（列表只有 0~n-1） |
| `KeyError` | 键不存在 |
| `IndentationError` | 缩进错 |
| `AttributeError` | 属性/方法不存在 |

### 4. print 调试
- 在可疑处 `print` 中间值，看它每一步怎么变

### 5. breakpoint() / pdb
- `breakpoint()` 停在那一行；`p 变量`看值、`n`下一行、`c`继续、`q`退出

## 踩坑记录（都是跑出来的）
- 取消注释时**别留行首空格**，否则顶层代码会报 `IndentationError`
- 一题可能藏两个错：先修缩进，再修逻辑（第 3 题）
- `NameError` 本质 = 用了一个从未定义过的名字
- 清华镜像 `from versions: none` → 换官方源
- black 格式化后命名不会变，命名靠人

## 三、标准库 × 工程实践 综合练习（两套）

→ 已单独成笔记，见 [`stdlib-engineering-practice.md`](stdlib-engineering-practice.md)

## 练习文件
- `pep8_practice.py`（脏代码 → 规范版）
- `debug_practice.py`（5 个埋 bug 小题）
- `stdlib_engineering_practice.py`（6 题，测试全绿）
- `stdlib_engineering_practice2.py`（6 题，测试全绿）

## 下一步
工程实践四件套已齐 + 标准库×工程实践综合两套练熟。下一步：回炉待改练习 或 综合项目实战
