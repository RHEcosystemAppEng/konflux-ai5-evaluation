.PHONY: bundles
bundles:
	hack/build-and-push-bundles.sh $(TASKS)

.PHONY: checkton
checkton:
	hack/checkton-local.sh

.PHONY: versioning-check
versioning-check:
	hack/versioning.py check

.PHONY: ta-check
ta-check:
	hack/missing-ta-tasks.sh

.PHONY: yamllint
yamllint:
	yamllint .

.PHONY: validate
validate: yamllint checkton versioning-check ta-check