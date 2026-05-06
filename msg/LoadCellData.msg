std_msgs/Header header
int32   raw_count    # 24-bit signed ADC count (AIN0 - AIN1 differential)
float64 voltage_mv   # Differential voltage [mV]
float64 force_n      # Calibrated force [N]  (= (voltage_mv - zero_offset_mv) * scale_n_per_mv)
