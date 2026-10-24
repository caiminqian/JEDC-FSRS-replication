# tex sync for v52 (Step 4, part 1)

- Source: `JEDC_submission_draft_FSRS_FINAL_v52.md` (12,182 words), converted
  by `md2tex.py` to `JEDC_submission_FSRS_FINAL_v52.tex`. The v43-era tex
  (`JEDC_submission_FSRS_FINAL_v43_final_clean.tex`) is untouched.
- Content: same sections, order, numbers, tables, and figures as v52 md.
  Title, author (MinQian Cai), and date updated to v52. Keywords drop
  "macroprudential policy" as in v52. Old tex claims (15.0% optimal policy,
  374%, 47,867x, calibrated S=45) are gone because the v52 text does not
  contain them.
- Figures: all 5 md images; numbers forced with `\setcounter` to match the
  md's in-text numbers (appearance order 5, 2, 4, 1, 6). fig4 and fig1 have
  no caption, as in the md (their descriptions are prose). Captions for
  fig5/fig2/fig6 are the md's caption paragraphs minus the "Figure N."
  prefix (LaTeX supplies it). `\graphicspath{{../figures/}{figures/}}`
  so the file compiles from `paper/` or from the pack root.
- References: md Appendix B converted to `thebibliography` (26 entries,
  same 6 groups); `references.bib` is retained in the folder but the tex
  does not use it (the md's citations are author-year prose, not keys).
- Verification (mine + independent review): section parity 1:1; number
  parity exact (-142.03: 13=13, -1065.35: 6=6, 47,000: 6=6, 0.7185: 5=5,
  0.000015: 8=8, 3947: 8=8, 3434: 7=7); 12 tables with matching column/row
  counts; braces balanced; dollar count even; all environments balanced;
  no leftover markdown markers or mangled commands.
- Review adjudication: independent review VERDICT: PASS with one MED
  (stray markdown blockquote ">" at the Terminology note) and three LOWs.
  MED fixed in the converter (blockquote now a `quote` environment) and
  regenerated. One LOW fixed as well (URL trailing punctuation ")."/"."
  in Appendix A was dropped by the first converter version; now preserved).
  Two LOWs accepted as faithful to the md and left as-is: the section 3.2
  contagion formula stays in the md's text-mode form, and prose identifiers
  keep literal underscores.
- Cover letter: rewritten as `cover_letter_v52.md` (old April letter
  untouched): v52 title, memory-contest framing, both negative control
  results, calibration gap stated, GitHub + Zenodo v52 DOI.
- KNOWN LIMITATION: compilation was NOT verified. No LaTeX engine exists
  in the sandbox (no pdflatex/xelatex/lualatex/tectonic). All checks above
  are static. Before submission, compile once (Elsevier's system or a
  local TeX install) and fix any error there; do not claim it compiles
  until that run succeeds.
- Submission itself is NOT part of this change and needs its own approval.
