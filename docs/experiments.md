# ManiMux 实验登记：Settings 与逐任务结果

> 2026-09-28 · v0.1 草案。Pi05 抓瓶子 RTC 最小执行步数已确认 12；完整 setting 尚未冻结，未写回运行 YAML，未新增实测结果。
> 本文是当前实验的登记入口；[研究设计](reference/experiment-design.md)解释对照原则，[实验设施](reference/experiment-infra.md)说明操作和数据格式。

## 1. 本轮范围与记录方式

- **先在抓瓶子任务确定 Serial / RTC setting；Pi05 增加丢硬币任务。SAPolicy 不进入本轮。**
- 一个 task 一张主结果表。同一模型主行用 **Serial**，下面用 **+ RTC / + ManiMux / + PAINT** 等子行；子行表示替换推理方法，复用同一 checkpoint。
- 表中 `—` 表示未测或缺失，不能当成 0。部署入口待绑定不代表没有训练好；有入口也不代表已通过真机实验。
- 本文维护任务、setting 决定、结果及证据链接；**运行值仍由已有 experiment / policy / inference / executor YAML 持有**，公共参数沿用 `config:` 引用。
- 每个最终 setting 使用唯一 ID，绑定 task、policy、本体、checkpoint、动作表示和算法。确认后填配置路径及版本；每轮实际采用值以该 session 的 resolved config 和 backend identity 核对。
- 顺序：**核对现值 → 确定 Serial / RTC 候选 → 写入匹配 YAML → dev 验证 → 冻结 setting → test → 回填同一张表**。调参记录与正式 test 结果分开。

## 2. 主表列定义

一个 task 一张结果表，横向只放 **模型/推理方法、Human、Chunk seam、PRM 指标**。共同 setting、10 个布局 × 3 次的评测预算和输出路径统一写在表外，不再添加 N_task 或 Setting 列。以下是报告格式草案，评测口径随 setting 一起冻结。

| 分组 | 列 | 定义与报告方式 |
|---|---|---|
| Human | H-SR ↑ | `success / (success + failure)`，填 `n/N (%)`；任务判据先冻结 |
| Chunk seam | L-Mean / L-P95 / L-Max；R-Mean / R-P95 / R-Max ↓ | 左右手各三列，独立计算，单位 mm；Mean 与 P95 按 episode 等权汇总，Max 分别保留该手最坏交接 |
| PRM | M25 / M50 / M75 / SR / MP / PPL / CRA / STR / DRR / FNS / SQS | 全部 11 项横向列入各 task 主表；定义与适用样本见 §2.2 |

**跳变口径：**比较“新 committed plan 首点”与“旧 committed plan 在新 plan 起始时刻的采样值”，经同一本体 FK 转为末端位置，计算欧氏距离。它是**参考轨迹接缝**，不称为实测机械臂瞬时跳变。

**三项统计：**每条 rollout 的左右臂分别计算有效交接值的 Mean、P95 和 Max。P95 是第 95 百分位数（采用线性插值），不是 95% 置信区间。主表 Mean/P95 分别对各 rollout 的 Mean/P95 等权平均；主表 Max 取本组全部有效交接中的最大值，同时在明细记录对应 rollout 和边界。主表 P95 因此表示“每条 rollout 的 P95 的均值”，不把长 rollout 的更多交接当成更多独立实验；三列使用相同有效边界集，无有效值填 `—`。

报告前必须检查连续运行段、实际接手边界和旧计划是否耗尽。Serial 等待期间的末点 hold 单独标记，不与 RTC 有重叠的交接混称；没有有效边界填 `—`。现有画图脚本提供逐交接字段，统一跨算法有效性筛选和聚合仍需补齐。

任务、seam、PRM 的有效样本可能不同，证据中分别列 `N_task / N_seam / N_prm`。录像故障不自动抹掉已有人工任务结论；空 PRM 曲线不填零分。PRM 的模型版本、视角、采样时间、prompt、goal/reference 和后处理必须固定。全部 11 项 PRM 指标进入主表；M25/M50/M75/SR 用百分数，其他量保留无量纲小数。

有数据后报告区间：SR 报二项比例区间；连续量按 matched layout/block 重采样，避免把同一 rollout 的接缝或 control ticks 当成独立实验。暂不预设最优数字，不加粗空格或缺失值。

来源：[人工标签](../manimux/evaluation/manual.py)、[交接分析](../scripts/validation/plot_chunk_handoffs.py)、[PRM 指标](../PRM-as-a-Judge/eval/prm_judge/metrics.py)。

### 2.1 跳变分析：现有计算与出图

现有脚本直接计算每次候选交接的 `left_position_seam_mm`、`right_position_seam_mm`，并保存 chunk/request 编号、切换时刻和裁剪信息。主表的 Mean/P95/Max 需要按上述有效边界规则另行汇总；画图脚本本身尚未输出这些汇总值。当前不计算姿态角、速度、加速度或 jerk 接缝。

- **逐交接图** `chunk-00-to-01-eef-xyz.png`：左右臂 XYZ 共 6 子图，对照旧/新 chunk，标出切换线、过期前缀、重叠区域与 committed 接缝点。
- **总览图** `rollout-<label>-all-handoffs-overview[-NN].png`：每页最多 12 次交接。
- **多页 PDF** `rollout-<label>-all-handoffs.pdf`：收集全部逐交接图。
- **数值明细** `handoff-summary.csv` / `.json`：每次候选交接一条，供筛选、聚合及回溯。

