# Python 学习总结 2026-09-10 —— 健身记录本（记账本同架构换域题）

> 出题思路：照搬记账本的 5 层架构，但换了域名（健身记录）和参数结构，防止照抄。14 个 TODO，验收靠 15 个单元测试。

## 结果
- **15/15 单元测试全绿**（test_storage 4 个 + test_service 11 个）
- CLI 端到端跑通：add / list / stats / delete / list --kind 全部正常，JSON 落盘中文可读
- 14 个 TODO 全部完成
- ⏳ bonus.py 加练 3 题（defaultdict / sorted / strptime+isocalendar）还没写

## 本次新学 / 复习的概念（用户主动提问的 6 个）
1. **`list.copy()` vs `records.copy()`** —— `list` 是类型本身，`list.copy` 是未绑定方法，缺 self 会 TypeError。要「让某个具体列表复印自己」必须 `records.copy()`
2. **`month=month`（关键字传参）** —— 左边的 `month=` 是形参名，右边的 `month` 是局部变量，同名纯属巧合。**必须写**，因为 `list_workouts(records, kind=None, month=None)` 里位置传参会让值落到 `kind` 上 → 静默错误（不报错但结果全错）
3. **`defaultdict(float)`** —— 第一个参数叫 `default_factory`，传的是**类本身**（不加括号），访问不存在的键时自动 `float()` → 0.0。等价于 `defaultdict(lambda: 0.0)`。int→0、list→[]、str→""
4. **`add_subparsers` / `add_parser` / `add_argument` 三层嵌套**
   - `add_subparsers()` 在主 parser 上调，1 次，返回「子命令容器」
   - `add_parser("add")` 在容器上调，每个子命令 1 次，**返回一个新的 ArgumentParser**（赋值必须）
   - `add_argument(...)` 在具体 parser 上调，**返回 None**（千万别赋值，会把 parser 覆盖成 None）
5. **`s['total_minutes']`** —— 就是 dict 用键取值，无特殊语法。f-string 里注意引号嵌套：外双内单 `f"{s['k']}"`；同名引号在 3.12 前会提前闭合
6. **`#{args.id}`** —— `#` 是普通字符原样输出（编号样式），`{args.id}` 是 f-string 占位符 + 点号取属性。**f-string 里 `#` 不是注释**

## 踩坑记录（本轮改了 4 次才全绿）
### 第 1 轮：语法错 + 语义错
- **中文全角逗号 `，` 混进代码** → `SyntaxError: invalid character '，' (U+FF0C)`。中文环境下头号坑，`,` `。` `：` `；` `！` `？` `（）` 七个全角符号在代码里都非法
- `defaultdict( ,float)` 多写一个逗号，第一个参数位置空了
- `except FileExistsError` 应为 `FileNotFoundError` —— **一字之差，语义完全不同**：前者是「写文件时目标已存在」，后者是「读文件时文件不在」
- `json.dump` 漏了 `indent=4`
- `sub.add_argument(...)` 三连错：对象错（`sub` 该是 `p_add`）、多写了 `=`（返回 None）、`argumemt` 拼写错
- `return list.copy()` 应为 `records.copy()`

### 第 2 轮：拼写 + 改多了
- 同一个词在三个地方三种拼法：`exercice`（多一个 c）/ `exerice`（少一个 c）/ 正确是 `exercise`（e-x-e-r-c-i-s-e，中间只有一个 c）
- **修 stats 时把 `by_kind` 的定义和累加循环整个删掉了**（改 79/84 行时删多了）
- 关键区分：`by_kind` 累加 **minutes**（时长），`by_exercise` 累加 **calories**（卡路里），两个 defaultdict 口径不同

### 第 3 轮：改漏 + 又改多了
- `models.py` 里的 `exercice` 漏改，导致「类里存 exercice，代码里用 exercise」对不上
- **删返回值时删错了键**：该删的是中间变量 `by_exercise`，结果把要求的 `by_kind` 也删了。判据 = docstring 列了几项（total_minutes / total_calories / by_kind / top，四项一个不多一个不少）

### 第 4 轮：全绿

## 两个可复用的教训
1. **Python 的 `Did you mean: 'xxx'?` 提示会把你带沟里** —— 它只是在你的类里找最接近的属性名。如果类里存的也是错的，它建议的也是错的（两次报错分别推荐了 `exercice` 和 `exercise`，都不可信）
2. **重命名别手打，用全局替换**（VS Code 选中变量按 `Ctrl+Shift+L`）。手打必然漏改或打出新错别字；**改完立刻跑测试**，别攒着——`，` 和 `defaultdict( ,float)` 这类错跑一次就现形

## 附带发现
- **Windows GBK 控制台打 emoji 会崩**：`print("✅")` 抛 `UnicodeEncodeError: 'gbk' codec can't encode character '✅'`。中文本身没问题（GBK 里有），崩的是 GBK 字符集里没有的符号。写自检脚本时用纯中文提示
- 我这条 bash 管道显示中文会是乱码（编码问题），加 `export PYTHONIOENCODING=utf-8` 就能正常显示，**文件本身和程序输出都没问题**

## 待办
- ⏳ `fitness_tracker/bonus.py` 加练 3 题：
  - A. `top_exercises(records, n=3)` —— defaultdict + sorted + 切片，返回卡路里前 n 的动作名
  - B. `monthly_trend(records)` —— 字符串切片 `w.date[:7]` + sorted，返回 `[(月份, 总卡路里)]` 升序
  - C. `group_by_week(records)` —— `datetime.strptime` + `isocalendar()`，返回 `{"2026-W36": 总分钟数}`（最陌生的一题）
- ⏳ `main.py` list 分支输出空格微调（4 处：拼接少空格 / 双空格 ×2 / 行尾空格）
- 跑一次 `black fitness_tracker` 统一格式（service.py:82 缩进是 5 个空格）
