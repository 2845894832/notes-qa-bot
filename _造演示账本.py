# -*- coding: utf-8 -*-
"""造一份演示账本 `记账演示.db`（第 6 课用的柜子）。

为什么另造一份、不直接翻你真正的账本？
    你 `D:\\CC Switch\\expenses.db` 里只有 1 笔（8000 工资），
    拿它问"9 月餐饮花了多少"，答案永远是 0 —— 数不出来，就没法验收。
    所以这里造一份数据量刚好的：**2026 年 9 月 + 10 月，21 笔**。

表名、列名、类型，跟你 SQL 第 5 关做的 A1 项目**一模一样**：
    记录(id, amount, category, kind, date, note)
所以今天这只手，直接就能伸进你自己那个柜子里去 —— 换的只是路径。

跑法：
    cd "D:\\CC Switch\\问答机器人"
    python _造演示账本.py

跑完会打印各月餐饮合计，拿它当答案尺子。
"""

import os
import sqlite3

账本路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "记账演示.db")

数据 = [
    # (amount, category, kind, date, note)
    (8000.0, "工资", "income", "2026-09-01", "9 月工资"),
    (25.5,   "餐饮", "expense", "2026-09-02", "午饭"),
    (18.0,   "餐饮", "expense", "2026-09-03", "咖啡"),
    (62.0,   "餐饮", "expense", "2026-09-05", "周末火锅"),
    (6.0,    "交通", "expense", "2026-09-06", "地铁"),
    (2500.0, "房租", "expense", "2026-09-08", "9 月房租"),
    (32.0,   "餐饮", "expense", "2026-09-10", "外卖"),
    (399.0,  "数码", "expense", "2026-09-12", "耳机"),
    (45.0,   "交通", "expense", "2026-09-15", "打车"),
    (88.0,   "餐饮", "expense", "2026-09-18", "聚餐"),
    (21.5,   "餐饮", "expense", "2026-09-22", "麻辣烫"),
    (15.0,   "餐饮", "expense", "2026-09-28", "早饭"),

    (8000.0, "工资", "income", "2026-10-01", "10 月工资"),
    (120.0,  "餐饮", "expense", "2026-10-02", "国庆聚餐"),
    (88.0,   "交通", "expense", "2026-10-05", "高铁"),
    (26.0,   "餐饮", "expense", "2026-10-08", "午饭"),
    (2500.0, "房租", "expense", "2026-10-10", "10 月房租"),
    (35.5,   "餐饮", "expense", "2026-10-12", "外卖"),
    (59.0,   "图书", "expense", "2026-10-16", "一本书"),
    (19.0,   "餐饮", "expense", "2026-10-20", "咖啡"),
    (42.0,   "餐饮", "expense", "2026-10-22", "火锅"),
]


def main() -> None:
    if os.path.exists(账本路径):
        os.remove(账本路径)

    连接 = sqlite3.connect(账本路径)
    连接.execute("""
        CREATE TABLE 记录 (
            id       INTEGER PRIMARY KEY,
            amount   REAL    NOT NULL,
            category TEXT    NOT NULL,
            kind     TEXT    NOT NULL,
            date     TEXT    NOT NULL,
            note     TEXT    NOT NULL DEFAULT ''
        )
    """)
    连接.executemany(
        "INSERT INTO 记录 (amount, category, kind, date, note) VALUES (?, ?, ?, ?, ?)",
        数据,
    )
    连接.commit()

    print(f"造好了：{账本路径}")
    for 月 in ("2026-09", "2026-10"):
        for 类 in ("餐饮", "交通"):
            合计 = 连接.execute(
                "SELECT SUM(amount) FROM 记录 WHERE kind='expense' AND date LIKE ? AND category = ?",
                (月 + "%", 类),
            ).fetchone()[0]
            print(f"    {月} {类} 合计 = {合计}")
        支出 = 连接.execute(
            "SELECT SUM(amount) FROM 记录 WHERE kind='expense' AND date LIKE ?", (月 + "%",)
        ).fetchone()[0]
        print(f"    {月} 支出合计 = {支出}")
    连接.close()


if __name__ == "__main__":
    main()
