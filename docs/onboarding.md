# Onboard a native plugin Component

One plugin maps to one Konflux Component, with scoped PR/push invocations.
Use the native
[reference build pipeline](https://gitlab.cee.redhat.com/ai5-marketplace/agentic-plugins/-/blob/per-plugin-componnent/konflux/pipelines/plugin-component-build.yaml).
Do not add a catalog-wide fanout, registered-SHA bot or a second market evaluator.

## Developer team

1. Provide the plugin manifest, ownership/lifecycle metadata, skill manifests and
   authoring content. Select the plugin ID explicitly.
2. Create the native Component/ImageRepository and normal PaC PR/push invocations.
   Scope triggers to that plugin and relevant shared build inputs.
3. Pin preparation, evaluation, evidence-verification and context-collection
   bundles. Feed every packaged skill into evaluation. Standard Konflux image
   build and scanning Tasks remain in place.
4. Provision existing approved evaluation, registry, PostgreSQL and Compass
   credentials through Secrets. Configure the actual Compass Secret key and
   trusted CA. Never put credentials in source or Task parameters.
5. Run Tier 1 by default. `evaluate` requests optional Tier 2; PRs disable
   persistence and pushes require PostgreSQL/Compass persistence.
6. Verify Chains records `PLUGIN_PACKAGE`, `PLUGIN_EVALUATION`,
   `PLUGIN_VERIFICATION` and `COMPASS_CONTEXT` in signed image provenance.
7. Configure official EC feedback scenarios using the managed team's policy.
   Review per-skill scores, producer trust, coverage and market results.

## Managed release team

Own the authoritative ECP and matching RPA in a managed namespace. Include the
upstream EC rules plus reusable plugin Rego, approved producer/runtime digests,
admitted source/image identities and reviewed market requirements. Build Tasks
supply facts; they do not compare market thresholds.

Use a matching developer ReleasePlan with auto-release disabled during onboarding.
Release a successful **push Snapshot** manually. The managed pipeline repeats
strict verification with the official `verify-enterprise-contract` Task before
accessing publication credentials. Git delivery opens a destination MR for review;
it does not push to the target branch or merge the MR.

The release pipeline's optional per-skill report explains the official EC result.
It does not replace EC or make eligibility decisions. Policy and release resource
installation are maintained in the `plugin-pipeline` repository, not this Task catalog.

## Validation

```sh
make test
hack/checkton-local.sh
hack/missing-ta-tasks.sh
```

Set `ABEVAL_TEST_CLI` to the installed CLI to run executable smoke tests.
For live onboarding, verify signed evidence, required persistence acknowledgements,
official EC rejection cases and managed delivery in the owning deployment.
Do not infer publication readiness from an evaluator's Task status alone.
