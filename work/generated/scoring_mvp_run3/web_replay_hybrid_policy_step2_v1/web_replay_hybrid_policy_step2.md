# Web 真实采集样本混合对齐策略回放

## 汇总

- 花 / all: n=37, old_avg=30.633, new_avg=58.563, avg_delta=27.930, new_min=10.076, new_max=78.949
- 花 / latest10: n=10, old_avg=30.232, new_avg=46.174, avg_delta=15.942, new_min=25.759, new_max=69.507
- 跳 / all: n=18, old_avg=22.209, new_avg=21.443, avg_delta=-0.767, new_min=2.200, new_max=77.209
- 跳 / latest10: n=10, old_avg=30.667, new_avg=31.352, avg_delta=0.685, new_min=4.213, new_max=77.209

## 最近样本

- web_20260523_021622_26666615 跳: old=10.536, new=10.536, delta=0.000, mode=semantic_action_window, len=19/30
- web_20260523_021604_9c415199 跳: old=27.034, new=27.034, delta=0.000, mode=semantic_action_window, len=19/60
- web_20260523_021006_aef545ce 跳: old=4.213, new=4.213, delta=0.000, mode=semantic_action_window, len=19/60
- web_20260523_020951_6ff2657c 跳: old=26.374, new=26.374, delta=0.000, mode=semantic_action_window, len=19/60
- web_20260523_020843_6ba8acd9 花: old=40.358, new=65.316, delta=24.958, mode=full_sequence_with_action_window_diagnostics, len=53/60
- web_20260523_020825_2312ad97 花: old=43.861, new=64.029, delta=20.168, mode=full_sequence_with_action_window_diagnostics, len=53/45
- web_20260523_020807_c15e8c2b 花: old=20.273, new=26.297, delta=6.024, mode=full_sequence_with_action_window_diagnostics, len=53/15
- web_20260523_020734_b9299448 花: old=17.864, new=27.613, delta=9.749, mode=full_sequence_with_action_window_diagnostics, len=53/15
- web_20260523_020721_d12639c5 花: old=15.142, new=26.841, delta=11.699, mode=full_sequence_with_action_window_diagnostics, len=53/15
- web_20260523_020656_ffa06ed9 花: old=14.338, new=25.903, delta=11.565, mode=full_sequence_with_action_window_diagnostics, len=53/15
- web_20260523_020555_09843ad1 跳: old=77.209, new=77.209, delta=0.000, mode=semantic_action_window, len=19/19
- web_20260523_015835_2dfac551 花: old=16.105, new=25.759, delta=9.653, mode=full_sequence_with_action_window_diagnostics, len=53/15
- web_20260523_015816_3c06955d 花: old=42.450, new=66.479, delta=24.029, mode=full_sequence_with_action_window_diagnostics, len=53/30
- web_20260523_015755_80a348dd 花: old=47.898, new=63.997, delta=16.099, mode=full_sequence_with_action_window_diagnostics, len=53/30
- web_20260523_015736_2678050f 花: old=44.034, new=69.507, delta=25.473, mode=full_sequence_with_action_window_diagnostics, len=53/30
- web_20260523_015727_2cb1fbe6 跳: old=69.389, new=77.209, delta=7.820, mode=semantic_action_window, len=19/19
- web_20260523_015650_c394e067 跳: old=63.278, new=71.725, delta=8.447, mode=semantic_action_window, len=19/19
- web_20260523_011135_5967dd5a 跳: old=10.315, new=7.192, delta=-3.123, mode=semantic_action_window, len=10/30
- web_20260523_011122_fb34e3e5 跳: old=11.705, new=6.377, delta=-5.328, mode=semantic_action_window, len=10/30
- web_20260523_010234_e2d59e5e 跳: old=6.617, new=5.650, delta=-0.967, mode=semantic_action_window, len=10/45
- web_20260523_010215_ab4961d9 花: old=65.883, new=64.978, delta=-0.905, mode=full_sequence_with_action_window_diagnostics, len=28/30
- web_20260523_010203_88bdaf53 花: old=12.225, new=15.264, delta=3.040, mode=full_sequence_with_action_window_diagnostics, len=28/30
- web_20260523_010014_049faf7d 跳: old=13.658, new=4.753, delta=-8.905, mode=semantic_action_window, len=10/15
- web_20260523_010004_7eaf7ee3 跳: old=6.130, new=5.585, delta=-0.544, mode=semantic_action_window, len=10/15
