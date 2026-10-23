# 复现步骤

## 环境

1. 按 `requirements.txt` 安装（2026-04-18 版，gymnasium 必备，
   stable-baselines3 / torch 为可选，只在跑 PPO 时需要）。
2. 原脚本写的是 `from ecos.control...`，不是 `src.ecos...`，所以跑任何
   experiments/ 下的脚本前，必须先设 PYTHONPATH 指向本包的 `src/` 目录，
   例如在包根目录执行：`set PYTHONPATH=%CD%\src`（cmd），再跑脚本。
   不要静默改脚本里的导入路径和公式。

## 最小验证（先跑这个，不要直接全量）

1. 导入冒烟（工作目录必须是本包的 `src/`，包名就是 ecos）：
   `cd JEDC-FSRS-v43-replication\src`
   `python -c "from ecos.control.ecos_env import ECOSControlEnv; from ecos.agents.fsrs_memory import FSRSMemoryBank; print('import ok')"`
   不要在包根目录用 `src.ecos.*`，环境内部写的是 `from ecos.core...`，那样会断。
   依赖：numpy、networkx、gymnasium，先确认这三项已装。
2. 单配置复验：用 `experiments/grid_search/grid_search_control.py` 的 evaluate 逻辑，
   只跑 thr=0.45, sev=0.40 和 thr=0.30, sev=0.60 各 10 episodes，
   期望接近 `results/grid/results_grid.json` 的 3947.33 / 3433.56，
   允许随机种子带来的小偏差，不允许量级偏差。
3. 全量网格：24 配置 × 10 episodes，耗时视机器而定，跑完再与 results_grid.json 全表比对。

## 缺口（跑之前先认）

1. PPO 训练脚本未定位：只有 results_v4.json 和模型 zip，不能声称训练过程已复现。
2. 目标区时间（48.1% / 51.0%）的源数据未定位：results_grid.json 无 zone 字段。
3. 稳健性脚本来自 4 月备份，9 月副本只有 run.py；若 9 月环境改过接口，
   先跑 4 月脚本的 import，再决定是否以 9 月 run.py 为准。
4. 本包正文未改：复现数字对得上，不代表论文文本矛盾已消除，见 README 末节。