另有 [终端诊断脚本](../scripts/validation/analyze_chunk_boundaries.py)，检查重规划间隔、跟踪差、chunk 首点相对上一 command 的差、blend 改变量及反向/回拉率。它不是上述末端位置接缝的统计器，不出图、不进主表；不能把其混合 group 的数值直接当成纯关节 rad 指标。

### 2.2 PRM：完整输出与主表取值

PRM 生成**按时间采样的原始/处理后进度曲线**，不是自动命名“抓取/搬运/放置”等语义阶段。当前工具的模型汇总有以下 11 项无量纲指标；阈值、采样与后处理尚需随 judge profile 冻结。

| 字段 | 含义 | 当前主表 |
|---|---|---|
| M25 / M50 / M75 ↑ | 达到 25% / 50% / 75% 最大预测进度的 episode 比例 | 已列入 |
| SR ↑ | 按进度阈值或指定标签汇总的成功率；默认进度阈值 0.99 | 已列入 PRM SR；不能替代 Human SR |
| MP ↑ | 最大预测进度；主表对有效 episode 等权平均 | **PRM MP** |
| PPL ↑ | 进度路径效率，`MP² / Σabs(Δprogress)` | 已列入 |
| CRA ↓ | 相对历史最高进度的平均回退损失，按 MP 归一化 | 已列入 |
| STR ↓ | 相邻采样进度变化小于阈值的比例，默认阈值 0.005 | 已列入 |
| DRR ↑ | 最大回退之后恢复了多少；汇总仅计发生真实回退的 episode | 已列入 |
| FNS ↑ | 失败样本距成功的接近程度；汇总仅计失败 episode | 已列入 |
| SQS ↑ | 由效率、回退与停滞合成的成功质量；汇总仅计成功 episode | 已列入 |

DRR/FNS/SQS 的样本集合不同，需同时保存各自 N。SR、FNS、SQS 的成功分类受 `success_source` 影响；缺失标签可能回退到进度阈值，不能据此补造人工结论。

回填时仅聚合该行明确选定的 task、setting、dev/test cohort；PRM manifest 的 `model` 分组键须区分不同模型与推理 setting。可读 `run_summary.json.metrics.groups` 中匹配该 task/setting 的组，不直接照搬可能跨 task 汇总的 leaderboard 或 Excel Model_Mean。FNS/SQS 由 `trace_summary` 派生，并不在普通逐 case `metrics` 中；`success_source=label` 时也不能照搬其中按阈值计算的 `metrics.SR`。没有适用样本的条件指标填 `—` 并记录 N=0，不照搬工具的零值。

- **数值/证据**：`per_case.jsonl`、每 case 的 `result_summary.json`、Dopamine 的 `pred_vllm.json`，以及 `run_params.json`、`discovery_manifest.json`、`run_summary.json`、`metrics.xlsx`、`report.md`。
- **启用可视化时**：Dopamine 的 `reward_vis.mp4` 展示视频与 progress/hop；`visualizations/cases/*.png` 对照原始/处理后进度曲线和成功阈值；`visualizations/report.html` 提供视频/曲线联动、指标与里程碑、回退恢复等图表；另有 CSV 索引及可视化 Markdown。PNG 依赖 matplotlib，生成失败须记录。
- **表格覆盖**：每 task 主表横向列出 Human SR、Mean/P95/Max 接缝和全部 11 项 PRM 指标；原始数据、逐 episode 明细和图在表外的路径登记中链接。当前没有新评测结果，主表仍为 `—`。

## 3. 逐任务结果表

表头简写：**H-SR** 为人工成功率，**P-SR** 为 PRM 成功率；H-SR、P-SR、M25/M50/M75 单位为 %。**L-Mean / L-P95 / L-Max** 为左手，**R-Mean / R-P95 / R-Max** 为右手，六列独立填写，单位 mm；后面的 M25 至 SQS 均为 PRM 指标。每个 task 的共同实验条件、样本数和证据在表外统一登记。

### Table 1. 抓瓶子放入箱子 · YAM · 首轮主任务

共同实验条件见 §4–5；每个模型 × 方法 10 个固定布局 × 每布局 3 次，共 30 条。进度见 §8，输出路径见 §9。

任务标识：`put_bottles`；指令：`Put the bottles into the bin.`。先确定瓶子数量、初始区域、箱子位置、完成判据、时间预算和 dev/test 布局。建议完成判据为“指定瓶子全部留在目标箱内”，数量及终态保持要求待确认。

| Model | H-SR ↑ | L-Mean ↓ | L-P95 ↓ | L-Max ↓ | R-Mean ↓ | R-P95 ↓ | R-Max ↓ | M25 ↑ | M50 ↑ | M75 ↑ | P-SR ↑ | MP ↑ | PPL ↑ | CRA ↓ | STR ↓ | DRR ↑ | FNS ↑ | SQS ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Pi05 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + ManiMux | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + PAINT | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **XR1 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + ManiMux | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **LingBot-VLA2 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **OpenWAM · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + ManiMux | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **DP · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + ManiMux | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

`+ ManiMux` 指现有普通异步调度，不能与 Serial 混为一个 baseline。OpenWAM / DP 当前接入未提供 RTC sampler hook，因此没有预填 RTC 结果行；未来实现后再增补。

