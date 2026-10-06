
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from analytics import (
    CFG,
    load_data,
    init_duckdb,
    validate_data,
    # 漏斗
    get_funnel_overall,
    get_funnel_by_dimension,
    get_funnel_all_dimensions,
    # A/B
    run_ab_test,
    ab_segment_effects,
    ci_overlap_check,
    # 留存
    get_overall_retention,
    get_retention_by_experiment,
    get_cohort_table,
    get_segment_retention,
    retention_dual_view,
    # 收入
    get_user_revenue,
    get_revenue_summary,
    get_revenue_by_experiment,
    get_cohort_revenue,
    get_segment_revenue,
    get_ltv_curve,
    # 流失
    build_churn_model,
    compare_churn_models,
    # 可视化
    plot_retention_curves,
    plot_cohort_heatmap,
    plot_funnel,
    plot_ab_test,
    plot_ltv_curve,
    plot_churn_coefficients,
)


# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="电商分析仪表盘",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .insight-box {
        background-color: #fff8e1;
        border-left: 4px solid #ffb300;
        padding: 0.8rem 1rem;
        border-radius: 0.4rem;
        margin: 0.8rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 数据加载（缓存）
# ============================================================
@st.cache_data(show_spinner=False)
def _load():
    users, transactions, retention = load_data()
    return users, transactions, retention


@st.cache_resource(show_spinner=False)
def _duck(users, transactions, retention):
    return init_duckdb(users, transactions, retention)


