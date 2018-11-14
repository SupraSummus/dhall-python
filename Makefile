.PHONY: all abnf_patch

all:

abnf_patch:
	diff -u dhall-lang/standard/dhall.abnf dhall.abnf > dhall.abnf.patch; test $$? -le 1