Pi05 主组暂选 Joint 30k；Joint+EE 训练后 Joint 输出、同 checkpoint 的 EEF 输出应另加具名动作表示对照，不能合并进上述 Pi05 主组。现有 PAINT 瓶子入口使用 15k，不能直接作为 30k 的 `+ PAINT` 结果。

### Table 2. 丢硬币 · YAM · Pi05 补充任务

本 task 统一实验条件；每个模型 × 方法 10 个固定布局 × 每布局 3 次，共 30 条；具体布局和共同条件待冻结；输出路径见 §9。

已有 Pi05 coin 50k 产物和离线推理记录；当前没有对应 ManiMux task recipe / experiment。离线记录的 prompt 是 `put_the_coin_into_the_bin`，正式指令、投放目标、起始状态和成功判据待确认；不从口语“丢”推断必须抛掷。

| Model | H-SR ↑ | L-Mean ↓ | L-P95 ↓ | L-Max ↓ | R-Mean ↓ | R-P95 ↓ | R-Max ↓ | M25 ↑ | M50 ↑ | M75 ↑ | P-SR ↑ | MP ↑ | PPL ↑ | CRA ↓ | STR ↓ | DRR ↑ | FNS ↑ | SQS ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Pi05 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + ManiMux | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + PAINT | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

先在瓶子 dev 布局选定 Pi05 推理 preset，再核对 coin checkpoint 的动作/时间约定。相同约定可复用该 preset；不能在 coin test 上重新挑参数。必须改动时记录新版本及原因，并单列实验。

### Table 3. 组装螺丝刀 · YAM · 后续预留

本 task 统一实验条件；每个模型 × 方法 10 个固定布局 × 每布局 3 次，共 30 条；具体布局和共同条件待冻结；输出路径见 §9。

已有 15k recipe / RTC 入口；当前不启动该任务。各模型的专用 Serial 入口、task rubric 和预算待绑定。

| Model | H-SR ↑ | L-Mean ↓ | L-P95 ↓ | L-Max ↓ | R-Mean ↓ | R-P95 ↓ | R-Max ↓ | M25 ↑ | M50 ↑ | M75 ↑ | P-SR ↑ | MP ↑ | PPL ↑ | CRA ↓ | STR ↓ | DRR ↑ | FNS ↑ | SQS ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Pi05 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **XR1 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **LingBot-VLA2 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Table 4. 传球 · Tianji · 后续预留

本 task 统一实验条件；每个模型 × 方法 10 个固定布局 × 每布局 3 次，共 30 条；具体布局和共同条件待冻结；输出路径见 §9。

独立本体 setting，不套用 YAM 的控制包络；UMI-DP / XR1 的模型和任务条件须分别核对。XR1 × Tianji 当前 adapter 明确不接收 RTC condition，不预填其 RTC 结果行。

| Model | H-SR ↑ | L-Mean ↓ | L-P95 ↓ | L-Max ↓ | R-Mean ↓ | R-P95 ↓ | R-Max ↓ | M25 ↑ | M50 ↑ | M75 ↑ | P-SR ↑ | MP ↑ | PPL ↑ | CRA ↓ | STR ↓ | DRR ↑ | FNS ↑ | SQS ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **UMI-DP · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **XR1 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Table 5. 红球放入盒子 · YAM · 历史任务预留

本 task 统一实验条件；每个模型 × 方法 10 个固定布局 × 每布局 3 次，共 30 条；具体布局和共同条件待冻结；输出路径见 §9。

只登记匹配红球任务的 Pi05 1k；`pick_red_object` 目录还包含其他物体/指令，不把目录里的所有实验自动汇总为同一 task。

| Model | H-SR ↑ | L-Mean ↓ | L-P95 ↓ | L-Max ↓ | R-Mean ↓ | R-P95 ↓ | R-Max ↓ | M25 ↑ | M50 ↑ | M75 ↑ | P-SR ↑ | MP ↑ | PPL ↑ | CRA ↓ | STR ↓ | DRR ↑ | FNS ↑ | SQS ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Pi05 · Serial** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| + RTC | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## 4. 抓瓶子：模型身份与当前入口

本节是 2026-09-28 的配置/产物清点，不是新推理验收。训练完成依据用户确认；所列本地文件及配置本轮仅只读查看，未重新校验全部权重 hash。

| 模型组 | 产物 / recipe | H；动作间隔 | 推理步数现值 | 当前缺口 |
|---|---|---|---|---|
| Pi05 Joint 30k | [joint-step30000](../manimux/configs/policy/pi05/yam/put-bottles/joint-step30000.yaml) | 50；1/30 s | 10 | Serial / RTC 控制设置不一致，见下一节 |
| XR1 EE 30k | [finetune-put-bottles-step30000](../manimux/configs/policy/xiaomi-xr1/yam/finetune-put-bottles-step30000.yaml) | 30；1/30 s | 5；模型当前也固定 5 | 瓶子 Serial 入口待绑定 |
| LingBot-VLA2 30k | `checkpoints/finetuned/ziyang/lingbot-vla2-put-bottles-b64-step30000` | 模型 chunk_size=50；训练 30 FPS | 产物 config 为 10，部署生效值待绑定 | 产物已存在；瓶子 recipe / experiment 待绑定 |
| OpenWAM 30k | [finetune-put-bottles-step30000](../manimux/configs/policy/openwam/yam/finetune-put-bottles-step30000.yaml) | 32；1/30 s | 待核对 effective sampler | Serial 当前额外 blend=8，尚未统一 |
| DP EEF 100k | [eef-step100000](../manimux/configs/policy/dp/yam/put-bottles/eef-step100000.yaml) | 输出 6；1/30 s | 待核对 checkpoint 内嵌 cfg | Serial 当前 K=6，不可强行改成超出输出的 12 |

