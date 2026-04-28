# 手语资料结构化盘点报告

- 生成时间：2026-04-28T23:11:23
- 视频数量：10
- 输出目录：/data/WYC/signLanguage/work/generated/sign_data_profile

## 量化指标模板

### hand
- `left_hand_presence_ratio`: 左手在样本中被成功检测到的帧占比
- `right_hand_presence_ratio`: 右手在样本中被成功检测到的帧占比
- `hand_visibility_mean`: 双手可见度均值
- `hand_motion_energy`: 相邻帧手部位移能量
- `left_right_symmetry_score`: 左右手运动对称性

### body
- `pose_presence_ratio`: 人体骨架成功检测到的帧占比
- `pose_visibility_mean`: 躯干和四肢关键点可见度均值
- `pose_motion_energy`: 相邻帧身体位移能量
- `upper_body_span_ratio`: 上半身关键点覆盖范围归一化比例

### face
- `face_presence_ratio`: 人脸成功检测到的帧占比
- `face_visibility_mean`: 面部关键点可见度均值
- `mouth_activity_score`: 嘴部活动强度
- `eyebrow_activity_score`: 眉眼区域活动强度

### temporal
- `sampled_frame_count`: 采样帧数
- `effective_span_sec`: 有效动作跨度（秒）
- `motion_peak_count`: 运动峰值数量
- `motion_smoothness`: 动作平滑度
- `coverage_stability`: 关键点覆盖稳定性

## 资料样本清单

### 1. 唱歌.mp4
- DOCX片段：左手竖着的食指表示香蕉；右手从左手食指上往下做剥皮动作；画面可以叠加一根真实未剥皮的香蕉，并随着右手的动作，香蕉皮慢慢被剥开
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/唱歌.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/唱歌.mp4", "name": "唱歌.mp4", "stem": "唱歌", "suffix": ".mp4", "size_bytes": 82916, "mtime": 1777372590.631236, "probe_backend": "ffprobe", "duration_sec": 2.12, "fps": 25.0, "frame_count": 53, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 2. 指示.mp4
- DOCX片段：一手撮合、指尖朝上模仿花朵含苞的样子；手缓缓向上的同时，慢慢张开，模仿开花的样子；画面可以叠加一朵含苞的花朵，随着手张开的动作同时逐渐绽放
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/指示.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/指示.mp4", "name": "指示.mp4", "stem": "指示", "suffix": ".mp4", "size_bytes": 56851, "mtime": 1777372590.6122367, "probe_backend": "ffprobe", "duration_sec": 2.645, "fps": 22.3062381852552, "frame_count": 59, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 3. 月亮.mp4
- DOCX片段：双手模拟开车的动作，两手虚握，想象手心内是方向盘；双手左右转动，模拟转动方向盘的动作；画面可以叠加一个方向盘，随着双手的转动进行旋转
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/月亮.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/月亮.mp4", "name": "月亮.mp4", "stem": "月亮", "suffix": ".mp4", "size_bytes": 96742, "mtime": 1777372590.5942373, "probe_backend": "ffprobe", "duration_sec": 3.72, "fps": 25.0, "frame_count": 93, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 4. 朋友.mp4
- DOCX片段：左手中、无名、小指和右手食指在前额比出一个“王”字，模仿老虎额头上的“王”字花纹；随后双手五指弯曲、指尖朝下，向前下方按动一下，模仿老虎的兽爪，需要坚定有力。；画面上可以在完成第一个动作后，于人物前额生成一个“王”字花纹，并在第二个动作完成的过程中，随着双手动作出现兽爪留痕
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/朋友.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/朋友.mp4", "name": "朋友.mp4", "stem": "朋友", "suffix": ".mp4", "size_bytes": 50174, "mtime": 1777372590.573238, "probe_backend": "ffprobe", "duration_sec": 2.16, "fps": 25.0, "frame_count": 54, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 5. 汽车.mp4
- DOCX片段：双手向两边移动的过程中，两根手指的距离需要逐渐变窄，模拟弯月两边窄、中间宽的形状；画面可以在双手运动的过程中，出现于两手间出现一轮弯月
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/汽车.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/汽车.mp4", "name": "汽车.mp4", "stem": "汽车", "suffix": ".mp4", "size_bytes": 101259, "mtime": 1777372590.5552385, "probe_backend": "ffprobe", "duration_sec": 3.3, "fps": 26.363636363636363, "frame_count": 87, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 6. 花.mp4
- DOCX片段：右手两根手指模拟人的两条腿，左手模拟地面；右手食、中指向上弹跳时，要先弯曲后伸直，并且动作较为迅速；画面可以在右手两根手指上叠加一个小人，双腿正好与右手的食指、中指重合，左手位置叠加一块平地，小人双腿随着右手食、中指的状态运动
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/花.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/花.mp4", "name": "花.mp4", "stem": "花", "suffix": ".mp4", "size_bytes": 87512, "mtime": 1777372590.5332391, "probe_backend": "ffprobe", "duration_sec": 3.633333, "fps": 29.44954128440367, "frame_count": 107, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 7. 虎.mp4
- DOCX片段：两根大拇指模拟两个人的头；两个人的头互相碰两下，象征亲密，表示朋友；画面可以在两根拇指上叠加笑脸和头发，模拟人头
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/虎.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/虎.mp4", "name": "虎.mp4", "stem": "虎", "suffix": ".mp4", "size_bytes": 144112, "mtime": 1777372590.5032399, "probe_backend": "ffprobe", "duration_sec": 3.9, "fps": 28.205128205128204, "frame_count": 110, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 8. 谗（羡慕）.mp4
- DOCX片段：左手拇指模拟人头，右手食指表示另一个人的食指，正在左右指挥前面这个人；画面可以在左手拇指上叠加表情和头发，模拟真的的头
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/谗（羡慕）.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/谗（羡慕）.mp4", "name": "谗（羡慕）.mp4", "stem": "谗（羡慕）", "suffix": ".mp4", "size_bytes": 74757, "mtime": 1777372590.467241, "probe_backend": "ffprobe", "duration_sec": 2.333333, "fps": 26.571428571428573, "frame_count": 62, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 9. 跳.mp4
- DOCX片段：头部左右晃动，模仿真实唱歌时的样子；双手拇指和食指同时从喉部两边向外移出，表示；从喉部发出声音
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/跳.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/跳.mp4", "name": "跳.mp4", "stem": "跳", "suffix": ".mp4", "size_bytes": 46091, "mtime": 1777372590.439242, "probe_backend": "ffprobe", "duration_sec": 2.52, "fps": 14.682539682539682, "frame_count": 37, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}

### 10. 香蕉.mp4
- DOCX片段：一手伸食指，熊嘴角处向下滑动，模仿口水从嘴角流出的样子；舌头从嘴巴里微伸出来，模仿馋嘴时舔嘴唇的样子；画面可以顺着向下的食指，叠加从嘴角流出的口水
- 视频路径：/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/香蕉.mp4
- 视频元数据：{"path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/香蕉.mp4", "name": "香蕉.mp4", "stem": "香蕉", "suffix": ".mp4", "size_bytes": 76530, "mtime": 1777372590.4122427, "probe_backend": "ffprobe", "duration_sec": 3.2, "fps": 25.625, "frame_count": 82, "width": 592, "height": 1280, "codec_name": "hevc", "pix_fmt": "yuv420p"}
