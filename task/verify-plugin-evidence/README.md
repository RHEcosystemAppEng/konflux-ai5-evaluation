# verify-plugin-evidence

Produces `PLUGIN_VERIFICATION` for official EC policies. It makes no market
eligibility decisions and contains no thresholds.

The task consumes the approved prepared source trusted artifact, immutable image
identity, evaluation summary and report artifact. It transports the actual image
and reports, verifies payload/inventory/hash identity, and checks every detailed
score against the inline schema-2 score matrix. It emits compact execution and
behavioral-health observations plus manifest/summary/report bindings.

`TEST_OUTPUT=SUCCESS` means evidence verification completed. Low measured scores
remain visible and are accepted/rejected by the selected EC market policy.
Missing, mismatched or malformed evidence fails the task.

Use a digest-pinned Task bundle and approved `evidence-image`. EC must verify both
pins and bind the supplied evaluation/report inputs to the approved evaluation
Task's attested results. The runtime is `plugin-pipeline`'s component tools image.
It does not execute plugin-authored scripts.

The image and report registry credentials use the native build account's linked
credentials. Results have a 3,500-byte combined budget and fail on overflow.

Build the bundle with `hack/build-and-push-bundles.sh verify-plugin-evidence`.
See the sibling `plugin-pipeline/policy/README.md` for policy installation and
`Design/02-Class-and-Relationship-Diagrams.md` for the versioned result format.