Pi05 coin 产物：`checkpoints/finetuned/pi05/pi05_coin_20260928_v2_w32/50000`。已有离线记录为 H=50、denoise=10、14D absolute joint/gripper；训练采样 30 Hz。正式部署 recipe、动作转换和 dt 仍需绑定，本次未复验模型。

**对齐规则：**同一模型的 Serial / RTC 必须使用同一 checkpoint、normalization、模型输入、H、动作 dt 和实际推理步数。跨模型保留训练约定，单列原生 H/步数与计算成本；Pi05 10 步、XR1 5 步目前不能声称全模型推理预算已对齐。等步数/等算力对照另行确认，不能只改 YAML 的声明值。

配对实验还需固定推理设备、精度、batch 和服务负载，记录预热、随机种子以及实测 latency / model evaluations。相同 denoising 步数也不保证 RTC 与 Serial 的计算开销相同。

## 5. 第一张 setting 卡：Pi05 抓瓶子 Serial / RTC

来源：[Serial 30k](../manimux/configs/experiments/put_bottles/pi05/yam_pi05_serial_joint_step30000.yaml)、[RTC 30k](../manimux/configs/experiments/put_bottles/pi05/yam_pi05_rtc_joint_step30000.yaml)、[Serial preset](../manimux/configs/inference/yam_serial_chunk12.yaml)、[RTC preset](../manimux/configs/inference/yam_rtc.yaml)。

**下表逐项标记确认状态；确认决定不等于 YAML 已更新或已通过实测。**候选 ID 为 `B-P05-S-v0` / `B-P05-R-v0`，先用于 dev，不进入正式结果。

| 参数 | 当前 Serial | 当前 RTC | 首轮建议 / 理由 |
|---|---|---|---|
| checkpoint / norm stats / 输入 | Joint 30k；三路 D405 | 相同 | 保持相同；冻结确切 task prompt 和相机映射 |
| `policy.action_dt_s`；H；`num_steps` | 1/30 s；50；10 | 相同 | 两者保持；不通过动作时间缩放调快机器人 |
| `robot.control_hz` | 100 Hz | 30 Hz | **两者 100 Hz**，消除控制频率差异 |
| executor | `yam_smooth_standard` | `yam_smooth_control_profile` + `yam_control` | **两者采用 standard 的共同有限限制**，并配套兼容的 control profile；当前 RTC 的 arm 速度/加速度为 null |
| arm 速度 / 加速度限制 | 0.25 rad/s；0.5 rad/s² | null；null | 两者复用 standard 的完整参数，含滤波和 gripper 限制 |
| `run.max_control_steps` | 12000 | 12000 | 待定任务时间预算；当前分别对应名义 120 s / 400 s，不能视为同样时长 |
| 调度 | `algorithm=manimux`，`inference_schedule=serial` | `algorithm=rtc` | 保留方法差异；Serial 等旧前缀结束后才请求，RTC 与旧计划执行重叠 |
| Serial `chunk_policy_steps` | 12 | 不作为固定执行长度 | **Serial K=12** 为首个候选，不截短模型输出 H |
| RTC `min_execute_policy_steps` | 不适用 | 12，经 `chunk_policy_steps` 别名映射 | **RTC s_min=12，用户已确认**；后续显式写 RTC 字段，含义见下一节 |
| RTC `initial_delay_policy_steps` | 不适用 | 4 | 初始候选保留 4；随后由实际已接受计划的延迟更新 |
| RTC `delay_buffer_size` | 不适用 | 10 | 初始候选保留 10 |
| RTC `beta` | 不适用 | 9.1 | **建议首轮改用原论文 β=5，待确认**；替代上一版“先保留 9.1”的建议，尚未改 YAML |
| `blend_policy_steps` | 0 | 4 | **两者 0**，先单独考察 Serial / RTC；额外 blending 后续单列消融 |
| `action_start_mode` | `first_step_when_ready` | `skip_elapsed_steps` | 保留各自方法语义，不能为表面一致改成同一个值 |
| `commit_lead_s`；`max_plan_age_s` | 0；2 s | 0；2 s | 两者保持 |
| 请求 deadline / WS RPC 超时 | 2 s / 10 s | 相同 | 保持；deadline 按 worker 响应完成时刻检查，不表示自动终止远端计算 |
| 初始状态 / 录像 | 零位、夹爪开；30 FPS | 相同 | 冻结相同初始状态、摆放参考图和录像配置；视频时间以记录 timestamp 为准 |

没有将 12000 ticks 等同严格 wall-clock timeout；每方法数量现已明确为 10 个布局 × 3 次 = 30 条；正式时间规则、具体 dev/test 布局、人工 rubric 和 PRM profile 仍待确定。先完成上面的算法对照 setting，再冻结这些任务项。

配置落地时必须一并处理 control profile：当前 RTC 的 `yam_control` 会注入 null motion limits，**只替换 executor YAML 会与 standard 的有限值冲突并被 loader 拒绝**。共同 profile / executor 组合待确认，见 [配置合并与冲突检查](../manimux/cli.py)。

