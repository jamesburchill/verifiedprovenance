# Makefile for Human Authorship Provenance
# Requires: opentimestamps-client (`pip install opentimestamps-client`)

PROOFDIR := proofs
OTS := ots
COMMITS := $(shell git rev-list --max-count=20 HEAD)

.PHONY: anchor verify manifest sign clean

anchor:
	@mkdir -p $(PROOFDIR)
	@echo ">> Building commit batch list..."
	@printf "" > $(PROOFDIR)/commits.txt
	@for c in $(COMMITS); do echo $$c >> $(PROOFDIR)/commits.txt; done
	@echo ">> Deriving merkle root (simple hash of list for MVP)..."
	@sha256sum $(PROOFDIR)/commits.txt | awk '{print $$1}' > $(PROOFDIR)/merkle_root.hex
	@xxd -r -p $(PROOFDIR)/merkle_root.hex > $(PROOFDIR)/merkle_root.bin
	@echo ">> Anchoring with OpenTimestamps..."
	$(OTS) stamp $(PROOFDIR)/merkle_root.bin
	@echo ">> Attempting OTS upgrade (may take time until confirmed on Bitcoin)..."
	-$(OTS) upgrade $(PROOFDIR)/merkle_root.bin
	@echo ">> Done. Proof at $(PROOFDIR)/merkle_root.bin.ots"

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
