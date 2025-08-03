# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Detect if we're in the right environment
CONDA_ENV := $(CONDA_DEFAULT_ENV)
CORRECT_ENV := pantheon-test

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Custom targets
.PHONY: clean
clean:
	rm -rf $(BUILDDIR)

.PHONY: livehtml
livehtml:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: linkcheck
linkcheck:
	$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

.PHONY: dev
dev:
	@echo "Starting development server with auto-reload..."
	@echo "Python: $$(which python)"
	@echo "sphinx-autobuild: $$(which sphinx-autobuild)"
	sphinx-autobuild \
		--host 127.0.0.1 \
		--port 8080 \
		--delay 1 \
		--watch "$(SOURCEDIR)" \
		--ignore "*.pyc" \
		--ignore "*.swp" \
		--ignore "*~" \
		--ignore "*.git" \
		--ignore "$(BUILDDIR)/*" \
		--re-ignore "__pycache__/" \
		--re-ignore "\.#.*" \
		"$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

.PHONY: install
install:
	@echo "Installing documentation dependencies..."
	pip install -r requirements.txt

.PHONY: dev-install
dev-install: install dev
	@echo "Dependencies installed and development server started"

.PHONY: watch
watch:
	@echo "Starting documentation server with file watching..."
	@echo "Watching directory: $(SOURCEDIR)"
	@echo "Output directory: $(BUILDDIR)/html"
	@echo "URL: http://127.0.0.1:8080"
	@echo ""
	micromamba run -n pantheon-test sphinx-autobuild \
		--host 127.0.0.1 \
		--port 8080 \
		--delay 1 \
		--watch source \
		--open-browser \
		source build/html

.PHONY: dev-env
dev-env:
	@echo "Starting development server in pantheon-test environment..."
	@./dev_with_env.sh