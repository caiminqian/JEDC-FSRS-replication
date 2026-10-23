# CHANGELOG v50 (2026-10-24)

Post-fix environment reruns (Step 1 of the strengthening plan).

Fix: `ECOSControlEnv._compute_obs` — an agent with no predecessors now gets
perceived R = true R exactly (previously (1-alpha) * true R = 0.4 * true R);
plus a `has_node` guard. Commit 7ee820c in caiminqian/JEDC-FSRS-replication.
The fix is merged into the replication pack `src/`; v49 tag is unaffected.

Reruns (all S=45, scripts unchanged, outputs `*_fix.json` in the pack):
- p/S sweep: all 9 cells p-independent (S30 -201.83, S45 -142.03, S60 -100.25;
  zone 0, interventions 0). The pre-fix p=0.05 positive returns
  (1737/1534/1316, zone ~25%) were entirely the isolated-agent artifact.
- Paired S=45: all 4 entries -142.03 (pre-fix -314.71/-304.23), zone 0,
  interventions 0. No optimum identified; conclusion unchanged.
- Grid S=45: all 24 configurations -142.03 (pre-fix spread -325.19 to -247.56),
  zone 0, interventions 0. Threshold/severity parameters completely inert.
- 1000-agent S=45: bit-identical to the v49 pre-fix rerun
  (-1065.3521728515625 both policies, interventions 0, zone 0, improvement
  0.0%; runtimes 469 s / 600 s). Fix is a no-op at 1000 agents (dense graph,
  essentially no isolated nodes).

Manuscript: abstract, Sections 4.1/4.3, 5.1 (paired + grid), 5.2 (stress),
5.3 (sweep), 6.2, 6.4 (limitations 6 and 11), and Section 7 updated.
Section 5.5 experiments need no post-fix rerun (they do not use
ECOSControlEnv._compute_obs). Pre-fix numbers retained and labelled as audit.
