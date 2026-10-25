# CHANGELOG v53（补 6 篇已核实文献，不动数据与结论，2026-10-25）

依据 `~/workspace/jedc_pack/doi_verification_opencode.md`（opencode 核实报告，
Crossref / doi.org / OpenReview / ICLR virtual / arXiv / OSF API 逐篇复验）。
v52 全部文件（md / tex / changelog / 复制包 / MANIFEST / jedc_build）原地未动，
md5 快照前后一致；本版只新增 v53 草稿文件，不 commit、不 push、不发 release。

- 方法：cp v52 md → v53 md（md5 先相同后改），只改 v53 一个文件；
  tex 由 md2tex 副本生成（见文末）。v52 12,182 词 → v53 12,805 词
  （`LC_ALL=POSIX wc -w` 实测，写进文首 header；v52 的 12,182 不再沿用）。

## 1. 新增 6 篇文献（Appendix B：26 → 32 条）

分组沿用原有 6 组，条目均按核实报告的 suggested bib entry 著录：

- Core Memory & Spaced Repetition（5 → 9）：
  1. Anderson, R. B., & Tweney, R. D. (1997). Artifactual power curves in
     forgetting. *Memory & Cognition*, 25(5), 724–730.
     doi:10.3758/BF03211315（报告 CONFIRMED，原样采纳）。
  2. Wixted, J. T., & Ebbesen, E. B. (1997). Genuine power curves in
     forgetting: A quantitative analysis of individual subject forgetting
     functions. *Memory & Cognition*, 25(5), 731–739.
     doi:10.3758/BF03211316（报告 §7.1 顺带核实；与第 1 篇同刊同卷、
     页码相接（724–730 / 731–739），是直接反驳，正文成对引用）。
  3. Wixted, J. T., & Carpenter, S. K. (2007). The Wickelgren power law
     and the Ebbinghaus savings function [Comment]. *Psychological
     Science*, 18(2), 133–134. doi:10.1111/j.1467-9280.2007.01862.x
     （2 页短评：页码 133–134、7 条参考文献，著录时加 [Comment]，
      不写成长文）。
  4. Kannan, V., & Ravi, N. (2026). *Evaluation of memory decay models
     in spaced repetition data* (EdArXiv preprint). Center for Open
     Science. doi:10.35542/osf.io/5hqc9_v1（明确标注预印本身份）。
- Agent-Based Modeling（5 → 6）：Zheng, M., Liu, R., & Li, Y. (2018).
  Long memory in financial markets: A heterogeneous agent model
  perspective. *International Review of Financial Analysis*, 58,
  38–51. doi:10.1016/j.irfa.2018.04.001。
- Reinforcement Learning & POMDP（3 → 4）：Hamadanian, P.,
  Nasr-Esfahany, A., Schwarzkopf, M., Sen, S., & Alizadeh, M. (2025).
  Online reinforcement learning in non-stationary context-driven
  environments. In *ICLR* (Spotlight). arXiv:2302.02182.
  https://openreview.net/forum?id=l6QnSQizmN（无 Crossref DOI，
  不编造 proceedings DOI，按报告用 OpenReview + arXiv 引用）。

合计 9 + 6 + 6 + 3 + 4 + 4 = 32 条；0 条与原有 26 条重复
（Wixted / Wickelgren / Tweney / Hamadanian / Zheng / Kannan 在 v52
正文与附录均为 0 次）。

## 2. Zheng, Liu & Li 归组理由（ABM 而非 Behavioral Finance）

选 **Agent-Based Modeling** 组。理由：该文是从异质 agent 模型
（HAM）视角解释金融市场 long memory 的综述，机制是 agent 在行为
预测规则间切换，近邻是 Brock & Hommes (1997)、Kirman (1993)、
Lux (1997)、Lux & Marchesi (1999)；而 Behavioral Finance & Memory
组收的是个体偏差类文献（disaster myopia、disposition effect、
availability）。按机制而非按期刊（IRFA）归组。

## 3. 对 Qwen 原始说法的 3 处纠正（只录结论，不采用原说法）

1. IRFA 长记忆篇作者不是 He, Li & Zheng，而是 **Zheng, Liu, & Li
   (2018)**，58:38–51，doi:10.1016/j.irfa.2018.04.001。Qwen 混淆了
   两篇：真正的 He–Li–Zheng 是另一篇更晚的 IRFA 文章
   （*Heterogeneous agent models in financial markets: A nonlinear
   dynamics approach*, 2019, 62:135–149,
   doi:10.1016/j.irfa.2018.11.016）。**本版不引 He/Li/Zheng 2019**，
   仅在此记一笔备查。
