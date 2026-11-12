#!/bin/bash
# Grants the appstudio-pipeline SA cluster-level permissions needed by
# the mcp-conformance-eval test pipeline: creating namespaces and
# managing resources inside them.
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
    resourceNames: ["mcp-eval-ephemeral-access-cr"]
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
---
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

# Create dummy Compass secret in default namespace for the test
# (The task will copy it to the ephemeral namespace)
kubectl apply -f - <<'EOF'
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

# In Kind (unlike OpenShift) there is no SCC to assign a consistent UID
# across steps.  ose-cli runs as root while mcp-eval-image runs as non-root,
# causing PermissionError on shared workspace files.  Add a stepTemplate so
# every step runs as root, matching the OpenShift restricted-SCC behaviour.
TASK_COPY="$1"
yq -i '.spec.stepTemplate.securityContext.runAsUser = 0' "$TASK_COPY"

echo "Pre-requirements setup complete for namespace: $TEST_NS"
