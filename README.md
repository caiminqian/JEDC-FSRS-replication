# JEDC-FSRS-v43 投稿复现包

论文：Cognitive Spaced Repetition in Agent-Based Economic Modeling: A SuperMemo Approach
正文：`paper/JEDC_submission_draft_FSRS_FINAL_v43.md`（2026-09-26 稿）
来源：dao 上 `.openclaw/workspace/ziwei/workspace/ecos/`（2026-09-26 工作副本）为主，
4 月备份 `backup/openclaw-full-2026-04-18/ecos/` 只补 9 月副本缺失的稳健性脚本。

## src/ecos 是完整包，不是截取

`src/ecos/` 是原包全量复制（不含 `__pycache__`），包含 control、agents（含 trader 全套，
因为 trader/`__init__.py` 会导入 institution/macro/regulator/risk/analyst）、
governance（含 ministries）、core（含 world_state）、risk 全套，
因为 `ecos_env.py` 直接导入 `ecos.core.world_state`，
`governance_manager.py` 直接导入 `ecos.core.metrics`、`ecos.governance.ministries`、
`ecos.risk.*`。只留 control/agents/governance 是跑不起来的，本包已补齐。
唯一生成文件是 `src/ecos/control/__init__.py`（空文件，源目录本来就没有，
Python 3 命名空间包本来也能跑，补上只是为了导入路径明确）。

运行工作目录必须是 `src/`，导入写 `from ecos.control.ecos_env import ECOSControlEnv`，
不要写 `src.ecos.*`，否则环境内部的 `from ecos.core...` 会断。详见 REPRODUCE.md。

## 表、图与脚本对照

1. 表 2 / 图 2 / §4.4.2 网格搜索：`experiments/grid_search/grid_search_control.py`
   → `results/grid/results_grid.json`，最优 thr=0.45, sev=0.40，3947.33；
   基线 thr=0.30, sev=0.60，3433.56。
2. §5.1.3 FSRS vs EE 对比：`experiments/comparison/compare_memory_engines.py`
   → `figures/fig4_fsrs_vs_ee.png`。
3. §5.3 稳健性：`experiments/robustness/robustness_fsrs_final.py`
   （仅 4 月备份有，9 月副本缺，已在 MANIFEST 标注来源）→ `figures/fig3_robustness.png`。
4. §4.3 校准：`experiments/calibration/`，S=45、α=0.6。
5. §5.5.1 端到端交易：`experiments/trading/run_enhanced_trading_simulation.py`
   → `results/validation_5_5/full_trading_simulation.json`。
6. §5.5.2 Monte Carlo：`experiments/monte_carlo/run_fsrs_vs_ee_monte_carlo.py`
   → `results/validation_5_5/fsrs_vs_sm20_monte_carlo.json`（30 runs，seed_base 0，250 ticks）。
7. §5.5.3 十年：`experiments/longterm/run_fsrs_vs_ee_10year_3650d.py`
   → `results/validation_5_5/fsrs_vs_sm20_10year_3650d.json`（8 runs，seed_base 200，3650 ticks）。
8. §5.4 PPO：只有 `results/rl/results_v4.json` 和模型 zip，训练脚本在本包来源清单中未定位，
   见 REPRODUCE.md 的缺口说明，不要把结果说成已完整复现训练过程。
9. §5.2 1000 agent：`results/stress/stress_1000a_output.txt`（原始输出文本）。

## 命名说明（不要改名掩盖）

`results/validation_5_5/` 里原始文件和键名还叫 sm20，但按论文自己的术语注，
代码实现的基线是 EE 指数曲线，不是商业 SM-20。原文件名保留作溯源，
README 在此写明：sm20 = EE 基线。

## 明确排除

1. v2–v42 草稿、v43 中间 tex 变体，只留一个 tex。
2. `ziwei/` 顶层 653 个 check_/fix_/update_ 一次性脚本。
3. `.env`、docker、grafana、logs、`__pycache__`。
4. 沙箱 ecos-push（后来 fsrs 6.3.1 官方库版），与本篇公式口径不同。

## 本包不等于论文已可发表

打包只解决“代码找得到、对得上 json”这一层。论文正文的以下问题仍在，
投之前必须另行修文（不在本包改动正文）：半衰期 FSRS/EE 混用、§3.3 G=2 示例反号、
§4.4.2 的 3927 stray、目标区 48.1%/51.0% 不一致、Monte Carlo 正文“No EE run > 0.5”
与 raw 数据自打脸、>100%、结论“early, mild, frequent”与“零干预最优”自相矛盾、
Cont(2001) 参考文献缺失。目标区时间的源 json 在本包来源中未找到，
`results/grid/results_grid.json` 里没有 zone 字段。
