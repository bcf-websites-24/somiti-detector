class Config:
    dt_dist = "log_normal"
    dt_avg = 60.0
    dt_std = 6.0

    temporal_weight = 0.6
    overlap_weight = 0.3
    batch_diff_weight = 0.1

    batch_diff_multiplier = 2.0

    threshold = 0.15


config = Config()
