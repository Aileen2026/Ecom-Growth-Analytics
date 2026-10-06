from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

@dataclass
class Config:
    base_path: Path = PROJECT_ROOT / "Data"

    # 流失模型
    churn_final_week: int = 8
    churn_early_window: int = 1        # 早期预警模型窗口
    churn_regular_window: int = 4      # 常规模型窗口
    test_size: float = 0.3
    random_state: int = 42

    # 统计检验
    alpha: float = 0.05
    primary_metric: str = "activation_rate"

    # 留存口径
    # "all_users"    -> 分母是 retention 表里所有用户（原口径）
    # "week0_active" -> 分母是 week=0 且活跃的用户（标准口径）
    retention_denominator: str = "week0_active"

    # 中文展示映射
    dim_labels: dict = field(default_factory=lambda: {
        "device_type": "设备类型",
        "acquisition_channel": "获客渠道",
        "user_segment": "用户分群",
        "country": "国家",
        "experiment_group": "实验分组",
    })
    group_labels: dict = field(default_factory=lambda: {
        "control": "对照组",
        "treatment": "实验组",
    })

CFG = Config()