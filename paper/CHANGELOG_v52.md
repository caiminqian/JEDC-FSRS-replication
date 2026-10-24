# CHANGELOG v52（B：重构叙事，不重做数据，2026-10-24）

- make_v52.py：先全篇节号重映射（占位符防二次偏移），再 §5
  移块改标题，最后重写摘要/§1/§2.4/§6.1/§6.2/§7。
  v51 11,846 词 → v52 12,182 词，md5 e05af7f1a1c6e33f2044dbb03289aa84。
  （评审后修正：见 adjudication；词数 +2 来自 §6.5 bullet 改写。）
- 标题：`Long Memory in Agent-Based Markets: FSRS Power-Law Forgetting
  vs Ebbinghaus Decay, and Why Control Fails to Bite`。
- §5 重排（内容不动）：5.1 FSRS vs EE（原 5.1.3 升格）、5.2 Control
  Probe I: Threshold Grid（原 5.1）、5.3 Scale Robustness（原 5.2）、
  5.4 Robustness sweep（原 5.3）、5.5 Control Probe II: Why RL Failed
  （原 5.4）、5.6 Extended Validation（原 5.5，含 5.6.1–5.6.4）。
  全篇节号引用同步重映射；范围引用按意图处理（limitation 11 的
  5.1-5.3 → 5.2-5.4；limitation 12 的 5.1-5.5 → 5.1-5.6）。
- 重写：摘要（记忆模型之争打头，47,000×、非干预、校准未识别）、
  §1 贡献 4/5 与路线图、§2.4（探针背景）、§3.3（改名探针设置 +
  框架句）、§4.4（改名 Control Probes (Design)）、§6.1（记忆核
  含义）、§6.2（改名 Implications: Model Choice First）、§7
  （三支柱收束）；§6.4 节首加 v52 范围说明；文首元数据更新为
  v52/12,180（旧文首仍写 v48/9723 已过期）。
- 不动：§5 全部数字（配对 -142.03 计 13 次、1000 agent -1065.35
  计 6 次，与 v51 一致；47,000× 与 0.7185 增加的次数均来自新
  摘要/§6.1/§7 的复述）；limitation 1–12 全文；复制包文件；
  tex（Step 4 时按 v52 正文同步）。
- 建造中抓到的自家 bug：范围引用若先替换再跑分量映射会被二次
  偏移（5.2-5.4 曾错成 5.3-5.4）；已改为范围先占位、映射完再按
  意图还原，并经 grep 复验两处范围正确。
- 评审 adjudication（08:39）：独立评审 VERDICT: FAIL，仅 1 类硬伤——
  §4.1/§4.3 两处 "(see Sections 5.3 and 5.5)" 的次元漏改：
  v51 原文 "(see Sections 5.2 and 5.5)" 中次元 5.5 不带 Section
  前缀，我的重映射只处理带前缀的 token，故首元改了、次元漏了；
  我独立验算确认（两句均指 1000-agent + extended 的 S 设置，
  正确应为 5.3 and 5.6）。其余全部通过：§5 顺序标题、数字未动
  （-142.03 13=13、-1065.35 6=6）、叙事一致性、limitation 12
  仅范围一处字符差异。已修：重映射加列表续元通用处理
  （"Sections A and B" 的裸 B 同映射），两处现为 5.3 and 5.6；
  LOW（§6.5 "test optimal policy robustness"）一并改成
  "test whether the non-intervention finding survives"。
  修正后按评审意见直接判 PASS，无需全文重审。
- 待批：留/回滚 → 同步（v52 md + 本 changelog）→ release 另批。
