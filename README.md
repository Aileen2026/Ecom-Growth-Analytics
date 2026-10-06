# 🚀 端到端产品增长分析

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-red)
![DuckDB](https://img.shields.io/badge/Engine-DuckDB-yellow)
![机器学习](https://img.shields.io/badge/ML-Logistic%20Regression-orange)
![A/B 测试](https://img.shields.io/badge/A%2FB%20Testing-Enabled-green)
![状态](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![许可证](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 🧭 TL;DR（执行摘要）

这是是一个**全栈产品分析案例研究**，覆盖 **50,000 名用户的完整生命周期**：

- 漏斗 → 激活 → 转化
- A/B 测试 → 实验影响
- 留存 → 队列衰减
- 收入 → ARPU 与分群
- 流失 → 预测建模

📌 **核心洞察：**
> 仅针对激活进行增长优化可能会损害留存——可持续增长需要针对 **LTV（生命周期价值）** 进行优化。

---

## 📌 问题陈述

大多数产品团队优化**漏斗顶部指标（激活、转化）**，
但未能评估**下游影响（留存、流失、收入质量）**。

本项目回答：

- 漏斗中最大的瓶颈在哪里？
- 提高激活会提升收入吗？
- 是否存在与留存相关的隐藏权衡？
- 哪些用户带来长期价值？
- 能否提前预测流失？

---

## 🧠 关键结果

| 指标 | 数值 |
|------|------|
| 用户数 | 50,000 |
| 激活率 | 37.75% |
| 购买者 | 5,277 |
| 收入 | $392,280 |
| ARPU | $7.85 |
| ARPPU | $74.34 |
| 早期预警模型 ROC-AUC | **0.743** |
| 常规流失模型 ROC-AUC | 0.862（存在信息泄露） |

---

## 🔍 分析拆解

### 🔻 1. 漏斗分析

- 最大流失发生在**激活阶段**（注册 → 激活仅 37.75%）
- 桌面端（40.89%）显著优于移动端（35.63%）
- `power` 分群激活率 44.78%，远高于 `price_sensitive`（35.13%）
- 获客渠道差异不明显，referral 略优

👉 **洞察：** 激活是杠杆最高的增长点，但不同分群差异巨大

---

### 🧪 2. A/B 实验

| 指标 | 对照组 | 实验组 | 提升 |
|------|--------|--------|------|
| 激活率 | 35.36% | 40.12% | **+4.76 pp**（相对 +13.5%） |
| 整体转化率 | 10.04% | 11.06% | +1.02 pp |
| ARPU | $7.37 | $8.32 | +12.8% |

- 统计显著改善（p ≈ 4.6e-28）
- 95% CI（差值）：(3.91 pp, 5.61 pp)，不包含 0

👉 **洞察：** 实验改善了漏斗顶部指标

---

### 🔁 3. 留存分析

- 标准口径下留存从 **week 1 = 93.3% → week 11 = 47.6%** 下降
- 实验组从 week 1 起留存即低于对照组，差距随周数扩大
- week 11 两组差值：**−11.1 pp**
- `price_sensitive` 分群留存约为其他两组一半，占总用户约 40%
- 8 个同期群曲线高度重合 → 过去 8 个月产品迭代对留存无显著改善

👉 **关键洞察：**
> 激活提升引入了质量较低的用户 → 留存权衡

---

### 💰 4. 收入影响

| 指标 | 对照组 | 实验组 |
|------|--------|--------|
| 收入 | $183,580 | $208,700 |
| ARPU | $7.37 | $8.32 |
| 付费用户数 | 2,501 | 2,776 |

- 收入集中在 **`power` 分群**（ARPU $9.72，人数与 `casual` 相当）
- 实验组同时提高了激活和 ARPU
- LTV 累计曲线：实验组全程领先，但差距随周数收窄

👉 **洞察：** 增长由高价值分群驱动；长期价值需用 12 周 LTV 曲线判断

---

### ⚠️ 5. 流失预测

| 模型 | 特征窗口 | ROC-AUC |
|------|----------|---------|
| 常规模型 | week ≤ 4 | 0.862 |
| **早期预警** | **week ≤ 1** | **0.743** |

- 常规模型 AUC 偏高来自 `early_activity_rate` 与标签高度相关（**信息泄露**）
- 早期预警模型 AUC 更低，但能提前 7 周干预，业务价值更高

👉 关键驱动因素：

- **最高风险**：`user_segment_price_sensitive`（系数 +0.93）
- **最强保护**：`early_activity_rate`（系数 −10.15）

👉 **洞察：**
> 流失可以被提前预测 → 存在很强的干预机会

---

## 🧪 产品思考与建议

### 🎯 分群感知的逐步上线

- 优先考虑 **`power` 分群 + 桌面端**
- 避免一刀切全面上线

---

### 🔄 改善早期留存（第 1–2 周）

- 新用户引导提醒
- 行为触发
- 价值强化

---

### 📊 针对 LTV 优化（而不仅仅是激活）

不要只优化：激活
要优化：**激活 × 留存 × 收入**

---

### 📱 需要移动端优化

- 激活率低（35.63% vs desktop 40.89%）
- 转化率较低（9.91% vs 11.51%）
- 流失风险较高

---

## 🛠️ 技术栈

- **Python**（Pandas、NumPy）
- **查询引擎**（DuckDB，内存 OLAP）
- **机器学习**（Scikit-learn，Logistic Regression）
- **统计**（statsmodels，proportions_ztest + 95% CI）
- **可视化**（Plotly）
- **仪表盘**（Streamlit）

---

## 📂 项目结构

```
.
├── analytics/                  # 分析逻辑包（Notebook 与仪表盘共用）
│   ├── __init__.py             # 统一导出
│   ├── config.py               # 全局配置 CFG
│   ├── data_loader.py          # 数据加载 / DuckDB 注册 / 质量校验
│   ├── funnel.py               # 漏斗分析（SQL）
│   ├── ab_test.py              # A/B 测试（z 检验 + 95% CI）
│   ├── retention.py            # 留存分析（双口径 + 同期群）
│   ├── revenue.py              # 收入与 LTV
│   ├── churn.py                # 流失预测（早期预警 vs 常规）
│   └── visualize.py            # Plotly 图表封装
├── Data/
│   ├── users.csv               # 用户维表
│   ├── transactions.csv        # 交易明细
│   └── retention.csv           # 用户 × 周次 活跃状态
├── Notebook
│   └── analysis.ipynb          # 完整分析 Notebook
├── app.py                      # Streamlit 仪表盘
├── Report.pdf                  # 分析报告
└── README.md
```

---

## 📊 仪表盘页面

| 页面 | 内容 |
|------|------|
| 总览 | 核心指标、漏斗、渠道/设备分布 |
| 漏斗分析 | 整体 + 按维度拆分，支持 4 个维度 |
| A/B 测试 | 主指标、置信区间、分层效应 |
| 留存分析 | 双口径对比、分群、同期群热力图 |
| 收入与 LTV | ARPU、付费率、LTV 累计曲线 |
| 流失预测 | 早期预警 vs 常规模型、特征系数 |
| 数据质量 | 校验报告与字段分布 |

---

## 📐 关键口径说明

| 口径 | 定义 |
|------|------|
| `activation_rate` | 激活用户 / 注册用户 |
| `purchase_rate_from_activated` | 已激活且购买用户 / 激活用户 |
| `overall_conversion` | 已激活且购买用户 / 注册用户 |
| 留存分母（默认） | `week0_active`：week 0 活跃用户（标准口径） |
| 留存分母（备选） | `all_users`：retention 表所有用户（原口径） |
| 流失标签 | week 8 不活跃即 `churned = 1` |

---

## ✅ 数据质量校验

`validate_data()` 返回以下指标，当前数据全部通过（异常项均为 0）：

| 字段 | 说明 |
|------|------|
| `duplicate_user_week` | (user_id, week) 重复行数 |
| `users_with_missing_weeks` | 记录不足 12 周的用户数 |
| `week0_active_users` | week 0 活跃用户数（标准留存分母） |
| `users_not_in_retention` | users 表有但 retention 表无 |
| `retention_users_not_in_users` | retention 表有但 users 表无 |
| `purchased_but_not_activated` | 购买但未激活（口径异常） |

---

## 📌 综合结论

| # | 结论 |
|---|------|
| 1 | **A/B 短期赢、长期存疑**：激活率和短期收入上升，但留存全面下滑 |
| 2 | **漏斗口径已修正**：购买率分子只含已激活用户 |
| 3 | **留存是最大问题**：同期群无改善，`price_sensitive` 是最大杠杆 |
| 4 | **流失模型应以早期预警版为准**：常规模型存在信息泄露 |
| 5 | **下一步**：用 12 周 LTV 曲线决策上线，针对 `price_sensitive` 设计召回，把 week 1 留存作为主指标 |

---