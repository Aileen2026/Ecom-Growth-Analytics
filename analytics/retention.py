import pandas as pd
from .config import CFG

def _enrich(retention, users):
    enriched = retention.merge(
        users[["user_id", "signup_date", "experiment_group",
               "acquisition_channel", "device_type", "user_segment"]],
        on="user_id", how="left"
    )
    enriched["signup_month"] = (
        enriched["signup_date"].dt.to_period("M").astype(str)
    )
    return enriched

def _apply_denominator(enriched):
    """
    口径选择：
      - all_users：原口径，分母是 retention 表里的所有用户
      - week0_active：标准留存口径，分母只看 week0 活跃用户
    """
    if CFG.retention_denominator == "week0_active":
        base = enriched.query("week == 0 and is_active == 1")["user_id"].unique()
        enriched = enriched[enriched["user_id"].isin(base)]
    return enriched

def get_overall_retention(retention, users):
    enriched = _apply_denominator(_enrich(retention, users))
    return (
        enriched.groupby("week")["is_active"].mean()
        .reset_index().rename(columns={"is_active": "retention_rate"})
    )

def get_retention_by_experiment(retention, users):
    enriched = _apply_denominator(_enrich(retention, users))
    return (
        enriched.groupby(["experiment_group", "week"])["is_active"].mean()
        .reset_index().rename(columns={"is_active": "retention_rate"})
    )

def get_cohort_table(retention, users):
    enriched = _apply_denominator(_enrich(retention, users))
    return (
        enriched.groupby(["signup_month", "week"])["is_active"].mean()
        .reset_index()
    )

def get_segment_retention(retention, users):
    enriched = _apply_denominator(_enrich(retention, users))
    return (
        enriched.groupby(["user_segment", "week"])["is_active"].mean()
        .reset_index()
    )

def retention_dual_view(retention, users):
    """
    同时返回原口径和标准口径，方便对比。
    这也是业务分析里值得明确写清楚的一步。
    """
    enriched = _enrich(retention, users)
    original = (
        enriched.groupby("week")["is_active"].mean()
        .rename("retention_all_users")
    )
    base = enriched.query("week == 0 and is_active == 1")["user_id"].unique()
    standard = (
        enriched[enriched["user_id"].isin(base)]
        .groupby("week")["is_active"].mean()
        .rename("retention_week0_active")
    )
    return pd.concat([original, standard], axis=1).reset_index()