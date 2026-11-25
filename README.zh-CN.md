# EOVT-Bench

面向具身视觉跟踪的遮挡鲁棒性评测基准。

本仓库提供固定场景、episodes、任务标注、环境配置、两个baseline与统一评价器。
使用者加载现有资源进行评测，无需重新构建场景或生成路径。
当前版本为`0.2.2-pre.20261125`，作为研究预览版本提供。
仓库公开benchmark接口、两个诊断baseline、版本化评价器和OmTrackVLA定性案例；
不公开学习模型权重及其内部实现。
baseline结果仅以本README中的数值表提供。

## 数据和三项任务

| 任务 | 内容 | 数量 | 主要指标 |
| --- | --- | --- | --- |
| STT | 单目标连续跟踪 | 1,800个回合 | SR、TR、CR |
| OR | 遮挡后目标重获 | 来自558个源回合的630个事件 | RSR、VOR、CRR、MRS |
| IC | 遮挡后身份一致性 | 630个事件，每个1 Same＋3个不同Similar | Same成功数、Similar跟随原目标数、有效跟随比例 |

三类场景分别为Route（资源标识`road`）、Indoor和Industrial，各20个布局。
全部场景由benchmark作者自行搭建。
参考遮挡标注不等同于每个策略运行时的实际可见性。

## 下载资源

代码、episodes、配置和人物相似度元数据保存在Git仓库。
baseline仅在下方公布汇总数值，不提供逐回合结果JSON或结果压缩包。
场景、人物、机器人和检测器权重改为由使用者向实际提供方获取；
不再通过本仓库的混合资源包下载。
详见[第三方资源获取与安装说明](docs/THIRD_PARTY_RESOURCES.zh-CN.md)，
包含官方地址、注册/申请步骤、放置目录及原实验文件校验值。

取得仓库后，可先检查自带元数据：

```bash
python scripts/check_resources.py --group metadata
```

运行仿真前，按获取说明准备匹配资源，再运行：

```bash
python scripts/check_resources.py
python evaluation/validate_package.py
```

场景由benchmark作者提供，人物资源通过作者指定的
[humanoids.zip下载地址](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1)
获取。已确认下载页面可访问，尚未下载该包核对内部文件与原实验清单是否一致。
通用资源不能替代原实验文件。
已合法持有原版本地完整包的使用者仍可离线安装；原混合分包下载入口已撤下。

## 环境与运行

仿真需要Linux/WSL2及适用的NVIDIA/EGL环境。环境文件记录已观察到的版本，
不代表已经验证全新机器安装或全量GPU复跑。后续精选的本机运行见下方真实视频案例。

```bash
conda env create -f environment.yml
conda activate eovt-bench
python -m pip install -r requirements.txt
bash baselines/scripts/test.sh

python run_baseline.py --variant oracle_pid --task stt --gpu 0 --max-episodes 1
python run_baseline.py --variant rgb_tracker_pid --task stt --gpu 0 --resume
python run_baseline.py --variant rgb_tracker_pid --task or --gpu 0 --resume
python run_baseline.py --variant rgb_tracker_pid --task ic --gpu 0 --resume
```

`--split-num 30 --split-id 0`用于原有30分片方式。
IC自动读取固定的新版人物配置和`_ic.json`控制参数。
结果写入`baselines/outputs/`；只有字段完整、可正常解析的最终JSON可用于续跑，
`*_info.json`不作为完成标志。

## 统一统计

```bash
python evaluation/score_or_ic.py or frames.jsonl --output scored_or/event.json
python evaluation/score_or_ic.py ic ic_event.json --output scored_ic/event.json
python evaluation/aggregate_results.py scored_or --task or --bootstrap 2000
python evaluation/aggregate_results.py scored_ic --task ic --bootstrap 2000
```

统计以布局为bootstrap聚类单位，报告95%置信区间。
IC先筛选Same资格，在事件内汇总Similar试验，再跨有效事件平均。
Same不合格的配对单独排除；合格事件中的Similar碰撞按失败处理。
OTPR数值不参与新版判定；缺失必要轨迹或时间戳属于输入错误。