# ============================================================
# 主入口
# ============================================================
def main():
    st.markdown(
        '<h1 class="main-header">📊 电商分析仪表盘</h1>',
        unsafe_allow_html=True,
    )

    with st.spinner("正在加载数据..."):
        users, transactions, retention = _load()
        con = _duck(users, transactions, retention)

    # ------- 侧边栏 -------
    st.sidebar.title("📋 导航")
    page = st.sidebar.radio(
        "选择分析模块",
        [
            "总览",
            "漏斗分析",
            "A/B 测试",
            "留存分析",
            "收入与 LTV",
            "流失预测",
            "数据质量",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**数据概览**")
    st.sidebar.metric("总用户数", f"{len(users):,}")
    st.sidebar.metric("总交易数", f"{len(transactions):,}")
    st.sidebar.metric(
        "总收入", f"${transactions['revenue'].sum():,.0f}"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"留存口径：`{CFG.retention_denominator}`\n\n"
        f"流失标签周：week {CFG.churn_final_week}"
    )

    # ------- 路由 -------
    if page == "总览":
        show_overview(users, transactions, retention, con)
    elif page == "漏斗分析":
        show_funnel(con)
    elif page == "A/B 测试":
        show_ab_test(con, users)
    elif page == "留存分析":
        show_retention(retention, users)
    elif page == "收入与 LTV":
        show_revenue(transactions, users)
    elif page == "流失预测":
        show_churn(retention, users)
    elif page == "数据质量":
        show_data_quality(users, transactions, retention)


# ============================================================
# 总览
# ============================================================
def show_overview(users, transactions, retention, con):
    st.header("📈 业务总览")

    funnel = get_funnel_overall(con).iloc[0]
    rev_summary = get_revenue_summary(get_user_revenue(transactions, users))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总注册数", f"{int(funnel['signups']):,}")
    c2.metric(
        "激活用户数",
        f"{int(funnel['activated_users']):,}",
        f"{funnel['activation_rate']*100:.1f}%",
    )
    c3.metric(
        "购买用户数",
        f"{int(funnel['purchasers']):,}",
        f"{funnel['overall_conversion']*100:.1f}%",
    )
    c4.metric("总收入", f"${rev_summary['total_revenue']:,.0f}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("转化漏斗")
        st.plotly_chart(
            plot_funnel(get_funnel_overall(con)),
            use_container_width=True,
        )
    with col2:
        st.subheader("用户分群占比")
        dist = users["user_segment"].value_counts()
        fig = px.pie(values=dist.values, names=dist.index, hole=0.4)
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("获客渠道")
        d = users["acquisition_channel"].value_counts()
        fig = px.bar(
            x=d.index, y=d.values,
            labels={"x": "渠道", "y": "用户数"},
            color=d.index,
        )
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("设备类型")
        d = users["device_type"].value_counts()
        fig = px.bar(
            x=d.index, y=d.values,
            labels={"x": "设备", "y": "用户数"},
            color=d.index,
        )
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 漏斗分析
# ============================================================
def show_funnel(con):
    st.header("🎯 漏斗分析")

    funnel = get_funnel_overall(con).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("激活率", f"{funnel['activation_rate']*100:.2f}%")
    c2.metric(
        "激活后购买率",
        f"{funnel['purchase_rate_from_activated']*100:.2f}%",
    )
    c3.metric(
        "整体转化率", f"{funnel['overall_conversion']*100:.2f}%"
    )

    st.markdown(
        '<div class="insight-box">'
        "口径已修正：购买率的分子只统计「已激活且购买」的用户，"
        "分母加 NULLIF 防止除零。"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    dim = st.selectbox(
        "分析维度：",
        list(CFG.dim_labels.keys()),
        format_func=lambda x: CFG.dim_labels[x],
    )
    dim_label = CFG.dim_labels[dim]

    df = get_funnel_by_dimension(con, dim)
    st.subheader(f"按{dim_label}的漏斗")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            df, x=dim, y="activation_rate",
            color="activation_rate", color_continuous_scale="Blues",
            labels={dim: dim_label, "activation_rate": "激活率"},
        )
        fig.update_layout(showlegend=False, height=400,
                          title=f"激活率（按{dim_label}）")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(
            df, x=dim, y="overall_conversion",
            color="overall_conversion", color_continuous_scale="Greens",
            labels={dim: dim_label, "overall_conversion": "整体转化率"},
        )
        fig.update_layout(showlegend=False, height=400,
                          title=f"整体转化率（按{dim_label}）")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("查看所有维度的漏斗结果（一次查询）"):
        st.dataframe(get_funnel_all_dimensions(con), use_container_width=True)


# ============================================================
# A/B 测试
# ============================================================
def show_ab_test(con, users):
    st.header("🧪 A/B 测试分析")

    ab = run_ab_test(con, users, metric="activated")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("对照组激活率", f"{ab['control_rate']*100:.2f}%")
    c2.metric("实验组激活率", f"{ab['treatment_rate']*100:.2f}%")
    c3.metric("绝对提升", f"{ab['absolute_lift']*100:.2f} pp")
    c4.metric("相对提升", f"{ab['relative_lift']*100:.2f}%")

    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("统计显著性")
        if ab["significant"]:
            st.success(f"✅ 统计显著（p = {ab['p_value']:.2e}）")
        else:
            st.warning(f"⚠️ 统计不显著（p = {ab['p_value']:.4f}）")

        low, high = ab["ci_95"]
        st.write(
            f"**主指标差值 95% 置信区间**："
            f"({low*100:.2f} pp, {high*100:.2f} pp)"
        )
        if ci_overlap_check(ab):
            st.caption("⚠️ 置信区间包含 0，效应可能不稳定。")

    with col2:
        st.metric("p 值", f"{ab['p_value']:.2e}")
        st.metric("显著性水平 α", f"{CFG.alpha}")

    st.markdown("---")

    st.subheader("分组详细对比")
    st.dataframe(ab["summary"], use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            plot_ab_test(ab["summary"], "activation_rate"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            plot_ab_test(ab["summary"], "overall_conversion",
                         title="A/B 整体转化率对比"),
            use_container_width=True,
        )

    st.subheader("分设备类型效应")
    seg = ab_segment_effects(con, "device_type")
    fig = px.bar(
        seg, x="device_type", y="activation_rate",
        color="experiment_group", barmode="group",
        labels={
            "device_type": "设备类型",
            "activation_rate": "激活率",
            "experiment_group": "分组",
        },
        text="activation_rate",
    )
    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="insight-box">'
        "<b>注意</b>：主指标（激活率）显著为正，但留存与 LTV 需要单独评估。"
        "请在「留存分析」和「收入与 LTV」页面查看长期效应，"
        "避免只看短期指标下结论。"
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# 留存分析
# ============================================================
def show_retention(retention, users):
    st.header("📅 留存分析")

    st.markdown(
        f'<div class="insight-box">当前留存口径：'
        f'<b>{CFG.retention_denominator}</b>'
        f'（`week0_active` 表示分母只含 week 0 活跃用户；'
        f'`all_users` 表示原口径）</div>',
        unsafe_allow_html=True,
    )

    # 双口径对比
    st.subheader("两种留存口径对比")
    dual = retention_dual_view(retention, users)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dual["week"], y=dual["retention_all_users"],
        mode="lines+markers", name="全用户口径",
    ))
    fig.add_trace(go.Scatter(
        x=dual["week"], y=dual["retention_week0_active"],
        mode="lines+markers", name="week0 活跃用户口径",
    ))
    fig.update_layout(
        height=420, yaxis_tickformat=".0%",
        xaxis_title="周次", yaxis_title="留存率",
    )
    st.plotly_chart(fig, use_container_width=True)

    # 整体留存（标准口径）
    st.subheader("整体留存曲线（标准口径）")
    overall = get_overall_retention(retention, users)
    st.plotly_chart(
        plot_retention_curves(overall, title="整体留存"),
        use_container_width=True,
    )

    c1, c2, c3 = st.columns(3)
    def _ret(week):
        r = overall.query("week == @week")
        return float(r["retention_rate"].iloc[0]) if len(r) else float("nan")
    c1.metric("第 1 周留存", f"{_ret(1)*100:.1f}%")
    c2.metric("第 4 周留存", f"{_ret(4)*100:.1f}%")
    c3.metric("第 8 周留存", f"{_ret(8)*100:.1f}%")

    st.markdown("---")

    # 按实验组
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("按实验分组的留存")
        ret_exp = get_retention_by_experiment(retention, users)
        st.plotly_chart(
            plot_retention_curves(
                ret_exp, color="experiment_group",
                title="按实验分组留存",
            ),
            use_container_width=True,
        )
    with col2:
        st.subheader("按用户分群的留存")
        ret_seg = get_segment_retention(retention, users)
        st.plotly_chart(
            plot_retention_curves(
                ret_seg, y="is_active", color="user_segment",
                title="按用户分群留存",
            ),
            use_container_width=True,
        )

    st.markdown(
        '<div class="insight-box">'
        "<b>观察</b>：<br>"
        "1. 实验组 week1 起留存即低于对照组，且差距随周数扩大；<br>"
        "2. <code>price_sensitive</code> 分群留存约为其他两组的一半，"
        "且占总用户约 40%，是留存优化的最大杠杆。"
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("同期群留存热力图")
    cohort = get_cohort_table(retention, users)
    st.plotly_chart(plot_cohort_heatmap(cohort), use_container_width=True)

    st.markdown(
        '<div class="insight-box">'
        "8 个同期群曲线高度重合，说明产品迭代在过去 8 个月里"
        "对留存没有显著改善。"
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# 收入与 LTV
# ============================================================
def show_revenue(transactions, users):
    st.header("💰 收入与 LTV 分析")

    ur = get_user_revenue(transactions, users)
    summary = get_revenue_summary(ur)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总收入", f"${summary['total_revenue']:,.0f}")
    c2.metric("ARPU", f"${summary['arpu']:.2f}")
    c3.metric("付费 ARPU", f"${summary['paying_arpu']:.2f}")
    c4.metric("付费用户占比", f"{summary['paying_rate']*100:.1f}%")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("按实验分组的收入")
        rev_exp = get_revenue_by_experiment(ur)
        st.dataframe(rev_exp, use_container_width=True)
    with col2:
        fig = px.bar(
            rev_exp, x="experiment_group", y="arpu",
            color="experiment_group", text="arpu",
            labels={"experiment_group": "分组", "arpu": "ARPU（美元）"},
        )
        fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("LTV 累计曲线")
    ltv = get_ltv_curve(transactions, users, by="experiment_group")
    st.plotly_chart(plot_ltv_curve(ltv), use_container_width=True)

    st.markdown(
        '<div class="insight-box">'
        "<b>判断方法</b>：<br>"
        "· 若实验组曲线始终高于对照组 → 可以考虑上线；<br>"
        "· 若两曲线在中后期交叉 → 实验组只是「提前变现」，长期未必更好；<br>"
        "· 若实验组后期斜率更低 → 长期负向，不建议上线。"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("按用户分群收入")
        seg_rev = get_segment_revenue(ur)
        st.dataframe(seg_rev, use_container_width=True)
    with col2:
        fig = px.bar(
            seg_rev, x="user_segment", y="arpu",
            color="arpu", color_continuous_scale="Viridis",
            text="arpu",
            labels={"user_segment": "用户分群", "arpu": "ARPU（美元）"},
        )
        fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("按注册同期群的收入")
    cohort_rev = get_cohort_revenue(ur)
    fig = px.line(
        cohort_rev, x="signup_month", y="arpu", markers=True,
        labels={"signup_month": "注册月份", "arpu": "ARPU（美元）"},
    )
    fig.update_traces(line_color="#2ca02c", line_width=3)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("收入分布（付费用户）")
    fig = px.histogram(
        ur[ur["total_revenue"] > 0], x="total_revenue", nbins=50,
        labels={"total_revenue": "总收入（美元）"},
        color_discrete_sequence=["#1f77b4"],
    )
    fig.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 流失预测
# ============================================================
def show_churn(retention, users):
    st.header("🔮 流失预测")

    st.markdown(
        f'<div class="insight-box">'
        f'流失标签：week {CFG.churn_final_week} 不活跃即为流失（churned=1）。'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 模型对比
    st.subheader("两版模型对比（早期预警 vs 常规）")
    cmp = compare_churn_models(retention, users)
    c1, c2 = st.columns(2)
    c1.metric(
        f"早期预警模型（week ≤ {cmp['early_window']}）",
        f"AUC = {cmp['early_auc']:.4f}",
    )
    c2.metric(
        f"常规模型（week ≤ {cmp['regular_window']}）",
        f"AUC = {cmp['regular_auc']:.4f}",
    )

    st.markdown(
        '<div class="insight-box">'
        "两版模型 AUC 差距主要来自 <code>early_activity_rate</code> 与标签"
        "高度相关（信息泄露）。业务上更应关注 <b>早期预警模型</b>："
        "AUC 更低，但能提前 7 周干预。"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 展示早期预警模型的系数
    with st.spinner("正在训练早期预警模型..."):
        auc, coef = build_churn_model(
            retention, users,
            early_window=CFG.churn_early_window,
        )

    st.subheader("早期预警模型特征系数")
    st.metric("ROC-AUC", f"{auc:.4f}")
    if auc >= 0.8:
        st.success("✅ 模型表现优秀")
    elif auc >= 0.7:
        st.info("ℹ️ 模型表现良好")
    else:
        st.warning("⚠️ 模型表现一般（这对早期预警模型来说是正常的）")

    st.plotly_chart(
        plot_churn_coefficients(coef), use_container_width=True
    )

    with st.expander("查看全部特征系数"):
        st.dataframe(coef, use_container_width=True)

    st.markdown("---")
    st.subheader("关键洞察")

    top_risk = coef.iloc[0]
    top_protective = coef.iloc[-1]

    c1, c2 = st.columns(2)
    with c1:
        st.warning(f"**最高风险因素**：{top_risk['feature']}")
        st.write(
            f"系数 {top_risk['coefficient']:.4f}，"
            "具有该特征的用户流失风险最高。"
        )
    with c2:
        st.info(f"**最强保护因素**：{top_protective['feature']}")
        st.write(
            f"系数 {top_protective['coefficient']:.4f}，"
            "具有该特征的用户流失风险最低。"
        )


# ============================================================
# 数据质量
# ============================================================
def show_data_quality(users, transactions, retention):
    st.header("🧹 数据质量报告")

    report = validate_data(users, transactions, retention)

    df = pd.DataFrame(
        [(k, v) for k, v in report.items()],
        columns=["指标", "值"],
    )
    st.dataframe(df, use_container_width=True)

    st.markdown(
        """
        **字段含义**

        | 字段 | 说明 |
        |------|------|
        | `duplicate_user_week` | (user_id, week) 重复行数，应为 0 |
        | `users_with_missing_weeks` | 记录数不足 12 周的用户数 |
        | `week0_active_users` | week 0 活跃的用户数（标准留存分母） |
        | `users_not_in_retention` | users.csv 中但不在 retention.csv 的用户数 |
        | `retention_users_not_in_users` | retention.csv 中但不在 users.csv 的用户数 |
        | `purchased_but_not_activated` | 购买了但未激活的用户数（口径异常） |
        """
    )

    st.markdown("---")

    # 分布类检查
    st.subheader("各字段分布")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**用户分群**")
        st.dataframe(
            users["user_segment"].value_counts().rename("用户数"),
            use_container_width=True,
        )
        st.write("**获客渠道**")
        st.dataframe(
            users["acquisition_channel"].value_counts().rename("用户数"),
            use_container_width=True,
        )
    with col2:
        st.write("**实验分组**")
        st.dataframe(
            users["experiment_group"].value_counts().rename("用户数"),
            use_container_width=True,
        )
        st.write("**设备类型**")
        st.dataframe(
            users["device_type"].value_counts().rename("用户数"),
            use_container_width=True,
        )

    st.subheader("收入分位数")
    if "revenue" in transactions.columns:
        q = transactions["revenue"].describe(
            percentiles=[0.5, 0.9, 0.99]
        )
        st.dataframe(q.rename("收入").to_frame(), use_container_width=True)


# ============================================================
if __name__ == "__main__":
    main()