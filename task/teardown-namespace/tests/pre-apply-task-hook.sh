#!/bin/bash
# Grants the appstudio-pipeline SA cluster-level permissions needed by
# the teardown-namespace test pipeline: creating and deleting namespaces.
set -e

TEST_NS="$2"

kubectl apply -f - <<'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: test-namespace-manager
rules:
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["rolebindings"]
    verbs: ["get", "list", "create", "update", "patch"]
EOF

kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: test-namespace-manager-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: test-namespace-manager
subjects:
  - kind: ServiceAccount
    name: appstudio-pipeline
    namespace: ${TEST_NS}
EOF

echo "Pre-requirements setup complete for namespace: $TEST_NS"
