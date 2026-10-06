import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from .config import CFG

def _build_features(retention, users, final_week, early_window):
    churn = (
        retention.query("week == @final_week")
        .rename(columns={"is_active": "is_active_final"})[["user_id", "is_active_final"]]
    )
    churn["churned"] = 1 - churn["is_active_final"]

    early = (
        retention.query("week <= @early_window")
        .groupby("user_id")["is_active"].mean()
        .reset_index().rename(columns={"is_active": "early_activity_rate"})
    )

    df = (
        users.merge(early, on="user_id", how="left")
             .merge(churn[["user_id", "churned"]], on="user_id", how="left")
    )

    df = df.dropna(subset=["churned"])
    df["churned"] = df["churned"].astype(int)
    df["early_activity_rate"] = df["early_activity_rate"].fillna(0)
    return df

def build_churn_model(retention, users,
                      final_week=None, early_window=None,
                      return_features=False):
    final_week = final_week or CFG.churn_final_week
    early_window = early_window or CFG.churn_regular_window

    feat = _build_features(retention, users, final_week, early_window)

    X = feat[[
        "activated", "early_activity_rate",
        "experiment_group", "device_type", "user_segment"
    ]]
    X = pd.get_dummies(
        X, columns=["experiment_group", "device_type", "user_segment"],
        drop_first=True
    )
    y = feat["churned"]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=CFG.test_size, random_state=CFG.random_state,
        stratify=y
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_tr, y_tr)

    prob = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, prob)

    coef = (
        pd.DataFrame({"feature": X.columns, "coefficient": model.coef_[0]})
        .sort_values("coefficient", ascending=False)
        .assign(impact=lambda d: d["coefficient"].apply(
            lambda c: "提高流失风险" if c > 0 else "降低流失风险"
        ))
    )

    if return_features:
        return auc, coef, feat
    return auc, coef

def compare_churn_models(retention, users):
    """
    对比早期预警模型和常规模型：
      - 早期预警：week<=1 -> week 8 流失，业务价值高，AUC 会低
      - 常规：week<=4 -> week 8 流失，AUC 高，但信息泄露严重
    """
    auc_early, _ = build_churn_model(
        retention, users,
        early_window=CFG.churn_early_window
    )
    auc_regular, _ = build_churn_model(
        retention, users,
        early_window=CFG.churn_regular_window
    )
    return {
        "early_window": CFG.churn_early_window,
        "early_auc": float(auc_early),
        "regular_window": CFG.churn_regular_window,
        "regular_auc": float(auc_regular),
    }