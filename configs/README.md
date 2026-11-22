# Configuration
The complete composed Habitat source YAML tree is in habitat/. Baseline JSON files are in baselines/.
Camera, physics, action limits, following and collision thresholds are preserved from the source.
The runner overrides maximum steps with the baseline config (300), dataset path, GPU index and absolute articulated assets.
IC uses the *_ic.json controller settings; STT and OR use the unsuffixed configs.
Asset relocations affect paths only. The scene geometry, metadata values and metric thresholds are unchanged.
Do not infer effective robot speed from a PID command alone: the simulator multiplies action commands by its action configuration.
