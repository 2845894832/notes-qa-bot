# Python 学习总结 — 2026-09-02

## 今日主题：Lambda 与高阶函数（函数进阶 · 第 3 课）

> 状态：概念已讲完，练习**进行中**（8 题，还有 4 题待改对）

---

## 一、Lambda 匿名函数

### 学了什么

| 概念 | 代码 | 一句话 |
|------|------|--------|
| lambda | `lambda 参数: 表达式` | 一次性、没名字的小函数 |
| 等价关系 | `add = lambda x, y: x + y` | 等价于 `def add(x,y): return x+y` |

### 关键收获

- lambda **只能写一个表达式**，不能写多行、不能有 if 块
- 语法固定：`lambda 参数: 返回值`，**冒号别写成逗号**
- 最适合的场景：`sorted(key=...)`、`map`、`filter` 里的一次性小逻辑

---

## 二、高阶函数（把函数当数据用）

### 三大件

| 函数 | 作用 | 返回 | 注意 |
|------|------|------|------|
| `map(func, 序列)` | 对每个元素应用 func | 迭代器 | 要套 `list()` |
| `filter(func, 序列)` | 留下 func 返回 True 的 | 迭代器 | 要套 `list()` |
| `reduce(func, 序列)` | 累积成一个值 | 单个值 | 从 `functools` 导入，**不套 list()** |

```python
list(map(lambda x: x**2, [1,2,3]))        # [1,4,9]
list(filter(lambda x: x > 0, [1,-2,3]))   # [1,3]
reduce(lambda a, b: a + b, [1,2,3,4])     # 10
```

### `sorted` 的 key（最常用的 lambda 场景）

```python
sorted(students, key=lambda s: s["score"], reverse=True)  # 字典列表按 score 降序
```

### `functools.partial`（固定部分参数）

```python
from functools import partial
square = partial(power, exp=2)   # 固定 exp=2
square(5)                         # 25
```

---

## 三、⚠️ 踩坑大全（今天暴露的，重点复习）

### 1. `%` 取余 vs `/` 除法（⚠️ 连续犯两次，最高优先级）

```python
10 / 3    # 3.333...  除法，得到商
10 % 3    # 1         取余，得到余数
```

- 能被 3 整除 → `x % 3 == 0`（不是 `x / 3 == 0`，那永远 False）
- 偶数 → `x % 2 == 0`
- 奇数 → `x % 2 == 1`（或 `x % 2 != 0`）

**记法**：`%` 念"取余"，脑子里默念"x 除以 2 的**余数**是不是 0"。

### 2. reduce 的 lambda 要返回"值"，不是"布尔"

```python
# ❌ 最大值写成 x > y，返回的是 True/False
maximum = reduce(lambda x, y: x > y, data)
# ✅ 要返回"较大的那个数"
maximum = reduce(lambda x, y: x if x > y else y, data)
```

- 求和用 `x + y`，乘积用 `x * y`（别搞混）

### 3. partial 的位置参数 vs 关键字参数冲突（新知识点）

```python
def connect(host, port, timeout=10): ...

# ❌ 用关键字固定了第一个参数 host，再 local(8080) 会报错：
#    TypeError: connect() got multiple values for argument 'host'
local = partial(connect, host="localhost")
local(8080)   # 8080 想填第一个空位 host，但 host 已被关键字占了

# ✅ 解法1：用「位置参数」固定 host（8080 自动落到 port）
local = partial(connect, "localhost")

# ✅ 解法2：调用时 port 也用关键字
local = partial(connect, host="localhost")
local(port=8080)
```

**规则**：partial 用关键字固定了某个参数，后面再传位置参数时，位置参数按顺序填到"还没被占用的位置"；固定的是第一个参数就会撞车。

### 4. 变量名张冠李戴（编程大忌）

```python
minimum = reduce(..., nums)   # ❌ 应该用 data，写了 nums（碰巧结果对，换数据就翻车）
raw = reduce(...)             # ❌ 结果塞回 raw，把原始数据覆盖了
by_name 没赋值 / 赋值写成了 by_age   # ❌ print(by_name) 出来是 None
```

**规则**：一个变量只干一件事；赋值号左边必须和你想存的一致；别让"结果变量"和"原始数据变量"重名。

