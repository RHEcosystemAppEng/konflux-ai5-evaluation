#!/bin/bash
# Grants the appstudio-pipeline SA cluster-level permissions needed by
# the deploy-mcp test pipeline: creating namespaces and managing
# resources inside them. Also grants secret read access in the test namespace.
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
  - apiGroups: ["rbac.authorization.k8s.io"]
    resourceNames: ["mcp-eval-ephemeral-access"]
    resources: ["clusterroles"]
    verbs: ["bind"]
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

# Create dummy pull secret for the test
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: nonexistent-pull-secret
  namespace: ${TEST_NS}
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: e30=
EOF

# Grant secret read access to specific secrets (matches production mcp-eval-llm-reader pattern)
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
  namespace: ${TEST_NS}
rules:
  - apiGroups: [""]
    resourceNames:
      - nonexistent-pull-secret
    resources: ["secrets"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: appstudio-pipeline-secrets-reader
  namespace: ${TEST_NS}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: secret-reader
subjects:
  - kind: ServiceAccount
    name: appstudio-pipeline
    namespace: ${TEST_NS}
EOF

# The task creates a RoleBinding referencing this ClusterRole inside the
# ephemeral namespace. It must exist or the RoleBinding is invalid.
kubectl apply -f - <<'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mcp-eval-ephemeral-access
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "serviceaccounts", "persistentvolumeclaims"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "replicasets"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "create", "delete"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["networkpolicies"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["resourcequotas", "limitranges"]
    verbs: ["get", "list", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods/log", "events"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]
EOF

echo "Pre-requirements setup complete for namespace: $TEST_NS"
