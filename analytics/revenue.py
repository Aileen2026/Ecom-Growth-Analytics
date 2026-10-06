import pandas as pd

def get_user_revenue(transactions, users):
    user_rev = (
        transactions.groupby("user_id")["revenue"].sum()
        .reset_index().rename(columns={"revenue": "total_revenue"})
    )
    df = users.merge(user_rev, on="user_id", how="left")
    df["total_revenue"] = df["total_revenue"].fillna(0)
    df["signup_month"] = df["signup_date"].dt.to_period("M").astype(str)
    return df

def get_revenue_summary(users_revenue):
    return {
        "total_revenue": float(users_revenue["total_revenue"].sum()),
        "arpu": float(users_revenue["total_revenue"].mean()),
        "paying_arpu": float(
            users_revenue.query("total_revenue > 0")["total_revenue"].mean()
        ),
        "paying_users": int((users_revenue["total_revenue"] > 0).sum()),
        "paying_rate": float((users_revenue["total_revenue"] > 0).mean()),
    }

def get_revenue_by_experiment(users_revenue):
    return (
        users_revenue.groupby("experiment_group")
        .agg(
            users=("user_id", "count"),
            total_revenue=("total_revenue", "sum"),
            arpu=("total_revenue", "mean"),
            paying_users=("total_revenue", lambda x: (x > 0).sum()),
        )
        .reset_index()
    )

def get_cohort_revenue(users_revenue):
    return (
        users_revenue.groupby("signup_month")
        .agg(
            users=("user_id", "count"),
            total_revenue=("total_revenue", "sum"),
            arpu=("total_revenue", "mean"),
        )
        .reset_index().sort_values("signup_month")
    )

def get_segment_revenue(users_revenue):
    return (
        users_revenue.groupby("user_segment")
        .agg(
            users=("user_id", "count"),
            total_revenue=("total_revenue", "sum"),
            arpu=("total_revenue", "mean"),
        )
        .reset_index().sort_values("arpu", ascending=False)
    )

def get_ltv_curve(transactions, users, by="experiment_group", weeks=12):
    """
    按周累计 LTV，可以看清 A/B 组里哪一组"活得久"。
    这里用每笔交易的 transaction_date 与 signup_date 的周差。
    """
    tx = transactions.merge(
        users[["user_id", "signup_date", by]], on="user_id", how="left"
    )
    tx["week"] = ((tx["transaction_date"] - tx["signup_date"]).dt.days // 7)
    tx = tx[(tx["week"] >= 0) & (tx["week"] < weeks)]

    weekly = (
        tx.groupby([by, "week"])["revenue"].sum()
        .groupby(level=0).cumsum()
        .reset_index()
    )
    return weekly