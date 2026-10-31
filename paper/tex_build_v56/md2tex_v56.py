#!/usr/bin/env python3
"""Convert the v52 markdown manuscript to LaTeX (JEDC submission tex).

Faithful conversion: same sections, same order, same numbers, same tables,
same figures. No new claims. Run: python3 md2tex.py
Writes ~/workspace/jedc_push/paper/JEDC_submission_FSRS_FINAL_v52.tex
"""
import re
import sys

SRC = '/home/hatch/workspace/jedc_push/paper/JEDC_submission_draft_FSRS_FINAL_v55.md'
DST = '/home/hatch/workspace/jedc_tex_build_v56/JEDC_submission_FSRS_FINAL_v56.tex'

UNI_TEXT = {
    '\u2014': '---', '\u2013': '--', '\u00b1': r'$\pm$', '\u00b7': r'$\cdot$',
    '\u2192': r'$\rightarrow$', '\u2212': '$-$', '\u2208': r'$\in$',
    '\u2248': r'$\approx$', '\u2264': r'$\leq$', '\u2265': r'$\geq$',
    '\u00d7': r'$\times$', '\u2227': r'$\wedge$', '\u03b3': r'$\gamma$',
    '\u03bb': r'$\lambda$', '\u03c1': r'$\rho$', '\u03b1': r'$\alpha$', '\u03b4': r'$\delta$',
    '\u2026': r'\ldots', '\u00a7': r'\S', '\u00ae': r'\textregistered',
    '\u0394': r'$\Delta$', '\u03c3': r'$\sigma$', '\u03c4': r'$\tau$',
    '\u2032': r"$'$", '\u2033': r"$''$", '\u221a': r'$\sqrt{}$',
    '~': r'$\sim$',
}
UNI_MATH = {
    '\u2014': '-', '\u2013': '-', '\u00b1': r'\pm', '\u00b7': r'\cdot',
    '\u2192': r'\rightarrow', '\u2212': '-', '\u2208': r'\in',
    '\u2248': r'\approx', '\u2264': r'\leq', '\u2265': r'\geq',
    '\u00d7': r'\times', '\u2227': r'\wedge', '\u03b3': r'\gamma',
    '\u03bb': r'\lambda', '\u03c1': r'\rho', '\u03b1': r'\alpha', '\u03b4': r'\delta',
    '\u2026': r'\ldots', '\u00a7': r'\S', '\u00ae': r'\textregistered',
    '\u0394': r'\Delta', '\u03c3': r'\sigma', '\u03c4': r'\tau',
    '\u2032': "'", '\u2033': "''", '\u221a': r'\sqrt',
    '~': r'\sim',
}


def apply_uni(s, table):
    for k, v in table.items():
        s = s.replace(k, v)
    return s


def map_text_uni(seg):
    # v55: √252 means sqrt(252): bind the digits into the root first,
    # then the generic table (lone √ falls back to an empty root).
    seg = re.sub(chr(0x221a) + r'(\d+)', lambda m: '$\\sqrt{' + m.group(1) + '}$', seg)
    return apply_uni(seg, UNI_TEXT)


def escape_text(s):
    """Escape tex specials in a text segment. Markdown escapes render as
    literal chars; dollar, percent, underscore, amp, hash keep tex form."""
    reps = {'\\(': '\x01', '\\)': '\x02', '\\[': '\x03', '\\]': '\x04',
            '\\$': '\x05', '\\%': '\x06', '\\_': '\x07', '\\&': '\x08',
            '\\#': '\x09', '\\*': '\x0a', '\\`': '\x0b'}
    for k, v in reps.items():
        s = s.replace(k, v)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, rep in [('{', r'\{'), ('}', r'\}'), ('#', r'\#'),
                    ('%', r'\%'), ('&', r'\&'), ('_', r'\_'),
                    ('^', r'\^{}')]:
        s = s.replace(ch, rep)
    restores = {'\x01': '(', '\x02': ')', '\x03': '[', '\x04': ']',
                '\x05': r'\$', '\x06': r'\%', '\x07': r'\_', '\x08': r'\&',
                '\x09': r'\#', '\x0a': '*', '\x0b': "'"}
    for k, v in restores.items():
        s = s.replace(k, v)
    return s


