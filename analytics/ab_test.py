import numpy as np
import pandas as pd
from statsmodels.stats.proportion import (
    proportions_ztest, confint_proportions_2indep
)
from .config import CFG

_AB_SQL = """
SELECT
    experiment_group,
    COUNT(*) AS users,
    SUM(CASE WHEN activated THEN 1 ELSE 0 END) AS activated_users,
    COUNT(DISTINCT CASE WHEN activated THEN t.user_id END) AS purchasers,
    ROUND(
        SUM(CASE WHEN activated THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0),
        4
    ) AS activation_rate,
    ROUND(
        COUNT(DISTINCT CASE WHEN activated THEN t.user_id END) * 1.0
        / NULLIF(COUNT(*), 0),
        4
    ) AS overall_conversion
FROM users u
LEFT JOIN transactions t ON u.user_id = t.user_id
GROUP BY experiment_group
"""

def run_ab_test(con, users, metric="activated"):
    """主指标默认用 activation，可换成其他 0/1 列"""
    summary = con.execute(_AB_SQL).df()

    control = users[users["experiment_group"] == "control"][metric]
    treatment = users[users["experiment_group"] == "treatment"][metric]

    successes = np.array([control.sum(), treatment.sum()])
    trials = np.array([len(control), len(treatment)])

    stat, pval = proportions_ztest(successes, trials)

    control_rate = control.mean()
    treatment_rate = treatment.mean()
    lift = treatment_rate - control_rate
    rel_lift = lift / control_rate if control_rate else np.nan

    # 95% 置信区间
    ci_low, ci_high = confint_proportions_2indep(
        successes[1], trials[1], successes[0], trials[0], method="wald"
    )

    return {
        "summary": summary,
        "z_stat": float(stat),
        "p_value": float(pval),
        "control_rate": float(control_rate),
        "treatment_rate": float(treatment_rate),
        "absolute_lift": float(lift),
        "relative_lift": float(rel_lift),
        "ci_95": (float(ci_low), float(ci_high)),
        "significant": bool(pval < CFG.alpha),
    }

def ab_segment_effects(con, dimension="device_type"):
    """分层看效果，用于探索性分析"""
    sql = f"""
    SELECT
        {dimension},
        experiment_group,
        COUNT(*) AS users,
        ROUND(
            SUM(CASE WHEN activated THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4
        ) AS activation_rate
    FROM users
    GROUP BY {dimension}, experiment_group
    ORDER BY {dimension}, experiment_group
    """
    return con.execute(sql).df()

def ci_overlap_check(ab_result):
    """A/B 主指标 95% CI 是否包含 0，用于辅助判断"""
    low, high = ab_result["ci_95"]
    return not (low > 0 or high < 0)