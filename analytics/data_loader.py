import duckdb
import pandas as pd
from .config import CFG

def load_data(base_path=None):
    base = base_path or CFG.base_path
    users = pd.read_csv(f"{base}/users.csv", parse_dates=["signup_date"])
    transactions = pd.read_csv(f"{base}/transactions.csv", parse_dates=["transaction_date"])
    retention = pd.read_csv(f"{base}/retention.csv")
    return users, transactions, retention

def init_duckdb(users, transactions, retention):
    con = duckdb.connect(database=":memory:")
    con.register("users", users)
    con.register("transactions", transactions)
    con.register("retention", retention)
    return con

def validate_data(users, transactions, retention, n_weeks=12):
    """数据质量校验，返回一个 dict 报告"""
    report = {}

    # 1. (user_id, week) 唯一性
    dup = retention.duplicated(["user_id", "week"]).sum()
    report["duplicate_user_week"] = int(dup)

    # 2. 缺失周次
    weeks_per_user = retention.groupby("user_id")["week"].count()
    report["users_with_missing_weeks"] = int((weeks_per_user < n_weeks).sum())
    report["total_users_in_retention"] = int(retention["user_id"].nunique())

    # 3. week 0 不活跃的用户数
    week0_active = retention.query("week == 0 and is_active == 1")["user_id"].nunique()
    report["week0_active_users"] = int(week0_active)

    # 4. 用户表与留存表的覆盖
    report["users_not_in_retention"] = int(
        len(set(users["user_id"]) - set(retention["user_id"]))
    )
    report["retention_users_not_in_users"] = int(
        len(set(retention["user_id"]) - set(users["user_id"]))
    )

    # 5. activated / purchased 一致性
    inconsistent = users.query("purchased == True and activated == False")
    report["purchased_but_not_activated"] = int(len(inconsistent))

    return report