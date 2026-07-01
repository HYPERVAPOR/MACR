# MACR Mid-term Paper Build System
# Usage:
#   make all        - Build figures and all conference-format PDFs
#   make figures    - Generate figures from Python scripts
#   make ieee       - Build IEEE conference format PDF
#   make acm        - Build ACM conference format PDF
#   make acl        - Build ACL conference format PDF
#   make clean      - Remove build artifacts
#   make watch      - Auto-rebuild on file changes (requires entr)

.PHONY: all figures ieee acm acl clean watch help

# Directories
ROOT        := $(CURDIR)
BUILD_DIR   := $(ROOT)/build
FIG_DIR     := $(ROOT)/figures
FILTERS_DIR := $(ROOT)/filters
CSL_DIR     := $(ROOT)/csl
TEMPLATES_DIR := $(ROOT)/templates
LATEX_CLASSES := $(TEMPLATES_DIR)/latex-classes

# Source files
METADATA    := $(ROOT)/metadata.yaml
PAPER       := $(ROOT)/paper.md
BIBLIO      := $(ROOT)/references.bib

# Report source files
REPORT_METADATA := $(ROOT)/report_metadata.yaml
REPORT          := $(ROOT)/report.md

# Output files
IEEE_PDF    := $(BUILD_DIR)/mid-term-ieee.pdf
ACM_PDF     := $(BUILD_DIR)/mid-term-acm.pdf
ACL_PDF     := $(BUILD_DIR)/mid-term-acl.pdf
REPORT_PDF  := $(BUILD_DIR)/mid-term-report.pdf

# Build tools
PANDOC      := pandoc
PDF_ENGINE  := xelatex
PYTHON      := python3

# Ensure local LaTeX classes (IEEEtran, acmart, acl.sty) are discoverable.
# The trailing colon preserves the default search path.
export TEXINPUTS := .:$(LATEX_CLASSES):

# Common pandoc flags
PANDOC_FLAGS := \
	$(METADATA) $(PAPER) \
	--lua-filter=$(FILTERS_DIR)/include.lua \
	--lua-filter=$(FILTERS_DIR)/table.lua \
	--bibliography=$(BIBLIO) \
	--citeproc \
	--pdf-engine=$(PDF_ENGINE) \
	--pdf-engine-opt=-shell-escape \
	--resource-path=$(ROOT):$(FIG_DIR)/output \
	--extract-media=$(BUILD_DIR)/media \
	-V fontsize=10pt

# Default target
all: figures ieee acm acl report
	@echo "Build complete. Outputs:"
	@ls -lh $(BUILD_DIR)/*.pdf

# Mid-term report (Chinese)
report: figures $(REPORT_PDF)

$(REPORT_PDF): $(REPORT_METADATA) $(REPORT) $(BIBLIO) $(wildcard sections/report_*.md) $(wildcard templates/report/*) $(wildcard filters/*.lua)
	@mkdir -p $(BUILD_DIR)
	$(PANDOC) $(REPORT_METADATA) $(REPORT) \
		--lua-filter=$(FILTERS_DIR)/include.lua \
		--lua-filter=$(FILTERS_DIR)/table-report.lua \
		--bibliography=$(BIBLIO) \
		--citeproc \
		--pdf-engine=$(PDF_ENGINE) \
		--pdf-engine-opt=-shell-escape \
		--resource-path=$(ROOT):$(FIG_DIR)/output \
		--extract-media=$(BUILD_DIR)/media \
		--template=$(TEMPLATES_DIR)/report/template.tex \
		--csl=$(CSL_DIR)/ieee.csl \
		-o $@

# Generate figures
figures:
	@echo "Generating figures..."
	@cd $(ROOT) && $(PYTHON) figures/generate_all.py

# IEEE conference format
ieee: figures $(IEEE_PDF)

$(IEEE_PDF): $(METADATA) $(PAPER) $(BIBLIO) $(wildcard sections/*.md) $(wildcard templates/ieee/*) $(wildcard csl/*.csl) $(wildcard filters/*.lua)
	@mkdir -p $(BUILD_DIR)
	$(PANDOC) $(PANDOC_FLAGS) \
		--template=$(TEMPLATES_DIR)/ieee/template.tex \
		--csl=$(CSL_DIR)/ieee.csl \
		-o $@

# ACM conference format
acm: figures $(ACM_PDF)

$(ACM_PDF): $(METADATA) $(PAPER) $(BIBLIO) $(wildcard sections/*.md) $(wildcard templates/acm/*) $(wildcard csl/*.csl) $(wildcard filters/*.lua)
	@mkdir -p $(BUILD_DIR)
	$(PANDOC) $(PANDOC_FLAGS) \
		--template=$(TEMPLATES_DIR)/acm/template.tex \
		--csl=$(CSL_DIR)/acm.csl \
		-o $@

# ACL conference format
acl: figures $(ACL_PDF)

$(ACL_PDF): $(METADATA) $(PAPER) $(BIBLIO) $(wildcard sections/*.md) $(wildcard templates/acl/*) $(wildcard csl/*.csl) $(wildcard filters/*.lua)
	@mkdir -p $(BUILD_DIR)
	$(PANDOC) $(PANDOC_FLAGS) \
		--template=$(TEMPLATES_DIR)/acl/template.tex \
		--csl=$(CSL_DIR)/acl.csl \
		-o $@

# Watch mode: rebuild all PDFs when markdown/yaml/bib/template files change
watch:
	@command -v entr >/dev/null 2>&1 || { echo "entr is required for watch mode. Install it first."; exit 1; }
	@echo "Watching for changes..."
	@find $(ROOT) -type f \( -name '*.md' -o -name '*.yaml' -o -name '*.bib' -o -name '*.tex' -o -name '*.csl' -o -name '*.py' \) | entr -c $(MAKE) -C $(ROOT) all

# Clean build artifacts

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)/*
	@rm -f $(FIG_DIR)/output/*.pdf $(FIG_DIR)/output/*.pgf $(FIG_DIR)/output/*.png $(FIG_DIR)/output/*.tikz
	@touch $(BUILD_DIR)/.gitkeep $(FIG_DIR)/output/.gitkeep

# Help
help:
	@echo "MACR Mid-term Paper Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make all        Build figures and all PDF variants"
	@echo "  make figures    Generate figures from Python scripts"
	@echo "  make ieee       Build IEEE conference format PDF"
	@echo "  make acm        Build ACM conference format PDF"
	@echo "  make acl        Build ACL conference format PDF"
	@echo "  make report     Build Chinese mid-term report PDF"
	@echo "  make clean      Remove build artifacts and generated figures"
	@echo "  make watch      Auto-rebuild on file changes (requires entr)"
	@echo "  make help       Show this help message"
