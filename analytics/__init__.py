from .config import Config, CFG
from .data_loader import load_data, init_duckdb, validate_data
from .funnel import get_funnel_overall, get_funnel_by_dimension, get_funnel_all_dimensions
from .ab_test import run_ab_test, ab_segment_effects, ci_overlap_check
from .retention import (
    get_overall_retention, get_retention_by_experiment,
    get_cohort_table, get_segment_retention, retention_dual_view
)
from .revenue import (
    get_user_revenue, get_revenue_summary,
    get_cohort_revenue, get_segment_revenue,
    get_ltv_curve, get_revenue_by_experiment
)
from .churn import build_churn_model, compare_churn_models
from .visualize import (
    plot_retention_curves, plot_cohort_heatmap,
    plot_funnel, plot_ab_test, plot_churn_coefficients, plot_ltv_curve
)


