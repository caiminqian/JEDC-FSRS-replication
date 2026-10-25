# CHANGELOG v54（T2 档位处理：新增 A/B 两章与 6 条 limitation，标题与 v53 数字全不动，2026-10-25）

依据：用户 2026-10-25 21:56 点选“接受 T2，进 v54 稿”；口径文件
`~/workspace/jedc_pack/v54/V54_SPEC.md`、阶段报告
`V54_STAGE1_REPORT.md` / `V54_STAGE2_REPORT.md`、以及
`v54/results/` 下 2547 个 json（A-500 100、A-grid 1920、Amc 360、
A10y 96、B1 71，另 B2_summary / stage2_tables）。

底本：`JEDC_submission_draft_FSRS_FINAL_v53.md`（12,805 词，CRLF）。
v53 文件原地未动（md5 动工前后一致，见文末自验）；本版只新增
v54 草稿与本 changelog 两个文件，不动 repo、dao pack、results jsons、
tex、cover letter，不写 V54_RESULTS.md。

- 方法：锚点插入式生成（搭建脚本放 /tmp，不计入交付文件）。
  v53 全文只改 3 行——文首 Submission Date、Word Count 两行，
  以及摘要段落 1 行（追加双口径句）；其余全部改动均为新增插入，
  无一行旧文被改写或删除（diff 验证，见文末）。
  新稿 16,863 词（`LC_ALL=POSIX wc -w` 实测，写进文首 header；
  v53 的 12,805 不再沿用），CRLF，755 行。

## 1. 标题不动（A）

标题与 v53 逐字一致：
*Long Memory in Agent-Based Markets: FSRS Power-Law Forgetting vs
Ebbinghaus Decay, and Why Control Fails to Bite*。
T2 档位不触发标题改动（标题改动只属于未达成的 T3）。

## 2. 摘要：双口径句（B）

在中心结果句后追加一句：§5.7 的第二口径——真同质 FSRS 格对
异质 EE 格（对数正态 σ=2）——tick-500 差距为 7.6×
（R̄(500) = 0.77844 vs 0.10201，G = 0.883），与已发表的
47,000× 并列为同一竞赛的两种口径，而非竞争性估计。
摘要其余主张一字未动。

## 3. §5.1：口径标注 + Table 5.1b（C）

- 在原表后加口径标注段：原表为已发表口径（混合人口基线，
  FSRS 组 avg_S 19.70、EE 组 45.0），原数字 0.7185 / 0.000015 /
  ~47,000× 原样保留。
- 新增 Table 5.1b（同质/异质两列）：同质 C1 0.77844 / C3 0.00001；
  对数正态 C2 σ=1/1.5/2 为 0.77917 / 0.77977 / 0.77988，
  C4 为 0.01894 / 0.05733 / 0.10201；两点 C4′ 0.02674；
  均匀 C4″ 0.54191（均为 tick-500 平均 R，10 seed 均值）。
  FSRS 的两点/均匀格未跑，表中明写 not run。

## 4. 新增 §5.7：异质性裁决实验（A 线，D）

- 设计：D1 对数正态 σ∈{0,1,1.5,2} 分位匹配到 45（主口径，
  乘性更新律内生）、D2 两点 11.68/173.34、D3 均匀 [0.89, 2268]；
  S0 下界 0.1 天；同一 agent 三课同 S0；CRN 配对
  （同 family/run_id 下 FSRS 与 EE 共享 S0 实现与网络实现）；
  治理层监控关闭并记入全部输出文件；α 不异质化（核心冻结）。
- 矩阵：C1/C2/C3/C4/C4′/C4″ × A-500 / A-grid / A-mc / A-10y
  四族；A-mc 与 A-10y 的归档 2 agent 协议只跑 C1/C3 作参照，
  异质性格用新人口协议（100 agent/engine），两协议数字不可混比。
- A-500 表：见 §3 数字，另附标准差（C2 0.00313/0.00457/0.00581，
  C4 0.00470/0.01205/0.01927，C4′ 0.00206，C4″ 0.01778，
  C1/C3 为 0）；全部 run 干预数 0。
- A-grid 表：FSRS 格全零干预（C1 全配置均值 −142.03，
  C2 −182.06/−203.98/−227.11）；EE 格干预约 4.5/集
  （C3 均值 +1413.53、基线 +190.97；C4 +1220.25/+1059.46/+902.88；
  基线 C4s1 −166.09、C4s1p5 −418.07、C4s2 −908.85，
  随 σ 增大恶化且方差爆炸）。