Serial 对 RTC 比较的是整个推理执行方案，包含调度和条件采样两部分变化。若要单独归因于 RTC conditioning，后续增加同执行条件的异步无 conditioning 对照，即主表中的 `+ ManiMux`。

## 6. RTC 到底能调哪些参数？

**Pi05 执行阈值已确认 12；β 建议先采用论文值 5，不必一开始逐模型搜索。**初始延迟和统计窗口先记录并固定。H、动作间隔、推理步数以及 executor 不是本轮可以随 RTC 单独改变的自由项。

| 参数 | 控制什么 | 本轮处理 |
|---|---|---|
| `inference.rtc.min_execute_policy_steps` | 下一次推理的源 chunk 执行索引阈值；影响更新时机与重叠长度 | Pi05 已确认 12；XR1 当前 15，处理其 setting 时再同步确认 |
| `inference.rtc.beta` | sampler 的条件引导强度参数；Pi05 中是时变 guidance scale 的上限，不是轨迹混合比例 | 当前 Pi05 9.1、XR1 4.25；首轮建议统一以论文值 5 为起点，待确认 |
| `inference.rtc.initial_delay_policy_steps` | 新 rollout 延迟窗口的初始样本；不是人为增加推理延迟，也不是永久下限 | Pi05 4，XR1 8；后续根据端到端延迟证据确认 |
| `inference.rtc.delay_buffer_size` | 保留多少个已接受计划的延迟样本，预测取窗口最大值 | 当前两者 10；窗口越长，历史慢响应影响持续越久 |

所有步数单位为 **policy action step**，不是控制 tick，也不是 denoising iteration。30 Hz 下 12 个 step 的名义时间为 0.4 s；不能据此声称 RTC 每 0.4 s 固定切换一次。

额外 blending、commit lead 和计划有效期也会影响结果，已在 §5 单列。普通调度的 `refill_threshold_s` / `inference_schedule` 不控制 RTC 请求时机，不能列作 RTC 的调参旋钮。

### “最小步数”的准确含义

令 H 为源输出 horizon，d 为当前延迟窗口最大值，m 为 `min_execute_policy_steps`：

```text
m 未指定时：m = max(1, floor(H / 2))
触发阈值：s_trigger = min(max(m, d), H - d)
当前进度：s = min(source_offset + trimmed_steps + timeline.cursor(now), H)
无在途请求且 s >= s_trigger 时，尝试发起下一次推理。
只有 d <= s <= H - d 时，才能构造 RTC overlap condition。
```

例：H=50、m=12、d=4，则阈值是 12。如果接手时已因耗时跳过 6 个源动作，cursor 再前进约 6 个索引就达到阈值；不是接手后重新执行 12 个动作。请求期间旧轨迹继续执行，因此 Serial K=12 与 RTC m=12 **只是相同名义参数起点，不代表相同实际开环执行长度或推理频率**。

若 `2d > H`，无法满足 overlap 条件；当前实现会记录 infeasible 并可能发出不带 condition 的请求。这样的 rollout 不能默默当作完整 conditioned RTC 成功验收；需要记录 conditioned 请求比例、延迟和 gap 原因。第一条无前序计划的请求本来就不带 condition。

源码：[RTC 调度与延迟统计](../manimux/runtime/rtc/strategy.py)、[condition mask](../manimux/runtime/rtc/mask.py)、[Serial 调度](../manimux/runtime/inference.py)、[Pi05 sampler](../XPolicyLab/policy/Pi_05/openpi/src/openpi/models/pi0.py)。

### 官方参数与本轮选择