2. Hamadanian 等是 **ICLR 2025 Spotlight**（不是 2024），标题全称
   *Online Reinforcement Learning in Non-Stationary Context-Driven
   Environments*，**无 Crossref DOI**；引用走 OpenReview
   （forum id l6QnSQizmN）与 arXiv:2302.02182。
3. Kannan & Ravi (2026) 是 **EdArXiv 预印本**（OSF Preprints,
   Center for Open Science，Crossref posted-content / preprint），
   **不是 PeerJ**；doi:10.35542/osf.io/5hqc9_v1 属实（前缀
   10.35542 为 COS 的 Crossref 前缀，与 DataCite 的 10.17605/OSF.IO
   是两套注册体系，均非伪造）。

## 4. 正文改动（只加不改；标题、数据、数字、表格、结论一律未动）

- §2.2 末：补一句 Zheng, Liu, & Li (2018) 与本文的贡献区分——
  他们是行为规则切换产生聚合层 long memory，本文是 agent 内部的
  认知记忆内核，两者互补不竞争。
- §3.1（FSRS 内核引入处）：补一句引 Wixted & Carpenter (2007)，
  点明幂律形式即 Wickelgren power law、与 Ebbinghaus savings
  function 的关系。
- §5.5（PPO 探针失败处）：补一句引 Hamadanian et al. (2025)，
  把非平稳上下文环境下 online RL 的灾难性遗忘列为叠加因素
  （主诊断仍是稀疏/延迟奖励，句中没有改这一归属）。
- §6.1（讨论）：新增一段，同时呈现 Anderson & Tweney (1997) 的
  聚合假象挑战与 Wixted & Ebbesen (1997) 的个体水平幂律反驳
  （同刊同卷、成对引用），承认群体异质性可能放大幂律与指数的
  表观差异——即该机制既可能放大本文测得的差距，也警告聚合曲线
  不能直接当作个体内核的证据；并如实写入 Kannan & Ravi (2026)
  预印本：个体 Anki 数据上 stretched exponential 占优（76%）、
  自适应调度造成 rate–delay 耦合、Anderson–Tweney 异质性机制
  不足以解释观测曲率——明确写成"对幂律故事的复杂化，不是佐证"，
  未写成支持 47,000× 的表述，也未把该预印本说成已评审。

## 5. 未动项（自查）

- 标题、摘要、§1–§7 全部数据/数字/表格/结论：0 处改动。
- 关键数字出现次数与 v52 完全一致（md 与 tex 分别比对）：
  -142.03 计 13 次、-1065.35 计 6 次、0.7185 计 5 次、
  0.000015 计 8 次、3947 计 8 次、3434 计 7 次；47,000×
  计 6 次（新段落只用"Section 5.1 contrast"指代，不复读数字）。
- 章节结构与 v52 1:1（无新增/删除标题）。
- Appendix A（Zenodo DOI、v52 provenance 句）、limitation 1–12、
  复制包、MANIFEST：未动。
- v52 的 md/tex/changelog/构建目录：未动（md5 快照复验）。

## 6. tex 生成与编译验证

- `md2tex.py`（jedc_pack 原件）未动；另存副本改输入输出为 v53
  （SRC/DST 指向 v53 文件，`\date{}` 草案行同步为 v53 / 2026-10-25）。
- 产物：`~/workspace/jedc_push/paper/JEDC_submission_FSRS_FINAL_v53.tex`
  （v52 tex 未动）。
- 构建目录：`~/workspace/jedc_build_v53/`（tex 副本 + figures 软链
  → ~/workspace/jedc_push/figures，做法同 jedc_build）。
- pdflatex 本机缺失，经 http://127.0.0.1:18082 代理 apt 安装
  texlive-latex-base + texlive-latex-recommended + texlive-fonts-recommended
  （Acquire::Languages=none）；两遍 pdflatex 均 rc=0。
- 结果：32 个 \bibitem（6 新 + 26 旧），页数 / error 数 /
  overfull 警告数见 `jedc_build_v53/BUILD_REPORT_v53.md` 与
  pass1.log / pass2.log。
- 遗留说明：tex 中 bibitem 标签由 md 条目自动生成（如
  `[Anderson (1997)]{anderson1997}`），key 与报告建议一致；
  Wixted & Ebbesen 与 Wixted & Carpenter 的 key 分别为
  wixted1997 / wixted2007，无冲突。

## 7. 明确不做的事

不 commit、不 push、不改 MANIFEST、不碰 dao、不发 release、
不重写 cover letter（投稿时再定）、不修改任何 v52 文件。