### 5. map/filter 要套 list()，reduce 不用

- `list(map(...))` ✅、`list(filter(...))` ✅
- `list(reduce(...))` ❌（reduce 结果是数字，不用 list）
- `map(lambda x: int(x))` ❌（少了 map 的第二个参数——序列）

---

## 练习文件

- `lambda_hof_practice.py` — 8 题，**进行中**（题 2 华氏度、题 3 正数、题 1 已对；题 2 立方、3 偶数、4、5、6、7、8 待改）
- `lambda_hof_review.py` — 6 题易错点专项，**进行中**（题 2 平方/立方、题 3 拼接、题 5 思路对；题 1、3 最小值、4、6 待改）

## 进度

- 函数进阶：作用域与闭包 ✅、装饰器 ✅、Lambda 与高阶函数 ✅（概念+踩坑已掌握；练习题未全部改对，暂跳过，可回炉）

---

## 四、模块与导入系统（模块与工具 · 第 1 课）

> 状态：✅ 完成（8 题一次全对 + `__name__` 实验验证）

### 学了什么

| 概念 | 代码 | 一句话 |
|------|------|--------|
| import 模块 | `import myutils` → `myutils.add()` | 带命名空间，拿到整个模块 |
| from 模块 import 名字 | `from myutils import greet` → `greet()` | 不带前缀，单独抓出来 |
| import as 别名 | `import myutils as mu` | 给模块起别名 |
| from import as | `from myutils import PI as p` | 给名字起别名 |
| 包 | 含 `__init__.py` 的文件夹 | 文件夹版的模块 |
| `__all__` | `__all__ = ["calc"]` | 控制 `import *` 的"限购清单" |
| `__name__` | `if __name__ == "__main__":` | 区分"主角 / 配角" |

### 核心理解（为什么）

1. **import 的本质 = 把别的文件里的名字搬进当前文件**
   - `import 模块` = 搬进"整个盒子"，用 `模块.名字` 访问
   - `from 模块 import 名字` = 单独抓出来，直接 `名字`
   - 两种方式并存是为了**防重名打架**：`A.add` / `B.add` 不会互相覆盖
2. **`__name__` 的机制**：直接运行 = `"__main__"`（主角）；被 import = 文件名（配角）
   - `if __name__ == "__main__":` 翻译成"只有当我是主角（被直接运行）时才执行"
   - 用途：文件末尾写测试代码，别人 import 时不触发
3. **包 = 文件夹 + `__init__.py` 标签**；`__all__` 是 `from 包 import *` 的限购清单（没写 `__all__` 则默认导入所有非下划线开头名字）

### 口诀

- `import 模块` → 带门牌；`from 模块 import 名字` → 不带门牌
- `__main__` = 我是主角才演

### 练习

- `module_practice/` 多文件协作（4 个文件）：`main.py` 8 题**一次全对** ✅
- `__name__` 对比实验：`python main.py` 不打印 myutils 那句；`python myutils.py` 打印 ✅

### 踩坑 / 注意

- 题 2 `greet("xiaoming")` 传了拼音，期望是中文 `"小明"`
- `myutils.py` 的 print 用了拼音（逻辑对，建议中文）
- `__init__.py` 里 `__all__ = None` 占位行没删，被下面 `__all__ = ["calc"]` 覆盖（结果对，但冗余）

## 进度

- 模块与导入系统 ✅（模块与工具 1/3）
- 下一站：虚拟环境与包管理（venv / pip / requirements.txt）

---

## 五、虚拟环境与包管理（模块与工具 · 第 2 课）

> 状态：✅ 完成（全程实操跑通，含一个意外发现）

### 学了什么

| 概念 | 命令 | 一句话 |
|------|------|--------|
| pip 装包 | `pip install 包名` | 装第三方库 |
| venv 创建 | `python -m venv myenv` | 每个项目一个独立环境 |
| 隔离开关 | `include-system-site-packages = false` | venv 看不到全局包 |
| 激活/退出 | `source Scripts/activate` / `deactivate` | 临时把 venv 塞进 PATH |
| 导出依赖 | `pip freeze > requirements.txt` | 生成包清单 |
| 还原依赖 | `pip install -r requirements.txt` | 一键还原环境 |
| 换镜像 | `-i https://mirrors.aliyun.com/pypi/simple/` | 国内加速 |

