# collect-plugin-context

Collects Compass facts for official EC policy evaluation. It makes no market
eligibility decisions and has no score or lifecycle thresholds.

The task consumes prepared source as a trusted artifact, verifies its package
inventory and fetches each plugin/skill/MCP entity over verified TLS. It emits
`COMPASS_CONTEXT` containing actual owners, lifecycles, requested SoundCheck
observations and collection time, bound to the image, revision and manifest.
`TEST_OUTPUT` reports collection execution. Checker errors remain errors.

Inputs include `compass-url`, a `soundcheck-checks` JSON object with plugin/skill/
mcp ID lists, the existing Compass Secret and native trusted CA ConfigMap.
Do not pass a verification bypass. The runtime leaves Tekton's `SSL_CERT_DIR`
untouched and sets `SSL_CERT_FILE` to the mounted CA file.

Run this task last to maximize freshness. EC checks the producer/runtime pins,
approved Compass endpoint, coverage, source/image binding and the market's
observation-age limit. A successful collection does not itself qualify a plugin.

Results have a 3,500-byte combined budget and fail explicitly on overflow.
Build the bundle with `hack/build-and-push-bundles.sh collect-plugin-context`.
The runtime is the sibling `plugin-pipeline` component tools image; see its
policy/architecture documentation for enforcement and the versioned format.
