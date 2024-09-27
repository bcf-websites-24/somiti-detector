class Config:
    dt_dist = "log_normal"
    dt_avg = 60.0
    dt_std = 6.0

    temporal_weight = 0.55
    overlap_weight = 0.25
    batch_diff_weight = 0.2

    batch_diff_multiplier = 2.0

    threshold = 0.4

    update_interval = 2 * 60  # Update every hour


config = Config()
