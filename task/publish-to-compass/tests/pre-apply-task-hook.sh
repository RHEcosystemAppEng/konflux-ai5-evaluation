#!/bin/bash
# Grants the appstudio-pipeline SA cluster-level permissions needed by
# the publish-to-compass test pipeline: creating namespaces, managing
# secrets, configmaps, and jobs for the publish workflow.
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
  - apiGroups: [""]
    resources: ["secrets", "configmaps"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "create", "delete", "watch"]
  - apiGroups: ["batch"]
    resources: ["jobs/status"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
EOF

# Grant access to read/write secrets in default namespace
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: default-namespace-secrets
  namespace: default
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: test-default-secrets
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: default-namespace-secrets
subjects:
  - kind: ServiceAccount
    name: appstudio-pipeline
    namespace: ${TEST_NS}
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

# Create dummy Compass secret in default namespace for the test
# (The task will copy it to the ephemeral namespace)
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: mcp-eval-compass
  namespace: default
type: Opaque
stringData:
  api-key: dummy-api-key
  compass-url: https://compass.example.com
EOF

echo "Pre-requirements setup complete for namespace: $TEST_NS"
