# EOVT-Bench

面向具身视觉跟踪的遮挡鲁棒性评测基准。

本仓库提供固定episodes、任务标注、环境配置、两个baseline与统一评价器。
自建场景以独立压缩包提供，人物、机器人和检测器资源从各自提供方单独获取。
取得匹配资源后，使用者无需重新构建场景或生成路径。
当前发布版本为`0.2.8`。
仓库公开benchmark接口、两个诊断baseline、版本化评价器和OmTrackVLA定性案例；
不公开学习模型权重及其内部实现。
旧版baseline汇总数值单独存档，不提供逐回合原始结果。

## 数据和三项任务

| 任务 | 内容 | 数量 | 主要指标 |
| --- | --- | --- | --- |
| STT | 单目标连续跟踪 | 1,800个回合 | SR、TR、CR |
| OR | 遮挡后目标重获 | 来自558个源回合的630个事件 | RSR、VOR、CRR、MRS |
| IC | 遮挡后身份一致性 | 630个事件，每个1 Same＋3个不同Similar | Same成功数、Similar跟随原目标数、有效跟随比例 |

三类场景分别为Road（资源标识`road`）、Indoor和Industrial，各20个布局。
全部场景由benchmark作者自行搭建。
参考遮挡标注不等同于每个策略运行时的实际可见性。

## 下载资源

代码、episodes、配置和人物相似度元数据保存在Git仓库。
baseline历史汇总单独存档，不提供逐回合结果JSON或结果压缩包。
自建场景由本仓库的资源Release提供；人物、机器人和检测器权重向实际提供方获取；
不再通过本仓库的混合资源包下载。
详见[第三方资源获取与安装说明](docs/THIRD_PARTY_RESOURCES.zh-CN.md)，
包含官方地址、注册/申请步骤、放置目录及原实验文件校验值。

取得仓库后，可先检查自带元数据：

```bash
python scripts/check_resources.py --group metadata
python scripts/download_resources.py --kind scenes
```

运行仿真前，按获取说明准备匹配资源，再运行：

```bash
python scripts/check_resources.py
python evaluation/validate_package.py
```

场景由benchmark作者提供，人物资源通过作者指定的
[humanoids.zip下载地址](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1)
获取。已实际核验下载包：500个必需人物文件均与原实验清单一致。
安装命令：`python scripts/install_humanoids.py --archive /path/to/humanoids.zip`。
通用资源不能替代原实验文件。
已合法持有原版本地完整包的使用者仍可离线安装；原混合分包下载入口已撤下。

## 环境与运行

仿真需要Linux/WSL2及适用的NVIDIA/EGL环境。2026-11-25已新建独立conda环境，
验证Habitat-Sim 0.3.3、声明的依赖、49项测试、两个baseline的STT以及当前Oracle OR/IC真实运行。
安装复用官方wheel缓存，没有复用原环境的site-packages；这不是总体性能重测。
详细步骤见[安装说明](docs/INSTALLATION.md)，实际版本见`configs/environment_validated.json`。

```bash
conda env create -f environment.yml
conda activate eovt-bench
python -m pip install -r requirements.txt
bash baselines/scripts/test.sh

python run_baseline.py --variant oracle_pid --task stt --gpu 0 --max-episodes 1
python run_baseline.py --variant rgb_tracker_pid --task stt --gpu 0 --resume
```

三项任务默认采用当前协议；OR/IC会保存完整同步证据，并直接调用公开的v0.2评价器：

```bash
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

新版OR/IC结果附有证据路径、SHA-256、运行配置指纹和评价器版本，续跑时逐一核对。
每次证据采集使用独立目录，统计时不会将其中的试验输入重复计入总体样本。
`--episode-id EVENT_ID`可固定事件并重复传入。
历史运行需显式指定`--legacy-online-metrics`，历史汇总需`--allow-legacy`；
缺少完整轨迹、投影和真实时间戳的历史汇总不能直接转换为新版结果。
自定义事件ID须提供`layout`或`layout_id`，布局缺失时不能计算布局层置信区间。

旧版SameSR、SwapSR、BIA和OTPR字段仅保留用于兼容和审计。
当前OR以运行时实际丢失事件作为分母；当前IC依据完整轨迹与位姿相对
Same的行为保持进行二元判定，不再使用OTPR进行身份判定。
初始阈值见`configs/evaluation/or_visibility_v0.2.json`。

## 两个baseline

- RGB Tracker PID：YOLO人物检测＋外观/运动关联＋框控制PID；初始选择最大检测框，
  不向策略提供原目标真值。
- Oracle PID：读取仿真器提供的原目标框/facing，使用同一PID实现及固定配置；
  这是诊断对照，不保证构成性能上界。

两个baseline保留既有控制参数；当前OR/IC和历史兼容输出使用不同目录及版本字段。
仓库不包含三个学习模型的完整源码或权重。

字段见[DATA_FORMAT](docs/DATA_FORMAT.md)，计分见[PROTOCOL](evaluation/PROTOCOL.md)，
历史baseline汇总见独立存档页。
当前校验范围与许可状态见[发布状态](docs/RELEASE_STATUS.md)。

## 许可证

自有代码、脚本和可执行配置采用[MIT许可证](LICENSE)。
自建场景、Episode、路径、事件标注、人物描述与相似候选元数据，以及自有文档，
采用[CC BY 4.0许可证](LICENSE-DATA)。两项均允许商业使用，
须按相应条款保留许可声明或署名、注明修改。
具体适用范围与署名格式见[许可说明](docs/LICENSING.md)。

第三方代码、人物资产、Spot机器人及检测器权重保留各自原有许可，
不纳入上述统一授权；下载地址和校验值不代表授予新的第三方资源权利。

## 真实视频案例

提供OmTrackVLA的12段机器狗第一视角真实案例（OR/IC按新版v0.2计分）：STT、OR、IC各成功2例、失败2例，并附本次结果JSON和逐步轨迹。详见[案例索引](qualitative/omtrack_first_person/README.md)及[中文判定说明](docs/QUALITATIVE_VIDEOS.zh-CN.md)。


## 历史结果

旧版汇总数值保存在[历史结果页](docs/HISTORICAL_REFERENCE_RESULTS.md)，保留原评价器版本。
新版OR/IC尚未进行baseline全量重跑；运行入口的真实冒烟验证不代表新的总体性能结果。

公开范围与署名说明：[PUBLICATION](docs/PUBLICATION.md)。
完整检查范围、已修正问题和仍未完成的工作见[仓库核查报告](docs/REPOSITORY_AUDIT.md)。
