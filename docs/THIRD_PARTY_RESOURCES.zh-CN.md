# 自建场景与第三方资源获取说明

资源策略版本：`separate-scenes-and-external-resources-20261125`；官方页面核对日期：2026-11-21。

本仓库保留评测代码、配置、episodes、事件标注、固定人物分配、相似人物信息和校验清单。
场景、定制人物、机器人资源及检测器权重不再通过混合资源包提供下载。
使用者从相应提供方获取资源并遵守其许可，再放入指定目录。

## 需要准备的资源

| 内容 | 放置位置，相对于仓库根目录 | 获取方式和当前状态 |
| --- | --- | --- |
| EOVT 的60个真实布局 | `scenes/layout_instances/` | 全部场景由benchmark作者自行搭建，由作者提供固定布局包，无需另找第三方场景下载。运行`python scripts/download_resources.py --kind scenes`获取独立场景包，不包含人物、机器人或检测器资源。 |
| 定制人物及动作 | `assets/humanoids/humanoid_data/` | 使用作者提供的[humanoids.zip下载地址](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1)，解压放置后核对原实验清单。 |
| Spot机器人 | `assets/robots/hab_spot_arm/` | 通过Habitat官方资源渠道获取，保留声明并核对版本和文件校验值。 |
| YOLO11x权重 | `assets/detectors/yolo11x.pt` | 从Ultralytics官方资源页获取并遵守其条款；仅RGB Tracker PID需要。 |
| 人物ID、文字描述和三个相似候选 | `assets/humanoids/*.json` | 已保留在Git中，不包含人物网格、模型参数或动作文件。 |
| 两个baseline的历史汇总 | `docs/HISTORICAL_REFERENCE_RESULTS.md` | 仅提供数值表与置信区间，不提供原始结果下载。 |

完整目标文件、大小、SHA-256见`assets/manifest.json`，
各资源组及官方地址见`assets/resource_policy.json`。
文件校验通过仅表示与原实验资源一致，不等于获得分发许可。

## 自建场景说明

benchmark作者于2026-11-21确认：Road、Indoor、Industrial场景均由其自行搭建。
60个布局属于作者提供的benchmark场景数据，不再列为来源不明的第三方场景。
使用时保留`scenes/layout_instances/`下的原目录名称及其episode引用。
独立包仅包含60个布局的1,860个固定文件，解压前后均校验SHA-256。
布局、路径与原实验文件保持一致。

## 人物资源下载与安装

作者提供的下载入口：

[Google Drive：humanoids.zip](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1)

2026-11-25已实际下载393,682,777字节的压缩包；500个必需人物文件全部通过固定清单校验。
压缩包根路径为`humanoids/humanoid_data/`。
该链接是作者指定的获取地址，不将Google Drive表述为模型原始授权方。

推荐使用`python scripts/install_humanoids.py --archive /path/to/humanoids.zip`安装；
只复制固定清单中的人物文件，跳过macOS附属文件并保留仓库元数据。

1. 下载并先解压到临时目录，保留资源附带的许可说明。
2. 找到人物数据层级。预期文件示例为`male_4/male_4.urdf`和
   `male_4/male_4_motion_data_smplx.pkl`，不要直接假定压缩包根目录就是安装目录。
3. 将各人物目录放入`assets/humanoids/humanoid_data/`，保留URDF引用的网格、纹理和动作。
   保留仓库中固定的`assets/humanoids/humanoid_infos.json`、
   `humanoid_descriptions.json`和`appearance_top3.json`，不要用下载包中的同名元数据覆盖。
4. 执行`python scripts/check_resources.py --group humanoids`。
   如有缺失或不一致，先排查资源版本；通用模型不能替代固定评测人物。

对于适用SMPL-X条款的内容，仍可查阅[官网](https://smpl-x.is.tue.mpg.de/)、
[模型许可](https://smpl-x.is.tue.mpg.de/modellicense.html)和
[Body许可](https://smpl-x.is.tue.mpg.de/bodylicense.html)。这些是补充说明，
不再把“单独申请SMPL-X模型”当作上述人物资源包的替代获取方式。
提供下载链接本身不代表本仓库新授予资源分发许可。

## 机器人资源如何获取

Habitat-Sim 0.3.3的[官方下载器](https://github.com/facebookresearch/habitat-sim/blob/v0.3.3/src_python/habitat_sim/utils/datasets_download.py)
包含`hab_spot_arm`，来源为
[ai-habitat官方资源库](https://huggingface.co/datasets/ai-habitat/hab_spot_arm)。
在兼容的Habitat-Sim环境中，官方获取命令为：

```bash
python -m habitat_sim.utils.datasets_download \
  --uids hab_spot_arm --data-path /path/to/separate/habitat-data
```

官方文件已实际下载核对。22个二进制文件与实验版本一致，三个文本文件需要明确转换：
README和许可文件仅统一换行符；URDF另外去除八个机械臂部件的可视网格，保留碰撞几何。
使用以下脚本从固定官方版本获取并转换，转换后25个文件的SHA-256均与实验清单一致：

```bash
python scripts/prepare_spot.py --download --source .downloads/spot-official
python scripts/check_resources.py --group robot
```

转换规则和官方源文件哈希公开保存在`assets/spot_upstream_manifest.json`，
不上传机器人二进制资源。保留并遵守`licenses/Spot-assets-LICENSE.txt`及上游条件。

## 检测器权重如何获取

先阅读[Ultralytics许可说明](https://www.ultralytics.com/license)和
[YOLO11文档](https://docs.ultralytics.com/models/yolo11/)，
再从[官方v8.3.0资源页](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt)
获取`yolo11x.pt`。

```text
放置位置：assets/detectors/yolo11x.pt
原实验文件大小：114636239字节
SHA-256：7bc158aa95c0ebfdd87f70f01653c1131b93e92522dbe15c228bcd742e773a24
```

2026-11-25已实际从该官方Release下载，SHA-256与原实验权重一致。
用户下载后应自行运行校验。Oracle PID不需要此权重。

## 安装后检查

在仓库根目录执行：

```bash
python scripts/check_resources.py --group metadata
python scripts/check_resources.py --group scenes
python scripts/check_resources.py --group humanoids
python scripts/check_resources.py --group robot
python scripts/check_resources.py --group detector
python evaluation/validate_package.py
```

检查程序只读取文件，不删除、覆盖或下载资源。加`--json`可查看具体缺失或不匹配的路径。
`--presence-only`只核对存在性和大小，不代表SHA-256校验通过。
Oracle运行需要场景、人物和机器人；RGB方法还需要检测器。

已经合法持有原版完整本地资源包的使用者，可继续使用离线安装入口：

```bash
python scripts/download_resources.py --kind assets --archive /path/to/existing/assets.tar.gz
```

该入口只安装与原校验清单匹配的本地包，不提供下载，也不授予再次分享该包的权利。
原有混合资源分包下载入口已经撤下。

## 公开发布时的边界

场景已按作者确认记录为自行搭建的数据，采用CC BY 4.0；
其中自有辅助代码采用MIT。具体范围与署名格式见[许可说明](LICENSING.md)。
人物、机器人及检测器资源通过单独获取入口准备，保留各自适用的原始声明。
原混合资源包不重新上传；资源仍按各自条件获取。