def inline(s, allow_path=True, _slots=None):
    r"""Convert one prose chunk (may contain $math$, `code`, **bold**, *ital*).
    allow_path=False for moving arguments (captions, headings): \path is
    fragile there (\url used in a moving argument) so code stays \texttt."""
    # v55 fix: slots must be shared with recursive inline() calls from
    # markup_prepass, else a placeholder created by an outer stash (e.g.
    # a stashed $S_0^*$ span inside an italic span) crashes the inner
    # call's restore with IndexError.
    slots = _slots if _slots is not None else []

    def stash(final):
        slots.append(final)
        return '\x1e%d\x1f' % (len(slots) - 1)

    def markup_prepass(s, pattern, wrapper):
        def repl(m):
            inner = m.group(1)
            if '$' not in inner:
                return m.group(0)
            return stash(wrapper + '{' + inline(inner, _slots=slots) + '}')
        return re.sub(pattern, repl, s)

    # The manuscript uses \(...\) as LaTeX inline-math delimiters (12 pairs,
    # all outside $...$ spans): convert them to $...$ before splitting.
    s = s.replace('\\(', '$').replace('\\)', '$')
    # Bare currency amounts ($7,091.30 with no closing $) are NOT math:
    # protect them before $ splitting, or the lone $ swallows everything
    # up to the next math $ and breaks compilation. The negative lookaheads
    # keep real math spans intact: after the number must NOT come a digit,
    # $, \, ^, _, a letter, or a decimal point followed by a digit (so
    # "$7.7\times$" and "$0.000015$" never match, even by backtracking),
    # nor whitespace followed by a math token (so "$1.5 \times 10^{-5}$"
    # never matches either).
    s = re.sub(r'\$(\d[\d,]*(?:\.\d+)?)(?![\d$\\^_a-zA-Z])(?!\.\d)'
               r'(?!\s*[\\+\-*=<>_^])',
               lambda m: stash('\\$' + m.group(1)), s)
    # v55 additions: dollar + unicode minus + amount ($-99,479.66), and
    # dollar amount + letter suffix with no closing $ (~$90k edge).
    s = re.sub('\\$' + chr(0x2212) + r'(\d[\d,]*(?:\.\d+)?)',
               lambda m: stash('\\$$-$' + m.group(1)), s)
    s = re.sub(r'\$(\d[\d,]*(?:\.\d+)?)(k|m|bn)\b(?!\$)',
               lambda m: stash('\\$' + m.group(1) + m.group(2)), s)
    # v55 fix: a '*' inside a math span (e.g. $S_0^*$) must never act as
    # an italic marker for markup_prepass (it used to swallow up to the
    # next '*' in the paragraph and mangle the math). Stash such spans
    # first, with UNI_MATH applied, so they survive verbatim.
    # NOTE: do NOT use a bare \$[^$]*\*[^$]*\$ search here: it can start
    # at the closing $ of an earlier math span and swallow the text up to
    # the next $ (e.g. "$S_0$, strength \u03b1, and **$" got stashed as
    # "math", eating the bold markers and dropping $\alpha$'s dollars).
    # Match real $...$ spans leftmost-first and stash only starred ones.
    def stash_math_star(m):
        span = m.group(0)
        return stash(apply_uni(span, UNI_MATH)) if '*' in span else span
    s = re.sub(r'(?<!\\)\$[^$\n]+\$', stash_math_star, s)
    # v55 fix: bare S0* is star notation in prose, not an italic marker
    # (it used to pair with the next S0* and swallow a paragraph into
    # \textit). Stash it as math before markup_prepass runs.
    s = re.sub(r'S0\*(?!\*)', lambda m: stash('$S_0^*$'), s)
    s = markup_prepass(s, r'\*\*([^*]+?)\*\*', r'\textbf')
    s = markup_prepass(s, r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\textit')
    parts = re.split(r'(\$[^$\n]+\$)', s)
    out = []
    code_slots = []

    def protect_code(seg):
        def repl(m):
            content = m.group(1)
            # File paths in \texttt cannot break across lines, which
            # produced up to 186pt overfull boxes; \path (from url, loaded
            # via hyperref) breaks at slashes. Paths here contain only
            # letters, digits, _, ., / so \path is safe for them.
            if (allow_path and '/' in content and content.isascii()
                    and not re.search(r'[%#\\{}]', content)):
                code_slots.append(r'\path{' + content + '}')
            else:
                code_slots.append(r'\texttt{' + map_text_uni(escape_text(content)) + '}')
            return '\x1c%d\x1d' % (len(code_slots) - 1)
        return re.sub(r'`([^`]+)`', repl, seg)

    for part in parts:
        if part.startswith('$') and part.endswith('$') and len(part) > 1:
            out.append(apply_uni(part, UNI_MATH))
        else:
            seg = protect_code(part)

            def url_repl(m):
                u = m.group(0)
                trail = ''
                while u and u[-1] in '.,)':
                    trail = u[-1] + trail
                    u = u[:-1]
                return stash(r'\url{' + u + '}') + trail

            seg = re.sub(r'https?://\S+', url_repl, seg)
            # Bare LaTeX commands in prose (e.g. 12.1\times, **47,000\times**):
            # stash them as math so escaping cannot mangle the backslash.
            seg = re.sub(
                r'\\(times|in|approx|pm|sim|cdot|leq|geq|rightarrow|'
                r'alpha|beta|gamma|lambda|rho|propto|infty)\b',
                lambda m: stash('$\\' + m.group(1) + '$'), seg)
            seg = re.sub(r'\\text\{([^{}]*)\}',
                         lambda m: stash(r'$\text{' + m.group(1) + '}$'),
                         seg)
            seg = escape_text(seg)
            seg = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', seg)
            seg = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'\\textit{\1}', seg)
            seg = re.sub(r'"([^"]+)"', r"``\1''", seg)
            seg = map_text_uni(seg)
            seg = re.sub(r'\x1c(\d+)\x1d',
                         lambda m: code_slots[int(m.group(1))], seg)
            seg = seg.replace('`', "'")
            out.append(seg)
    joined = ''.join(out)
    joined = re.sub(r'\x1e(\d+)\x1f',
                    lambda m: slots[int(m.group(1))], joined)
    return joined