- A-mc 表：人口 C1 0.9819（30/30 >0.85）、C2s2 0.9760（29/30）、
  C3 0.6455（8/30）、C4s2 0.6202（6/30）、C4u 0.9351（28/30）；
  参照 C1 0.9820、C3 0.6040 与归档一致。
- A-10y 表：参照差距 0.0922（0.9996−0.9074）、人口差距
  0.0646（0.9997−0.9351），协议不同不可混比。
- 形状拟合（pooled R̄(t)）：窗口 [10,500] C1 表观指数
  0.0575（R² 0.9944、ΔAIC −156.7）、C4s2 0.5330（R² 0.9784、
  ΔAIC −67.4）；[50,500] 0.0615/0.6090（ΔAIC −98.4）；
  [100,500] 0.0627/0.6467（ΔAIC −100.4）。
- G 值：C4s1 1.614、C4s1p5 1.133、C4s2 0.883、C4p 1.464、
  C4u 0.157（分子一律为 C1）。
- 档位结论 T2：主口径 G=0.883 < 1 但指数距离 0.476（窗口
  [50,500]/[100,500] 下 0.548/0.584）远大于 0.5·b_FSRS=0.029
  阈值，故非 T3；三分布一致 T2（D1 σ=1/1.5 与 D2 直接落
  T2 档，D3 指数距离 0.1205 > 0.029 亦为 T2）。
- 干预限定：EE 格 grid 干预可识别性恢复，v53“阈值从不触发”
  结论须加 EE 异质限定；FSRS 格仍全零干预。

## 5. 新增 §5.8：实证验证 Tier 1（B 线，E）

- 口径：只用在手数据，不重做校准（949 天墙不动），不改模拟器
  公式，不重跑 PPO；GPH / 局部 Whittle 只作方法名，不进参考文献。
- B-1a：主口径 CALIB 等级变化日 408 冲击，8/8 通过——峰度
  105.29–112.16（基准 ΔlogVIX 9.68）、Hill 1.54–1.59/1.15–1.18
  （基准 2.89/3.11）、ACF1 0.184–0.203（基准 0.200）、显著
  lag 9–10 个、τ 3.9–4.6（R² 0.86–0.92，基准 τ 9.4，τ 比
  2.1–2.4 倍在 3 倍软带内）；如实写模拟尾部比基准更极端系
  高斯核+跳变混合结构；敏感性：每日施加复现基准、STEP2
  四档通过、vxo 通过、仅上穿日注入时聚类与 τ 不通过
  （ACF1 0.040、R² 0.44）。
- B-1a 修正记录：原 json 的 r 排除了跳变（prev 取在跳变之后），
  初版“全不通过”已作废；修正为冲击日 r += log(mult)，
  修正前原貌保存在 stage2b_dao_originals.zip 内；
  仅 r 受影响，B-1b 与 B-2 模拟侧不受此 bug 影响。
- B-1b：同质格退化（R_std 恒为 0，记为退化非 0）；
  FSRS 格不适用（S 撞 36500 上限致 R_std 仅 145/9301 tick
  非零、最晚 152 天，早期汇总的 CL/Tau 8/8 系零主导伪影
  已推翻）；EE 格为真实压力序列，聚类与 τ 8/8
  （ACF1 约 0.98、τ 约 86–97、R² 0.99），肥尾随 σ 增大消失
  （σ=1 时 6/8、σ=1.5/2 时 0/8）；lev_std 是 R 的仿射函数
  故无独立信息；两 engine 杠杆标度不同不跨 engine 比绝对值。
- B-2：无一格通过——真实侧 logVIX 全样本 T=9301，
  GPH 0.580、渐近 CI [0.452, 0.709]、带宽漂移 0.260、
  LW 顶格 0.499 boundary_censored；§4.4 预设的 d≈0.3–0.4
  前提不成立；模拟侧 EE GPH 0.642–0.752、LW 顶格；
  模拟侧 FSRS 不适用（T=153–156）；block bootstrap
  （块长 20）对长记忆序列失效、中心约 0，须以渐近 CI
  为 operative 依据；B-1a 收益滚动波动率敏感性
  GPH 0.296/LW 0.313 但漂移 >0.1 故不下结论。

## 6. 新增 limitations 13–18（F，接在现有条目之后，现有条目原文未动）

现有 limitations 编号为 1–12（其中 10 在 12 之后，属 v53 原貌，
未动）；新条目从 13 起连续编号，接在条目 10 之后：

