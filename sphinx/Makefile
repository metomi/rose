# Minimal makefile for Sphinx documentation

# You can set these variables from the command line:
ROSE_VERSION = $(shell rose version)
SPHINXOPTS    = -n
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = ../doc/$(ROSE_VERSION)
SOURCEDIR     = .

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help clean Makefile .EXPORT_ALL_VARIABLES M

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
# NOTE: EXPORT_ALL_VARIABLES exports make vars as env vars
%: Makefile .EXPORT_ALL_VARIABLES
	# build documentation
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
