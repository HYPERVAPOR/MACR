# AGENTS.md — papers/mid-term

Conventions for AI agents working on the MACR mid-term paper project.

## Scope

This directory contains a structured academic paper writing project and a Chinese mid-term report. Content is authored in Markdown + YAML, references in BibTeX, and PDFs are produced via Pandoc + XeLaTeX using conference-specific LaTeX templates.

## Editing Rules

1. **Content lives in `sections/`**: Edit the modular Markdown files (`abstract.md`, `introduction.md`, etc., and `report_*.md` for the mid-term report). Do not put long-form content directly in `paper.md` or `report.md` unless it is a deliberate one-off exception.
2. **Metadata lives in `metadata.yaml`**: Title, authors, abstract, keywords, and venue information go here. Keep author schema consistent (name, affiliation, country, email).
3. **References go in `references.bib`**: Use standard BibTeX. Prefer conference/journal entries over arXiv when a peer-reviewed version exists.
4. **Figures are generated, not committed**: Add generation scripts to `figures/` and register them in `figures/generate_all.py`. Do not commit generated PDF/PNG/PGF files to Git.
5. **Do not commit build artifacts**: `build/` and `figures/output/` are gitignored except for `.gitkeep` markers.

## Build Verification

After any non-trivial change, run:

```bash
make clean && make all
```

All four PDFs (IEEE, ACM, ACL, and the Chinese mid-term report) must compile without errors. Warnings about missing characters or overfull boxes should be minimized.

## Citation and Cross-References

- This project uses **CSL** via pandoc `--citeproc`, not `pandoc-crossref`.
- Use explicit numbering for cross-references (e.g., "Figure 1", "Table 1", "Section 3").
- Avoid `@fig:`, `@sec:`, `@tbl:` syntax unless `pandoc-crossref` is installed and configured.

## Templates

- `templates/ieee/template.tex` — IEEEtran conference format
- `templates/acm/template.tex` — ACM acmart sigconf format
- `templates/acl/template.tex` — ACL article format
- `templates/report/template.tex` — Chinese mid-term report (ctexart)

Each template includes pandoc CSL/citeproc definitions, tight-list support, syntax-highlighting macros, and a table-to-float Lua filter. Be cautious when modifying shared LaTeX snippets; test all three formats after changes.

## Adding New Figures

When adding a figure:

1. Create `figures/figure_<name>.py` with a `main()` function.
2. Save output to `figures/output/` as PDF (or PGF for TikZ).
3. Register the script in `figures/generate_all.py`.
4. Reference the figure in the relevant `sections/*.md` file with explicit text.
5. Run `make figures` to regenerate.

## Mid-term Report

The report (`report.md`) uses `templates/report/template.tex` and `filters/table-report.lua` for single-column Chinese layout. Report-specific figures are generated alongside paper figures by `figures/generate_all.py`.

## Dependencies

- `pandoc`, `xelatex`, `make`, `python3`
- Python package: `matplotlib`
- For the Chinese report: `ctex` package (usually included in TeX Live)

Do not install global TeX Live packages without confirming with the user; the project bundles required `.cls`/`.sty` files under `templates/latex-classes/`.