- 13. §5.1 基线非同质（FSRS avg_S 19.70 vs EE 45.0）。
- 14. §5.6.2 的“100 agents”写法无归档支撑（归档 MC 实为
  2 agent/run；人口 MC 数字与 v53 的 27/30、30/30 不可混比）。
- 15. 治理层潜在 UnboundLocalError（从未触发，因集体 avg_R
  全程 >0.25；全部 v54 run 已关闭监控）。
- 16. B-2 基准出带与 bootstrap 限定。
- 17. FSRS 饱和致 B-1b 不适用。
- 18. sens_daily C3 格 OverflowError（int(interval×EF) 复利至
  inf，确定性，核心冻结不修，主口径不受影响）。

## 7. 文首 header（G）

改为 v54 draft、2026-10-25，词数 16863（实测），
并注明 v43–v53 preserved unchanged for provenance。

## 8. 未做清单（硬约束自查）

- 未改 v53 任何数字、表格、结论、参考文献条目：
  Appendix B 逐字一致，DOI 提及数 30 = 30。
- 未新增参考文献，未新增 DOI，未写 T3 式标题改动。
- 未动 repo、dao pack、results jsons、tex、cover letter。
- 未写 V54_RESULTS.md。

## 9. 交稿前自验（全部通过）

1. v53 md5 动工前后一致：48979d0eefddb2e7590a78fa04363803。
2. 新稿 POSIX 词数 16863，与 header 一致；CRLF；755 行。
3. diff（去 CR 后）：仅 3 行改动（Submission Date、Word Count、
   摘要段落），其余全部为新增插入。
4. 全部数字与 results / 阶段报告逐项对过：A-500、A-grid、
   A-mc、A-10y 均值与 >0.85 比例、B-1a 区间、B-1b 饱和
   （145/9301、最晚 152 天）、B-2（GPH 0.580 独立重算一致、
   扫带宽 0.53→0.79）、形状拟合与指数距离（含均匀格
   0.1205 复算一致）。
5. 新增 limitation 编号 13–18 连续，现有条目原文未动。
6. 标题与 v53 逐字一致。

## F1 fix batch (2026-10-25, after Gemini + Qwen web review, both NEEDS_WORK)

Web review verdicts: Gemini Argon (gemini.google.com/app/4a0c666b4f4faa4f) and
Qwen3.8-Max deep (discovery chat/1464197) both NEEDS_WORK; T2 arithmetic confirmed
by both routes. Joint adjudication: fixes below, all inside v54 (no version bump).
Pre-F1 backup: JEDC_submission_draft_FSRS_FINAL_v54_preF1.md. Script: apply_f1.py.

1. Section 5.7 prose: two-point 28x -> 29x (29.11x from 0.77844/0.02674; 28x was the
   design-phase analytic budget, not a run result).
2. Section 5.7: window shape-fit table added ([10,500]/[50,500]/[100,500] with C1 and
   C4 sigma=2 b, R^2, dAIC, distance, threshold); tier paragraph thresholds corrected
   to 0.029/0.031/0.031 per window.
3. Section 5.8: daily-shock sentence qualified as FSRS cell + pointer to limitation 18.
4. Section 5.8: correction record notes 71/72 files; B-2 sample-size note added
   (9282 = 9301 - 19 rolling window; FSRS transient 153-156 vs raw 145 days).
5. Cross-section updates: limitations 2/3/5 (v54-update wording), section 6.5 completed
   items removed with a completion note, section 7 dual caliber + v54 summary +
   limitations paragraph + future list item 3, section 6.1 Anderson & Tweney pointer
   to 5.7, section 1 roadmap, Appendix A v54 data availability, section 6.4 numbering
   reordered to 1-18 (content numbers unchanged).
6. Section 5.8 uncited-methods sentence replaced; Appendix B gains a Long-Memory
   Econometrics subsection (Geweke & Porter-Hudak 1983, DOI 10.1111/j.1467-9892.1983.tb00371.x;
   Künsch 1987, DOI 10.1515/9783112314227-005; Robinson 1995, DOI 10.1214/aos/1176324317;
   all three verified via Crossref).

Result: 17,321 words (POSIX wc -w), SHA256
7891accb1dfd05070e98738ed0950610e7453f0d9779a2daae99949916c857bf. v53 untouched.
Strategic items NOT in F1 (separate decisions): v55-scale rewrite, core unfreeze +
L15/L18 fixes + reruns, price feedback.