核对来源为作者论文 [v2 Appendix A.5 / Table 4](https://arxiv.org/html/2506.07339v2#A1.SS5)，不是第三方实现的默认值。

| 参数 | 论文真机实验 | ManiMux Pi05 抓瓶子 |
|---|---|---|
| β | 5 | 当前 9.1；建议 5，待确认 |
| 最小执行步数 | 25 | **12，已确认** |
| 延迟窗口 b | 10 | 当前 10，建议保持 |
| H | 50 | 当前 50，建议保持 |
| 去噪步数 n | 5 | 当前 10；是否改为 5 另行确定，Serial / RTC 必须成对修改 |
| 初始延迟 d_init | 算法输入；超参数表未给统一数值 | 当前 4；根据部署延迟确认，不能称为官方默认 |

β 是手动给定的常数上限；实际 guidance scale 随去噪时间按公式计算，不逐步手工指定、不在线学习 β。论文 A.2 通过消融选择 5，并指出过高 β 在少步去噪下可能造成不稳定。建议先使用该有出处的起点，不宣称它已是本平台各模型的最优值。

官方 Algorithm 1 用延迟历史窗口的最大值预测下一次延迟；soft mask 使用 Eq. 5 的指数衰减。作者公开仓库 [real-time-chunking-kinetix](https://github.com/Physical-Intelligence/real-time-chunking-kinetix) 是仿真实验代码，不能把其中的固定模拟延迟当作真机自适应调度的部署默认值。

公开代码亦核对到固定版本 `9296f31d62d5bfeb5779dcb2f9bcf71ca37f448b`：[RealtimeMethodConfig](https://github.com/Physical-Intelligence/real-time-chunking-kinetix/blob/9296f31d62d5bfeb5779dcb2f9bcf71ca37f448b/src/eval_flow.py) 的 `max_guidance_weight=5.0`、`prefix_attention_schedule=exp`。该仿真评估显式扫描 delay / execution horizon；上表的真机数值来自论文，而非将 Kinetix 的 H=8 配置移植为 Pi05 setting。

## 7. 决定与下一步

| 日期 | 决定 | 状态 |
|---|---|---|
| 2026-09-28 | 排除 SAPolicy；先抓瓶子；Pi05 增加丢硬币 | 用户已确认 |
| 2026-09-28 | 每 task 一张论文式主表；模型主行，算法子行 | 用户已确认 |
| 2026-09-28 | 主结果表不放 N_task、Setting；共同实验条件、数量和路径放在表外 | 用户已确认 |
| 2026-09-28 | 跳变增加 P95 和 Max；左右手各自独立列出 Mean/P95/Max，单位 mm | 指标已选；统计口径见 §2 |
| 2026-09-28 | Human + seam + PRM 三类分析；主表横向列出全部 11 项 PRM 指标 | 用户已确认完整列；具体 judge profile 待冻结 |
| 2026-09-28 | 每个 task 下，每个模型 × 推理方法采用 10 个固定布局，每布局 3 次，共 30 条；完整保存输出路径 | 用户最新决定，替代原 20/30 候选；具体布局待冻结，见 §9 |
| 2026-09-28 | 取消人工平滑度评分；人工只记录任务结论、失败标签和备注 | 用户已确认；新标签 v2 不再保存 HSS，历史标签保留 |
| 2026-09-28 | Pi05 抓瓶子 Serial / RTC 首轮候选，见 §5 | 待讨论，未改 YAML |
| 2026-09-28 | Pi05 抓瓶子 RTC `min_execute_policy_steps=12` | 用户已确认；完整 preset 未冻结 |
| 2026-09-28 | 核对原作者论文；β 首轮建议由保留 9.1 改为 5 | 建议，待确认；官方值与本地现值分列 |

下一步先收口 **抓瓶子评测协议与唯一评测入口**：layout/repeat 的 Prepare 冻结与 metadata 传递已接入代码，尚待交互验收；确认现有 10 张参考图作为正式布局，补齐交接分段证据，再按 §10 串起离线评测。实验参数仍须独立冻结：RTC m 已定 12，β、Serial K、共同推理步数和执行条件尚未决定；不能把评测流程明确视为运行 setting 已全部统一。

每次回填结果附：setting 版本、准确入口/recipe、checkpoint 与 norm 身份、代码版本、resolved config、layout/block 与 rollout 清单、三类指标各自样本数、无效/缺失原因及完整分析路径。机器地址和设备序列号留在私有 station，权重、视频和 rollout 不提交到仓库。

## 8. Agent 评测与进度登记

使用 [manimux-experiments skill](../.agents/skills/manimux-experiments/SKILL.md) 读取本文 setting、核对实际 rollout、执行离线分析并回填。Skill 不保存另一份参数默认值。

下面统计**选定 setting 对应的 cohort**，不自动纳入同名模型的历史试跑。`—` 表示尚未核对，不代表 0；当前目标是每组 10×3=30 个预定试验；具体布局冻结且逐条身份可核对后才填写完成比例。

| Setting | 阶段 | N_target | Attempts / finalized / partial | N human / seam / PRM | 下一项 | Cohort / evidence |
|---|---|---|---|---|---|---|
| B-P05-S-v0 | setting 讨论中 | 30（10×3） | — | — | 确认 Serial K、共同推理步数和执行条件 | 待生成，路径登记见 §9 |
| B-P05-R-v0 | min step 已确认 12 | 30（10×3） | — | — | 确认 β、延迟参数和共同条件 | 待生成，路径登记见 §9 |

每轮评测还需在对应 setting 的 evidence 中登记 **metric profile / judge profile**：指标版本与有效边界类别、judge 模型/权重身份、视角/时间采样、prompt/goal/reference、推理模式、后处理和样本清单。当前 PRM profile 尚未冻结，agent 应先准备输入和列出缺项，不能自行采用默认分数作为正式结果。

记录覆盖及缺口见 [数据审计](reference/experiment-infra.md#recording-coverage-audit--2026-09-28)。Human、seam、PRM 分别检查可用性：某项不足时保留 `—` 和原因，其余项可以独立推进。

## 9. 评测数量与输出路径登记

### 9.1 数量

- 用户已确认：每个真机任务下，**每个模型 × 推理方法各采用 10 个固定布局 × 每布局 3 次 = 30 条**。布局用 `01`–`10`，重复编号用 `1`–`3`；所有比较组使用同一组布局、重置规则和任务判据，每次重复重新摆放。每个布局/重复 block 内交错或随机化方法顺序，不固定总是 Serial 先跑。
- 30 表示预定试验槽位，不是 30 次成功。失败计入已评测及人工 SR 分母；invalid、partial、未标注、PRM 失败分别留档，不自动补测凑分。若人工明确安排补测，保留原 attempt 和原因，在同一布局/重复槽位下登记新 attempt，不能覆盖原始记录或事后挑选成绩。有效样本数与已执行槽位数分别报告。
- 不因 seam/PRM 数据缺失而重跑直到得到足额好分数；分别报告 `N_task / N_seam / N_prm`，以及条件指标 `N_DRR / N_FNS / N_SQS`。同一 rollout 的多个 chunk 不算多条实验。

| Task | 本体 | N_target | 数量状态 | 输出登记状态 |
|---|---|---|---|---|
| put_bottles | YAM | 30（10×3） | 数量已定；具体布局与任务判据待冻结 | Pi05 配置目标目录已登记；正式 cohort 待生成 |
| coin | YAM | 30（10×3） | 待冻结 | recipe / experiment 和输出路径待绑定 |
| assemble_screwdriver | YAM | 30（10×3） | 后续任务，待冻结 | 待登记 |
| pass_ball | Tianji | 30（10×3） | 后续任务，待冻结 | 待登记 |
| 红球放入盒子（匹配指令） | YAM | 30（10×3） | 历史任务预留，待冻结 | 待登记；历史试跑不自动计入 |

### 9.2 路径登记表

表中“配置目标目录”只说明 YAML 将数据写到哪里，不表示已收集正式结果；下列绝对路径按当前 checkout `/home/ubuntu/manimux` 解析。其他机器同时记录 host/storage 标识。保留原始目录，不搬动历史 rollout；每次新 session/分析产生后补上精确路径。

| Task / setting | 配置目标目录（run.output_dir） | 正式 cohort 清单 | Seam / 汇总分析目录 | PRM run 目录与报告 |
|---|---|---|---|---|
| put_bottles / B-P05-S-v0 | `/home/ubuntu/manimux/data/experiments/pi05-put-bottles-joint-step30000/serial` | 待生成 | 待生成 | 待生成 |
| put_bottles / B-P05-R-v0 | `/home/ubuntu/manimux/data/experiments/pi05-put-bottles-joint-step30000/rtc` | 待生成 | 待生成 | 待生成 |
| put_bottles / 其余模型与方法 | 各 setting 冻结时从实际 YAML 登记 | 待生成 | 待生成 | 待生成 |
| coin / Pi05 各方法 | 待绑定 | 待生成 | 待生成 | 待生成 |
| assemble_screwdriver / 各模型与方法 | 待逐 setting 登记 | 待生成 | 待生成 | 待生成 |
| pass_ball / 各模型与方法 | 待逐 setting 登记 | 待生成 | 待生成 | 待生成 |
| 红球放入盒子 / 各方法 | 待逐 setting 登记 | 待生成 | 待生成 | 待生成 |

同一个 task 的每个实际 setting/version/split 分别新增登记行，不能把多组输出合到一个“最新结果”路径。路径与证据在以下三处互相链接：**本节路径表 ↔ §8 进度行 ↔ §3 对应 task**。主结果表不再重复这些字段。

### 9.3 每条 rollout 的精确索引

Agent 每轮建立唯一分析目录，推荐 `data/analysis/<task>/<setting>/<split>/<analysis-id>/`，并在路径表填入它的绝对路径。其中 `cohort.jsonl` 每个尝试一行，枚举所有 session 下的完整 rollout 路径；不能只记录 `rollout-001`、通配符或 output root。重复评测时创建新分析版本，保留旧清单。

每行最少记录：

- `task`、`setting_id`、`split`、`host`、`attempt_id`、`layout_id`、`repeat_id`、block 和参考图路径/hash（缺失明确标记）；
- `episode_dir`、`session_manifest`、`meta`、`result`、`data_zarr`、`events` 的绝对路径；
- `videos_index`、各视角 `video_paths`、`human_label` 的绝对路径；
- `seam_output_dir`、`prm_manifest`、`prm_run_dir`、`prm_case_id`、逐 case 输出路径；
- final/partial 状态及 Human/seam/PRM 各自的有效性、缺失或排除原因。

不存在的文件写 `null` 与原因，不伪造路径；尚未分析的 seam/PRM 字段同样为 `null`。同时保存 `provenance.json`、`episode-metrics.json`，串起 cohort、metric/judge profile、各自分母、汇总数值、图和报告。以上是 **agent 的分析交付约定**，不是 recorder 当前已自动生成的文件；原始录像、轨迹和人工标签保持在原 episode 目录。

## 10. 统一离线评测接口：实现方案

**状态：流程与职责已明确，统一入口尚未实现；不能把本节命令当成当前可用命令。** 当前 `manimux/evaluation/` 包含人工标签保存与 rollout 身份校验；跳变分析和 PRM 各有独立入口，任务发现、正式边界筛选、汇总和报告回填仍未接通。

### 10.1 现有十个布局

本轮只读确认：`data/evaluation_layouts/put_bottles_into_the_bin/01.png`–`10.png` 全部存在，均为 640×480，十个文件 hash 不同。已有独立采集工具及 Viser 参考蒙版；这证明图片已保存，不代替对物体摆放、机位和正式任务条件的确认。

图库分组 `put_bottles_into_the_bin` 必须在后续 task 文件中显式对应实验 task `put_bottles`；图库名称和模型 Task command 都不自动充当规范 task ID。

**已接入代码，静态检查通过，尚未做 Viewer/真机验收：** 在参考布局选择 Task、编号 `01`–`10`，在 New rollout 选择 `Experiment repeat=1/2/3`，点击 `Prepare experiment rollout`。Prepare 一次冻结指令、位置、重复次数及参考图身份；取消独立可编辑 layout 框。位置/Task/重复次数在准备和运行期间锁定，蒙版透明度仍可调。参考图缺失时不提交 Prepare；普通 rollout 不要求参考图并清空正式实验身份。

冻结内容经 Viewer → session → runtime 同时写入 `meta.json` 与 Viewer 状态：`layout_id`、`repeat_id`、`reference_layout={task,path,sha256}`。图像解码和 hash 来自同一份文件字节；控制轮询不再读取图库。`Run / Recorded layout / repeat` 显示本次身份；重连后图库版本不匹配时隐藏参考并提示。独立尝试继续使用现有 episode 路径与 session/episode ID，不新增第二套 attempt UUID；重复选择同一位置/次数仍产生独立 rollout，后续盘点需显式处理重复。

这里冻结的是图片身份，不会复制或禁止独立采集工具覆盖原 PNG；正式采集期间不覆盖参考图。旧 rollout 缺少这些字段时保持未知，不补猜编号、次数或 hash。一次性 `manimux run` 若设置 `run.experiment_mode=true`，也必须显式提供上述身份字段，缺失或非法值会在创建机器人/传感器前报错。

### 10.2 唯一数据流与接口

```text
Task 目录：task.yaml（任务与数据索引；引用已有 runtime YAML 和 rollout 路径）
  └─ python -m manimux.evaluation --task-dir <task-directory>   [拟实现]
       ├─ 核对 task / 模型 / 方法 / 布局 01–10 / repeat 1–3 / attempt
       ├─ human-label.json → Human SR
       ├─ data.zarr + 离线 FK + 有效交接证据 → L/R Mean、P95、Max + 图
       ├─ videos + task prompt + judge profile → 现有 PRM 后端 → 11 项指标
       └─ analysis/<analysis-id>/ → 逐条指标、任务汇总、图与表格
```

沿用已有 `manimux/evaluation/`，不另建平行的 `manimux.eval` 实现，不引入通用插件/注册框架。该接口只做离线评测，不打开机器人或相机，不改原始 episode。任务目录作为索引和报告入口，显式引用当前分散的 rollout 根目录；历史数据保持原位，不要求为了评测搬迁录像。

`task.yaml` 只持有机器需要读取的评测协议和来源：稳定 task ID、layout 库和参考图身份、10×3 计划、成功判据/超时、模型方法对应的已有配置与 raw roots、metric/judge profile 和 PRM 解释器。运行参数仍归已有 experiment/policy/inference/executor YAML 管理，实际值从 session resolved config 核对，不另抄一份 RTC/训练参数。实验 Markdown 展示已确认约定与生成的结果；指标计算不能依赖 agent 临时编写算式或解析自然语言猜参数。

### 10.3 三类指标各自读什么

- **Human**：读取真实 `evaluation/human-label.json`；成功/失败用于 SR，invalid/缺失分别计数，不能从 runtime `success` 推断任务结论。
- **左/右跳变**：读取 `data.zarr/plans/*/committed` 的关节轨迹，用记录本体的离线 FK 得到末端 XYZ；比较新 chunk 首点与旧 chunk 在交接时刻的采样位置，得到 mm 距离。结合 `ticks.plan_id`、时间与分段事件确认实际使用过的交接；参考轨迹接缝不等于实测位移，也不从视频估计。左右手各自计算三个统计量，口径沿用 §2。
- **PRM**：读取已保存视频、任务指令和固定 judge profile；主视角与可选双腕视角的选择须固定。若采用多视角，依据 `videos/index.json` 的时间戳检查/处理同步，不能直接假设相同帧号表示同一时刻。只生成 manifest 并调用现有 PRM 后端，复用其 11 项公式；PRM 模型依赖留在独立环境，不导入硬件 runtime。目标图需要在 profile 中明确，初始布局参考图不自动充当任务完成目标图。

### 10.4 最小实现范围与验收

1. **记录身份与分段证据**：layout、repeat、参考图身份已接入现有 Viewer/session/runtime metadata 路径，尚待交互验收；有时间戳的暂停/恢复分段仍待实现，需结合已保存 tick plan ID 判断交接。旧数据缺证据则标未知，不猜 repeat 或拼接跨段边界。
2. **任务读取和数值评测**：在现有 `manimux/evaluation/` 增加统一入口与读取/计算模块，盘点所有尝试和 10×3 槽位、汇总 Human SR，规范有效接缝分类及左右 Mean/P95/Max。提取现有画图脚本中可复用的 FK/绘图逻辑，让旧 CLI 调用同一实现，不复制第二套 seam 公式。
3. **PRM 适配**：增加薄适配模块，完成视频质量/对齐检查、manifest 导出、独立环境调用与结果导入；保存实际 PRM run/case 路径和 profile 身份。读取已有匹配结果可以复用；profile 或视频改变则不得复用旧分数。
4. **统一报告**：一个 report 模块生成 `cohort.jsonl`、`episode-metrics.json`、`summary.json`、`table.md` 和图。每个 metric 带有效数量、来源及缺失原因；写入新 analysis 目录，精确索引原始证据。固定 task/model/method 行映射后更新 Markdown 对应表格及表外进度/路径，不重写人工说明。

离线验收覆盖重复/缺失槽位、Human v1/v2、已知 FK 接缝、暂停/hold/未执行计划排除、空条件指标、PRM profile 不匹配与缺视频。先用已知轨迹和已有记录验证数字及路径，再单独做真实 PRM 推理验收；离线检查不代表真机任务成功。实现后 skill 只负责选择协议、调用此入口和检查结果，不能保留与入口竞争的临时计算流程。
