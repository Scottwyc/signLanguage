# 手语文本语义权重 profile

- 生成时间：`2026-05-23T00:33:26`
- DOCX：`/data/WYC/signLanguage/data/Demo词汇.docx`
- 模板库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results`
- 口径：文本语义工程权重，不是人工标注校准权重。

## 唱歌

- 说明：头部左右晃动，模仿真实唱歌时的样子；双手拇指和食指同时从喉部两边向外移出，表示；从喉部发出声音；嘴巴张开，模仿唱歌时的样子；画面可以顺着双手拇指和食指的移动，叠加流动的音符
- 允许左右手互换匹配：`True`
- 重点组：`left_hand, right_hand, face, pose`
- 组权重：
  - `left_hand`: `0.2200`
  - `right_hand`: `0.2200`
  - `left_hand_shape`: `0.1200`
  - `right_hand_shape`: `0.1200`
  - `pose`: `0.1000`
  - `face`: `0.1700`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 指示

- 说明：左手拇指模拟人头，右手食指表示另一个人的食指，正在左右指挥前面这个人；画面可以在左手拇指上叠加表情和头发，模拟真的的头
- 允许左右手互换匹配：`True`
- 重点组：`right_hand, right_hand_shape, left_hand`
- 组权重：
  - `left_hand`: `0.2200`
  - `right_hand`: `0.3200`
  - `left_hand_shape`: `0.1200`
  - `right_hand_shape`: `0.1800`
  - `pose`: `0.1100`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 月亮

- 说明：双手向两边移动的过程中，两根手指的距离需要逐渐变窄，模拟弯月两边窄、中间宽的形状；画面可以在双手运动的过程中，出现于两手间出现一轮弯月
- 允许左右手互换匹配：`True`
- 重点组：`left_hand_shape, right_hand_shape, left_hand, right_hand`
- 组权重：
  - `left_hand`: `0.2500`
  - `right_hand`: `0.2500`
  - `left_hand_shape`: `0.2000`
  - `right_hand_shape`: `0.2000`
  - `pose`: `0.0500`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 朋友

- 说明：两根大拇指模拟两个人的头；两个人的头互相碰两下，象征亲密，表示朋友；画面可以在两根拇指上叠加笑脸和头发，模拟人头
- 允许左右手互换匹配：`True`
- 重点组：`left_hand, right_hand, left_hand_shape, right_hand_shape`
- 组权重：
  - `left_hand`: `0.3000`
  - `right_hand`: `0.3000`
  - `left_hand_shape`: `0.1600`
  - `right_hand_shape`: `0.1600`
  - `pose`: `0.0300`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 汽车

- 说明：双手模拟开车的动作，两手虚握，想象手心内是方向盘；双手左右转动，模拟转动方向盘的动作；画面可以叠加一个方向盘，随着双手的转动进行旋转
- 允许左右手互换匹配：`True`
- 重点组：`left_hand, right_hand, left_hand_shape, right_hand_shape`
- 组权重：
  - `left_hand`: `0.2800`
  - `right_hand`: `0.2800`
  - `left_hand_shape`: `0.1600`
  - `right_hand_shape`: `0.1600`
  - `pose`: `0.0700`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 花

- 说明：一手撮合、指尖朝上模仿花朵含苞的样子；手缓缓向上的同时，慢慢张开，模仿开花的样子；画面可以叠加一朵含苞的花朵，随着手张开的动作同时逐渐绽放
- 允许左右手互换匹配：`True`
- 重点组：`right_hand_shape, left_hand_shape, right_hand, left_hand`
- 组权重：
  - `left_hand`: `0.1200`
  - `right_hand`: `0.3200`
  - `left_hand_shape`: `0.1800`
  - `right_hand_shape`: `0.3500`
  - `pose`: `0.0000`
  - `face`: `0.0000`
  - `missing`: `0.0300`
- 语义说明：
  - 重点是一手从撮合/含苞到张开，脸部基本不参与评分。
  - 手指张开由 fingertip spread、tip-to-wrist、finger straightness 等相对特征刻画。

## 虎

- 说明：左手中、无名、小指和右手食指在前额比出一个“王”字，模仿老虎额头上的“王”字花纹；随后双手五指弯曲、指尖朝下，向前下方按动一下，模仿老虎的兽爪，需要坚定有力。；画面上可以在完成第一个动作后，于人物前额生成一个“王”字花纹，并在第二个动作完成的过程中，随着双手动作出现兽爪留痕
- 允许左右手互换匹配：`True`
- 重点组：`left_hand_shape, right_hand_shape, left_hand, right_hand`
- 组权重：
  - `left_hand`: `0.2400`
  - `right_hand`: `0.2400`
  - `left_hand_shape`: `0.1800`
  - `right_hand_shape`: `0.1800`
  - `pose`: `0.0600`
  - `face`: `0.0500`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 谗（羡慕）

- 说明：一手伸食指，熊嘴角处向下滑动，模仿口水从嘴角流出的样子；舌头从嘴巴里微伸出来，模仿馋嘴时舔嘴唇的样子；画面可以顺着向下的食指，叠加从嘴角流出的口水
- 允许左右手互换匹配：`True`
- 重点组：`face, right_hand, left_hand`
- 组权重：
  - `left_hand`: `0.1600`
  - `right_hand`: `0.2400`
  - `left_hand_shape`: `0.0800`
  - `right_hand_shape`: `0.1200`
  - `pose`: `0.0500`
  - `face`: `0.3000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 跳

- 说明：右手两根手指模拟人的两条腿，左手模拟地面；右手食、中指向上弹跳时，要先弯曲后伸直，并且动作较为迅速；画面可以在右手两根手指上叠加一个小人，双腿正好与右手的食指、中指重合，左手位置叠加一块平地，小人双腿随着右手食、中指的状态运动
- 允许左右手互换匹配：`True`
- 重点组：`right_hand_shape, right_hand, left_hand`
- 组权重：
  - `left_hand`: `0.1400`
  - `right_hand`: `0.3400`
  - `left_hand_shape`: `0.1000`
  - `right_hand_shape`: `0.2800`
  - `pose`: `0.0900`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。

## 香蕉

- 说明：左手竖着的食指表示香蕉；右手从左手食指上往下做剥皮动作；画面可以叠加一根真实未剥皮的香蕉，并随着右手的动作，香蕉皮慢慢被剥开
- 允许左右手互换匹配：`True`
- 重点组：`right_hand, left_hand, right_hand_shape, left_hand_shape`
- 组权重：
  - `left_hand`: `0.2400`
  - `right_hand`: `0.3000`
  - `left_hand_shape`: `0.1400`
  - `right_hand_shape`: `0.1600`
  - `pose`: `0.1100`
  - `face`: `0.0000`
  - `missing`: `0.0500`
- 语义说明：
  - 由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。
  - 手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。
