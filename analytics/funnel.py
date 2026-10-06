import pandas as pd
from .config import CFG


_FUNNEL_SQL = """
SELECT
   {dim}COUNT(*) AS signups,
   SUM(CASE WHEN U.activated THEN 1 ELSE 0 END) AS activated_users,
   COUNT(DISTINCT CASE WHEN U.activated THEN T.user_id END) AS purchasers,
   ROUND(
       SUM(CASE WHEN U.activated THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0),
       4
   ) AS activation_rate,
   ROUND(
       COUNT(DISTINCT CASE WHEN U.activated THEN T.user_id END) * 1.0
       / NULLIF(SUM(CASE WHEN U.activated THEN 1 ELSE 0 END), 0),
       4
   ) AS purchase_rate_from_activated,
   ROUND(
       COUNT(DISTINCT CASE WHEN U.activated THEN T.user_id END) * 1.0
       / NULLIF(COUNT(*), 0),
       4
   ) AS overall_conversion
FROM users U
LEFT JOIN transactions T ON U.user_id = T.user_id
{group_by}
"""

def get_funnel_overall(con):
    return con.execute(_FUNNEL_SQL.format(dim="", group_by="")).df()

def get_funnel_by_dimension(con, dimension):
    assert dimension in CFG.dim_labels, f"未知维度: {dimension}"
    sql = _FUNNEL_SQL.format(
        dim=f"U.{dimension},\n   ",
        group_by=f"GROUP BY U.{dimension}\nORDER BY overall_conversion DESC"
    )
    return con.execute(sql).df()

def get_funnel_all_dimensions(con):
    """一次算出所有维度的漏斗，用 GROUPING SETS，减少重复扫描"""
    dims = ["acquisition_channel", "user_segment", "country", "device_type"]
    union_sql = "\nUNION ALL\n".join([
        _FUNNEL_SQL.format(
            dim=f"'{d}' AS dimension, U.{d} AS dimension_value,\n   ",
            group_by=f"GROUP BY U.{d}"
        ) for d in dims
    ])
    return con.execute(union_sql).df()