### 核心理解（为什么）

1. **为什么需要 venv**：全局只有一个 Python，所有项目的包堆一起 → 版本冲突；venv = 每个项目一个独立小仓库
2. **venv 本质** = 复制一份 Python + 独立包目录（`Lib/site-packages`）；"激活"只是临时把 venv 的 `Scripts` 塞进 PATH 最前面
3. **`include-system-site-packages = false`** 是隔离的核心开关（改 true 就能看到全局包）
4. **pip 自动解析依赖**：装 requests 一个，自动带 urllib3 / idna / certifi / charset_normalizer 四个

### ⚠️ 意外发现：WindowsApps 的假 python 存根

- PATH 里的 `python` 指向 `...\Microsoft\WindowsApps\python`（Windows 商店存根，不是真 Python）
- 真 Python 在 `...\Programs\Python\Python314-32\`，但没加 PATH
- 所以 `python`/`pip` 命令一直不能用（`command not found` / `Exit 49`），要用完整路径
- 激活 venv 后 `python` 命令能用了（venv 的 Scripts 进了 PATH 最前面）
- 想彻底修：把真 Python 目录加进 PATH，且排在 WindowsApps **前面**

### 踩坑 / 经验

- 清华镜像报 `from versions: none` → 换阿里云镜像（32 位平台 wheel 索引不全）
- 32 位平台：wheel 命名是 `cp314-cp314-win32`
- `pip freeze` 不导出 pip/setuptools 自己

### 练习

- `venv_demo/myenv`：创建 venv + 装 requests + 导出 requirements.txt，全程跑通 ✅

## 进度

- 模块与工具：模块与导入 ✅、虚拟环境与包管理 ✅（异常处理、文件上下文此前已掌握，域内 4/4 齐）
- 下一站：属性管理（@property / setter / 描述符 / __slots__）—— OOP 收尾

---

## 六、属性管理（面向对象 · 第 4 课，OOP 收尾）

> 状态：概念已讲，练习**进行中**（巩固 7 题对 5，3 处待改）

### 学了什么

| 概念 | 代码 | 一句话 |
|------|------|--------|
| @property | `@property def age(self): return self._age` | 方法伪装成属性（读） |
| @age.setter | `@age.setter` | 拦截赋值，做校验 |
| @age.deleter | `@age.deleter` | 拦截删除 |
| 只读属性 | 只写 @property 不写 setter | 只能读不能写 |
| __slots__ | `__slots__ = ("x", "y")` | 限制属性 + 省内存 |

### 核心理解

1. **@property 本质**：方法伪装成属性 —— 外面 `obj.age` 像属性，里面是方法能做校验
2. **self vs self.xxx**（⭐ 连犯两次，重点）：`self` 是对象本身，`self.xxx` 是属性值；算面积用 `self.side ** 2`，绝不 `self = self.side`
3. **内部存数据用 `_age`**（下划线），不能碰同名属性 `age`，否则 property 递归死循环
4. **范围校验方向**：if 写「非法」——`value < 下限 or value > 上限` 才 raise（合法放行）

### 踩坑（本次暴露，重点记）

1. `self = self.side`（把对象覆盖成数字）→ 应 `return self.side ** 2`
2. 漏 `self` 参数（`def bark():`）→ `def bark(self):`
3. `&&` → Python 用 `and`
4. `__slot__` 拼错 → `__slots__`
5. deleter 用 `del self._code` → 应 `self._code = None`（删属性 ≠ 设 None）
6. 范围方向反（合法才 raise）→ 非法才 raise：`len < 6 or len > 20`
7. `__init__` 里 `self.value = value`（value 未定义）→ 应 `self._value = 0`

### 练习

- `property_practice.py` — 7 题初练，暴露 6 处错误（5 粗心 + 3 概念）
- `property_practice2.py` — 巩固 7 题，5 题对 ✅；题 2（self.xxx）、题 5（初始化）、题 7（范围方向）待改

## 进度

- OOP：类与对象 ✅、继承多态 ✅、魔术方法 ✅、属性管理（概念已懂，练习待改对）
- 下一站：常用标准库（os / sys / json / datetime / csv / collections）
