# Makefile for Automated Human Authorship Provenance (No NFTs)
PROOFDIR := proofs
OTS := ots

.PHONY: install-hooks anchor verify manifest sign clean

install-hooks:
	@mkdir -p .git/hooks
	@cp hooks/post-commit .git/hooks/post-commit
	@chmod +x .git/hooks/post-commit
	@echo ">> Installed post-commit hook"

anchor:
	@python3 scripts/anchor_ots.py --force

verify:
	$(OTS) verify $(PROOFDIR)/merkle_root.bin || true

manifest:
	@python3 scripts/gen_provenance.py
	@echo ">> Wrote provenance.json"

sign:
	@gpg --armor --detach-sign --output provenance.json.asc provenance.json
	@echo ">> Wrote provenance.json.asc"

clean:
	rm -f provenance.json provenance.json.asc