baseline运行器的在线OR/IC汇总仍采用历史口径，不能仅凭这些汇总字段
转换为v0.2结果。新版离线计分需要完整同步证据；视频包附有可复算输入，
不代表baseline日志采集器已升级或已完成新版全量实验。
当前OR/IC计分需要NumPy，汇总统计使用Python标准库。

旧版SameSR、SwapSR、BIA和OTPR字段仅保留用于兼容和审计。
当前OR以运行时实际丢失事件作为分母；当前IC依据完整轨迹与位姿相对
Same的行为保持进行二元判定，不再使用OTPR进行身份判定。
初始阈值见`configs/evaluation/or_visibility_v0.2.json`。

## 两个baseline

- RGB Tracker PID：YOLO人物检测＋外观/运动关联＋框控制PID；初始选择最大检测框，
  不向策略提供原目标真值。
- Oracle PID：读取仿真器提供的原目标框/facing，使用同一PID实现及固定配置；
  这是诊断对照，不保证构成性能上界。

两个baseline保留既有STT、OR、IC协议和控制参数。
仓库不包含三个学习模型的完整源码或权重。

字段见[DATA_FORMAT](docs/DATA_FORMAT.md)，计分见[PROTOCOL](evaluation/PROTOCOL.md)，
baseline汇总数值见下方表格。
当前校验范围与许可状态见[发布状态](docs/RELEASE_STATUS.md)。

## 真实视频案例

提供OmTrackVLA的12段机器狗第一视角真实案例（OR/IC按新版v0.2计分）：STT、OR、IC各成功2例、失败2例，并附本次结果JSON和逐步轨迹。详见[案例索引](qualitative/omtrack_first_person/README.md)及[中文判定说明](docs/QUALITATIVE_VIDEOS.zh-CN.md)。


## Baseline汇总数值

以下为历史已完成baseline实验的汇总结果，口径为`eovt-evaluator-20261121`；
括号内为布局层bootstrap的95%置信区间，2,000次重采样。
比例指标单位为%，MRS单位为步。本次视频更新未重跑这些baseline或改变数值。
本仓库与Release不提供baseline逐回合结果JSON、文件清单或结果压缩包。

### STT

| 方法 | 回合/事件数 | SR | TR | CR |
| --- | --- | --- | --- | --- |
| RGB Tracker PID | 1800 | 49.28 [46.50, 52.06] | 69.31 [66.88, 71.60] | 0.00 [0.00, 0.00] |
| Oracle PID | 1800 | 42.28 [38.94, 45.39] | 65.74 [63.02, 68.30] | 0.00 [0.00, 0.00] |

### OR

| 方法 | 回合/事件数 | RSR | VOR | CRR | MRS |
| --- | --- | --- | --- | --- | --- |
| RGB Tracker PID | 630 | 31.43 [27.82, 35.33] | 72.54 [69.23, 75.94] | 43.33 [38.53, 48.28] | 4.50 [3.29, 5.89] |
| Oracle PID | 630 | 11.43 [8.62, 14.24] | 72.54 [69.69, 75.46] | 15.75 [11.85, 19.75] | 11.29 [9.66, 12.94] |

### IC

| 方法 | 有效Same数 | DSR合格事件数 | RFR | DSR |
| --- | --- | --- | --- | --- |
| RGB Tracker PID | 630 | 174 | 72.22 [68.97, 75.39] | 72.80 [65.15, 80.61] |
| Oracle PID | 629 | 130 | 79.17 [75.97, 82.38] | 61.79 [51.99, 71.78] |

**版本与解释限制。**表中历史汇总数值保留原有
`eovt-evaluator-20261121`口径，没有静默改写为新版OR/IC结果。
后续运行必须同时记录评价器版本和协议版本。该协议用于诊断模型能力
短板，不用于宣称所有模型在任意参数设置下的普遍排序。完整计分语义见
[PROTOCOL](evaluation/PROTOCOL.md)。


公开范围与署名说明：[PUBLICATION](docs/PUBLICATION.md)。
