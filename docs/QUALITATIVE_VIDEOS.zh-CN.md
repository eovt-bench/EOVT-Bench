# OmTrackVLA：三任务第一视角真实案例

本包包含12段OmTrackVLA新运行的闭环评测视频：STT、OR、IC各2个成功和2个失败。
画面直接来自机器狗原有的 `agent_1_articulated_agent_jaw_rgb`，没有添加相机、
真值框或轨迹覆盖。每个初始化状态及每个动作执行后的状态各录一帧，以10 fps播放；
视频时间不是模型推理的真实耗时。帧编号与 `trajectory.jsonl` 中的step一一对应。

这些案例是按运行结果挑选的定性示例，不能据其成功比例估计整体性能。
历史日志仅用于选择候选，最终标签由本次重新运行产生。所有尝试保留在本机原目录。
未修改原数据、模型权重、动作接口、相机或判定阈值。与旧服务器的Habitat版本不同，
本机重跑不声称与历史轨迹逐帧一致。

## 如何解释成功与失败

- **STT**：采用原评测器的最终 `success` 字段，同时提供TR、碰撞和终止状态。
- **OR**：这些视频的标签保留生成时记录的旧评价器版本，用于展示成功和失败
  案例，不将旧标签冒充新版OR分数。新运行应使用
  `evaluation/or_visibility.py`：实际丢失、重新可见机会和连续有效跟随恢复
  分开判定。
- **IC**：这些视频的标签同样保留原始OTPR口径，仅作历史定性展示。新版IC
  使用完整轨迹和机器人朝向相对Same进行判断，不再用OTPR作二元身份判定；
  规则见`evaluation/ic_behavior.py`和`evaluation/PROTOCOL.md`。

每段目录内有原始MP4、最终JSON、步骤轨迹、摄像记录和案例编号。
`case_index.csv/json`汇总12例；`video_validation.json`记录完整解码、帧数和步骤对应检查；
`model_provenance.json`记录权重哈希和运行版本。视频仅是定性材料，
不包含第三方模型权重、人物模型或场景模型本身，原资源条款仍适用。

完整视频包：[下载](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/eovt-omtrack-first-person-cases-20261121.zip)。
视频仅展示OmTrackVLA运行行为，不包含模型权重或内部实现。
