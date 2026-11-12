#!/bin/bash
# Grants the appstudio-pipeline SA cluster-level permissions needed by
# create-namespace: creating namespaces and rolebindings. Also creates
# the mcp-eval-ephemeral-access-cr ClusterRole that the task references
# when granting the pipeline SA access inside the new namespace.
set -e

TEST_NS="$2"

# ClusterRole: namespace management (create, get, apply namespaces + rolebindings)
# plus bind permission for mcp-eval-ephemeral-access-cr to avoid RBAC escalation
kubectl apply -f - <<'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: test-namespace-manager
rules:
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["get", "list", "create", "update", "patch"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["rolebindings"]
    verbs: ["get", "list", "create", "update", "patch"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resourceNames: ["mcp-eval-ephemeral-access-cr"]
    resources: ["clusterroles"]
    verbs: ["bind"]
EOF

# Bind ClusterRole to the appstudio-pipeline SA in the test namespace
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

# The task creates a RoleBinding referencing this ClusterRole inside the
# ephemeral namespace. It must exist or the RoleBinding is invalid.
kubectl apply -f - <<'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mcp-eval-ephemeral-access-cr
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