def strip_number(h):
    return re.sub(r'^\d+(\.\d+)*\.?\s+', '', h).strip()


def main():
    lines = open(SRC, encoding='utf-8').read().splitlines()
    title = lines[0].lstrip('# ').strip()
    body = []          # tex lines for the main document
    bib_groups = []    # (group, [(label, key, text)])
    state = 'pre'      # pre | abstract | main | ack | appA | appB
    cur_group = None
    pending_fig = None
    para = []
    lst = None         # (kind, [items])
    table = None       # [rows]

    def flush_para():
        nonlocal para
        if para:
            body.append(inline(' '.join(para)))
            body.append('')
            para = []

    def flush_list():
        nonlocal lst
        if lst:
            kind, items = lst
            env = 'itemize' if kind == 'dash' else 'enumerate'
            body.append('\\begin{%s}' % env)
            for it in items:
                body.append('\\item ' + inline(it))
            body.append('\\end{%s}' % env)
            body.append('')
            lst = None

    def flush_table():
        nonlocal table
        if table:
            header, rows = table[0], table[1:]
            ncol = len(header)
            for r in rows:
                assert len(r) == ncol, 'table col mismatch: %r vs %d' % (r, ncol)
            body.append('\\begin{table}[htbp]')
            body.append('\\centering')
            body.append('\\begin{tabular}{%s}' % ('l' * ncol))
            body.append('\\toprule')
            body.append(' & '.join('\\textbf{' + inline(c) + '}'
                                   for c in header) + r' \\')
            body.append('\\midrule')
            for r in rows:
                cells = [inline(c) for c in r]
                # v55: a row starting with '[' after the previous row's \\
                # would be read as \\ [<dim>] (row spacing) -> illegal
                # unit error. Shield it with an empty group.
                if cells and cells[0].startswith('['):
                    cells[0] = '{}' + cells[0]
                body.append(' & '.join(cells) + r' \\')
            body.append('\\bottomrule')
            body.append('\\end{tabular}')
            body.append('\\end{table}')
            body.append('')
            table = None

    def flush_all():
        flush_para()
        flush_list()
        flush_table()

    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if s == '```':
            flush_all()
            fence = []
            i += 1
            while i < n and lines[i].strip() != '```':
                fence.append(lines[i])
                i += 1
            body.append(r'\[')
            body.append(r'\begin{aligned}')
            for fl in fence:
                if '#' in fl:
                    form, comment = fl.split('#', 1)
                else:
                    form, comment = fl, ''
                form = form.strip()
                form = form.replace('pre_avg_R', r'\mathrm{pre\_avg\_R}')
                form = form.replace('avg_R', r'\mathrm{avg\_R}')
                form = form.replace('R_std', r'\mathrm{R\_std}')
                form = apply_uni(form, UNI_MATH)
                form = form.replace('[', r'\left[').replace(']', r'\right]')
                # TeX control words eat following letters: "2\cdotseverity"
                # would parse as the undefined command \cdotseverity.
                form = re.sub(r'\\cdot(?=[a-zA-Z])', r'\\cdot ', form)
                if comment.strip():
                    body.append(form + r' &\text{' + comment.strip() + r'} \\')
                else:
                    body.append(form + r' \\')
            body.append(r'\end{aligned}')
            body.append(r'\]')
            body.append('')
            i += 1
            continue
        if s == '$$':
            flush_all()
            math_lines = []
            i += 1
            while i < n and lines[i].strip() != '$$':
                math_lines.append(lines[i].strip())
                i += 1
            body.append(r'\[')
            body.append(apply_uni(' '.join(math_lines), UNI_MATH))
            body.append(r'\]')
            body.append('')
            i += 1
            continue
        if s == '':
            flush_all()
            i += 1
            continue
        if s == '---':
            flush_all()
            i += 1
            continue
        m = re.match(r'^!\[(.*?)\]\((.*?)\)\{#fig:(.*?) width=(\d+)%\}$', s)
        if m:
            flush_all()
            fname = m.group(2).split('/')[-1]
            label = m.group(3)
            width = int(m.group(4))
            # In-text references use the md's figure numbers, which do NOT
            # match appearance order (5, 2, 4, 1, 6): force the counter.
            fig_num = {'fig5_grade_impact_v47.png': 5,
                       'fig5_grade_impact_v55.png': 5,
                       'fig2_grid_search.png': 2,
                       'fig4_fsrs_vs_ee.png': 4,
                       'fig1_trajectory.png': 1,
                       'fig6_fsrs_vs_ee_10year.png': 6,
                       'fig6_fsrs_vs_ee_10year_v55.png': 6}[fname]
            # Look ahead: only a "**Figure N.** ..." paragraph directly
            # after the image is a caption. "**Figure 1** displays ..." is
            # prose (bold subject, no period) and must NOT be consumed.
            cap = None
            j = i + 1
            while j < n and lines[j].strip() == '':
                j += 1
            if j < n and re.match(r'^\*\*Figure \d+(\s+\(v\d+\))?\.\*\*',
                                  lines[j].strip()):
                cap = re.sub(r'^\*\*Figure \d+(\s+\(v\d+\))?\.\*\*\s*', '',
                             lines[j].strip())
                i = j
            body.append('\\setcounter{figure}{%d}' % (fig_num - 1))
            body.append('\\begin{figure}[htbp]')
            body.append('\\centering')
            body.append('\\includegraphics[width=%.2f\\textwidth]{%s}'
                        % (width / 100.0, fname))
            if cap is not None:
                body.append('\\caption{%s}' % inline(cap, allow_path=False))
                body.append('\\label{fig:%s}' % label)
            body.append('\\end{figure}')
            body.append('')
            i += 1
            continue
        if s.startswith('#'):
            flush_all()
            depth = len(s) - len(s.lstrip('#'))
            head = s.lstrip('#').strip()
            if depth == 1:
                i += 1
                continue
            if head == 'Abstract':
                state = 'abstract'
                body.append('\\begin{abstract}')
            elif head == 'Acknowledgments':
                state = 'ack'
                body.append('\\section*{Acknowledgments}')
            elif head.startswith('Appendix A'):
                state = 'appA'
                body.append('\\appendix')
                body.append('\\section{Data Availability}')
            elif head.startswith('Appendix B'):
                state = 'appB'
                body.append('\\section{References}')
                body.append('\\begin{thebibliography}{99}')
            elif state == 'appB':
                cur_group = head
                bib_groups.append((cur_group, []))
                body.append('\\subsection{%s}' % inline(head, allow_path=False))
            elif state == 'abstract':
                body.append('\\end{abstract}')
                state = 'main'
                body.append('\\section{%s}' % inline(strip_number(head), allow_path=False))
            else:
                if state == 'abstract':
                    body.append('\\end{abstract}')
                    state = 'main'
                body.append('\\section{%s}' % inline(strip_number(head), allow_path=False)
                        if depth == 2 else
                        '\\subsection{%s}' % inline(strip_number(head), allow_path=False)
                        if depth == 3 else
                        '\\subsubsection{%s}' % inline(strip_number(head), allow_path=False))
            i += 1
            continue
        if s.startswith('> '):
            flush_all()
            quotes = []
            while i < n and lines[i].strip().startswith('> '):
                quotes.append(lines[i].strip()[2:].strip())
                i += 1
            body.append('\\begin{quote}')
            body.append(inline(' '.join(quotes)))
            body.append('\\end{quote}')
            body.append('')
            continue
        if s.startswith('|'):
            if para:
                flush_para()
            if lst:
                flush_list()
            cells = [c.strip() for c in re.split(r'(?<!\\)\|',
                                                s.strip('|'))]
            if all(re.match(r'^:?-{2,}:?$', c) for c in cells):
                i += 1
                continue
            if table is None:
                table = []
            table.append(cells)
            i += 1
            continue
        if table is not None:
            flush_table()
        if state == 'appB' and s.startswith('- '):
            if para:
                flush_para()
            if lst:
                flush_list()
            entry = s[2:].strip()
            m2 = re.match(r'^(.*?)\s*\((\d{4})[a-z]?\)', entry)
            if m2:
                first = m2.group(1).split(',')[0].strip()
                label = '%s (%s)' % (first, m2.group(2))
                key = re.sub(r'[^a-z0-9]', '', first.lower()) + m2.group(2)
            else:
                label, key = 'anon', 'anon'
            body.append('\\bibitem[%s]{%s} %s' % (label, key, inline(entry)))
            i += 1
            continue
        dm = re.match(r'^- ', s)
        nm = re.match(r'^(\d+)\. ', s)
        im = re.match(r'^  - ', ln)
        if dm or nm or im:
            if para:
                flush_para()
            kind = 'dash' if (dm or im) else 'num'
            if lst is None or lst[0] != kind:
                flush_list()
                lst = (kind, [])
            text = re.sub(r'^(  - |- |\d+\. )', '', s if not im else s.strip())
            lst[1].append(text)
            i += 1
            continue
        if lst is not None and s and not s.startswith('#'):
            lst[1][-1] += ' ' + s
            i += 1
            continue
        if state == 'pre':
            i += 1
            continue
        para.append(s)
        i += 1

    flush_all()
    if state == 'abstract':
        body.append('\\end{abstract}')
    if state == 'appB':
        body.append('\\end{thebibliography}')

    out = []
    out.append('\\documentclass[11pt]{article}')
    out.append('\\usepackage[margin=1in]{geometry}')
    out.append('\\usepackage[utf8]{inputenc}')
    out.append('\\usepackage[T1]{fontenc}')
    out.append('\\usepackage{amsmath,amssymb,amsthm}')
    out.append('\\usepackage{booktabs}')
    out.append('\\usepackage{graphicx}')
    out.append('\\graphicspath{{../figures/}{figures/}}')
    out.append('\\usepackage{hyperref}')
    out.append('\\usepackage{parskip}')
    out.append('\\setlength{\\parindent}{0pt}')
    out.append('\\setlength{\\parskip}{1ex}')
    out.append('')
    out.append('\\title{%s}' % inline(title, allow_path=False))
    out.append('\\author{MinQian Cai}')
    out.append('\\date{Submitted to \\textit{Journal of Economic Dynamics '
               'and Control}\\\\Draft: 2026-10-31 (v55)}')
    out.append('')
    out.append('\\begin{document}')
    out.append('\\maketitle')
    out.append('')
    out.extend(body)
    out.append('\\end{document}')
    open(DST, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('wrote', DST)
    print('bibitems:', sum(1 for ln in body if ln.startswith('\\bibitem')))
    print("pending_fig removed")


if __name__ == '__main__':
    main()
