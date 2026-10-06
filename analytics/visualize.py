import plotly.express as px
import plotly.graph_objects as go

COLOR_MAP = {"control": "#636EFA", "treatment": "#EF553B"}

def plot_retention_curves(df, x="week", y="retention_rate", color=None, title=""):
    fig = px.line(df, x=x, y=y, color=color, markers=True, title=title,
                  color_discrete_map=COLOR_MAP if color == "experiment_group" else None)
    fig.update_layout(yaxis_tickformat=".0%", height=420,
                      xaxis_title="周次", yaxis_title="留存率")
    return fig

def plot_cohort_heatmap(cohort_df, title="同期群留存热力图"):
    pivot = cohort_df.pivot(index="signup_month", columns="week", values="is_active")
    fig = px.imshow(
        pivot, color_continuous_scale="RdYlGn", aspect="auto",
        labels=dict(x="周次", y="注册月份", color="留存率"),
        title=title
    )
    return fig

def plot_funnel(funnel_df, title="转化漏斗"):
    fig = go.Figure(go.Funnel(
        y=["注册", "激活", "购买"],
        x=[
            funnel_df["signups"].iloc[0],
            funnel_df["activated_users"].iloc[0],
            funnel_df["purchasers"].iloc[0],
        ],
        textinfo="value+percent previous",
        marker=dict(color=["#1f77b4", "#ff7f0e", "#2ca02c"]),
    ))
    fig.update_layout(title=title, height=420)
    return fig

def plot_ab_test(summary, metric="activation_rate", title="A/B 激活率对比"):
    fig = px.bar(
        summary, x="experiment_group", y=metric, color="experiment_group",
        text=metric, color_discrete_map=COLOR_MAP, title=title
    )
    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig.update_layout(showlegend=False, height=420,
                      xaxis_title="分组", yaxis_title="比率")
    return fig

def plot_ltv_curve(ltv_df, by="experiment_group", title="LTV 累计曲线"):
    fig = px.line(ltv_df, x="week", y="revenue", color=by, markers=True,
                  color_discrete_map=COLOR_MAP, title=title)
    fig.update_layout(height=420, xaxis_title="周次", yaxis_title="累计收入")
    return fig

def plot_churn_coefficients(coef_df, top_n=10):
    pos = coef_df[coef_df["coefficient"] > 0].head(top_n)
    neg = coef_df[coef_df["coefficient"] < 0].tail(top_n)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=pos["feature"], x=pos["coefficient"],
                         orientation="h", name="提高流失风险",
                         marker_color="#EF553B"))
    fig.add_trace(go.Bar(y=neg["feature"], x=neg["coefficient"],
                         orientation="h", name="降低流失风险",
                         marker_color="#00CC96"))
    fig.update_layout(barmode="relative", height=520,
                      title="流失模型特征系数",
                      xaxis_title="系数", yaxis_title="特征")
    return fig