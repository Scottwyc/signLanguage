# 手语文本语义权重 profile

- 生成时间：`2026-06-03T07:36:43`
- DOCX：`/data/WYC/signLanguage/data/Demo词汇.docx`
- 模板库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results`
- 口径：文本语义工程权重，不是人工标注校准权重。

## 唱歌

- 说明：头部左右晃动，模仿真实唱歌时的样子；双手拇指和食指同时从喉部两边向外移出，表示；从喉部发出声音；嘴巴张开，模仿唱歌时的样子；画面可以顺着双手拇指和食指的移动，叠加流动的音符
- 允许左右手互换匹配：`True`
- 重点组：`left_hand, right_hand, face, pose`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.2000`
  - `right_hand`: `0.2000`
  - `left_hand_shape`: `0.1000`
  - `right_hand_shape`: `0.1000`
  - `pose`: `0.1400`
  - `face`: `0.2100`
  - `missing`: `0.0500`
- 语义说明：
  - DOCX 语义同时包含双手从喉部向外移出、头部左右晃动和嘴巴张开。
  - 双手拇指/食指、嘴唇张合、头部/肩部运动都参与主评分；这类词不是纯手势动作。
  - 动态重要帧由双手外移、嘴部开合和头部晃动共同决定。

## 指示

- 说明：左手拇指模拟人头，右手食指表示另一个人的食指，正在左右指挥前面这个人；画面可以在左手拇指上叠加表情和头发，模拟真的的头
- 允许左右手互换匹配：`True`
- 重点组：`right_hand, right_hand_shape, left_hand`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.2400`
  - `right_hand`: `0.3600`
  - `left_hand_shape`: `0.1400`
  - `right_hand_shape`: `0.2100`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - DOCX 语义是左手拇指模拟人头，右手食指左右指挥前面的人。
  - 主语义是右手食指的左右摆动和左手拇指参照；脸、身体和真实头部位置不参与主距离。
  - 动态重要帧主要由右手食指摆动驱动，左手拇指作为手部参照。

## 月亮

- 说明：双手向两边移动的过程中，两根手指的距离需要逐渐变窄，模拟弯月两边窄、中间宽的形状；画面可以在双手运动的过程中，出现于两手间出现一轮弯月
- 允许左右手互换匹配：`True`
- 重点组：`left_hand_shape, right_hand_shape, left_hand, right_hand`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.2400`
  - `right_hand`: `0.2400`
  - `left_hand_shape`: `0.2400`
  - `right_hand_shape`: `0.2400`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0400`
- 语义说明：
  - DOCX 语义是双手向两边移动时，两根手指距离逐渐变窄，形成弯月形状。
  - 主语义是双手相对运动和指间形状变化；脸、身体和手-躯干关系不参与主距离。
  - 动态重要帧由双手分离过程和双手手指间距变化驱动。

## 朋友

- 说明：两根大拇指模拟两个人的头；两个人的头互相碰两下，象征亲密，表示朋友；画面可以在两根拇指上叠加笑脸和头发，模拟人头
- 允许左右手互换匹配：`True`
- 重点组：`left_hand, right_hand, left_hand_shape, right_hand_shape`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.3000`
  - `right_hand`: `0.3000`
  - `left_hand_shape`: `0.1700`
  - `right_hand_shape`: `0.1700`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0600`
- 语义说明：
  - DOCX 语义是两根大拇指模拟两个人的头，并互相碰两下表示亲密。
  - 主语义是左右拇指位置、碰撞节奏和双手相对运动；脸和躯干不参与主距离。
  - 动态重要帧由两拇指靠近/接触的重复动作驱动。

## 汽车

- 说明：双手模拟开车的动作，两手虚握，想象手心内是方向盘；双手左右转动，模拟转动方向盘的动作；画面可以叠加一个方向盘，随着双手的转动进行旋转
- 允许左右手互换匹配：`True`
- 重点组：`left_hand, right_hand, left_hand_shape, right_hand_shape`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.3000`
  - `right_hand`: `0.3000`
  - `left_hand_shape`: `0.1700`
  - `right_hand_shape`: `0.1700`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0600`
- 语义说明：
  - DOCX 语义是双手虚握并左右转动方向盘；评分只看双手位置、手形和双手协同转动。
  - 脸、嘴和躯干相对位置不参与主距离。
  - 动态重要帧由双手同步旋转/转向动作驱动。

## 花

- 说明：一手撮合、指尖朝上模仿花朵含苞的样子；手缓缓向上的同时，慢慢张开，模仿开花的样子；画面可以叠加一朵含苞的花朵，随着手张开的动作同时逐渐绽放
- 允许左右手互换匹配：`True`
- 重点组：`right_hand_shape, right_hand`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.020`, `anchor_penalty_weight=0.110`, `phase_order_guard=True`, `phase_order_disorder_span=0.400`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.0800`
  - `right_hand`: `0.3400`
  - `left_hand_shape`: `0.1000`
  - `right_hand_shape`: `0.4400`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0400`
- 语义说明：
  - DOCX 语义是一手撮合/含苞并缓慢张开；评分只看主手手形和主手运动。
  - 脸、身体、主手相对躯干位置不参与主距离；另一只手只作为手势完整性约束，用于惩罚额外双手动作。
  - 允许左右手互换：用户用左手或右手完成时，都映射到模板主手。
  - 动态重要帧由主手 opening/spread、指尖相对腕部距离和手指伸直度驱动。

## 虎

- 说明：左手中、无名、小指和右手食指在前额比出一个“王”字，模仿老虎额头上的“王”字花纹；随后双手五指弯曲、指尖朝下，向前下方按动一下，模仿老虎的兽爪，需要坚定有力。；画面上可以在完成第一个动作后，于人物前额生成一个“王”字花纹，并在第二个动作完成的过程中，随着双手动作出现兽爪留痕
- 允许左右手互换匹配：`True`
- 重点组：`left_hand_shape, right_hand_shape, left_hand, right_hand`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.2400`
  - `right_hand`: `0.2400`
  - `left_hand_shape`: `0.2000`
  - `right_hand_shape`: `0.2000`
  - `pose`: `0.0300`
  - `face`: `0.0400`
  - `missing`: `0.0500`
- 语义说明：
  - DOCX 语义包含两段：先在前额比出“王”字，再双手五指弯曲向前下方按动模拟兽爪。
  - 主语义是双手手形和兽爪按动；额头位置只作小权重定位参照，不让脸/躯干主导评分。
  - 动态重要帧由双手从王字过渡到兽爪按动、五指弯曲开合变化驱动。

## 谗（羡慕）

- 说明：一手伸食指，熊嘴角处向下滑动，模仿口水从嘴角流出的样子；舌头从嘴巴里微伸出来，模仿馋嘴时舔嘴唇的样子；画面可以顺着向下的食指，叠加从嘴角流出的口水
- 允许左右手互换匹配：`True`
- 重点组：`face, right_hand, right_hand_shape`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.1000`
  - `right_hand`: `0.2400`
  - `left_hand_shape`: `0.0500`
  - `right_hand_shape`: `0.1200`
  - `pose`: `0.0000`
  - `face`: `0.4400`
  - `missing`: `0.0500`
- 语义说明：
  - DOCX 语义是食指从嘴角向下滑动模拟口水，同时舌头/嘴巴表现馋嘴。
  - 脸部嘴唇/嘴角是主语义之一，手部食指下滑是另一主语义；躯干不参与主距离。
  - 保留少量非主手约束，用于惩罚额外双手动作；动态帧由嘴部和食指下滑共同驱动。

## 跳

- 说明：右手两根手指模拟人的两条腿，左手模拟地面；右手食、中指向上弹跳时，要先弯曲后伸直，并且动作较为迅速；画面可以在右手两根手指上叠加一个小人，双腿正好与右手的食指、中指重合，左手位置叠加一块平地，小人双腿随着右手食、中指的状态运动
- 允许左右手互换匹配：`True`
- 重点组：`two_hand_relation, right_hand_shape, right_hand, left_hand`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.016`, `anchor_penalty_weight=0.090`, `phase_order_guard=True`, `phase_order_disorder_span=0.600`, `phase_order_adjacent_span=0.250`
- 组权重：
  - `left_hand`: `0.2136`
  - `right_hand`: `0.2991`
  - `left_hand_shape`: `0.1068`
  - `right_hand_shape`: `0.3205`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0600`
- 语义说明：
  - DOCX 语义是右手食指/中指模拟两条腿，先弯曲后伸直并向上弹跳；评分主导项是右手两指手形动态。
  - 左手模拟地面，必须进入评分；单手动作缺少左手地面或双手相对关系时应明显扣分。
  - 脸、躯干和手-躯干相对位置不参与主距离，核心是右手在左手基础上的相对跳跃。
  - 动态重要帧主要由 two_hand_relation、跳跃手食指/中指相对运动和弯曲-伸直变化驱动。

## 香蕉

- 说明：左手竖着的食指表示香蕉；右手从左手食指上往下做剥皮动作；画面可以叠加一根真实未剥皮的香蕉，并随着右手的动作，香蕉皮慢慢被剥开
- 允许左右手互换匹配：`True`
- 重点组：`right_hand, left_hand, right_hand_shape, left_hand_shape`
- 语义相位 DTW：`enabled=True`, `local_phase_weight=0.018`, `anchor_penalty_weight=0.100`, `phase_order_guard=False`, `phase_order_disorder_span=0.000`, `phase_order_adjacent_span=0.000`
- 组权重：
  - `left_hand`: `0.2600`
  - `right_hand`: `0.3400`
  - `left_hand_shape`: `0.1500`
  - `right_hand_shape`: `0.2000`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - DOCX 语义是左手竖食指表示香蕉，右手沿左手食指向下做剥皮动作。
  - 主语义是左手食指稳定参照和右手剥皮轨迹；脸、身体和手-躯干关系不参与主距离。
  - 动态重要帧主要由右手沿左手食指下滑/剥开的相对运动驱动。
