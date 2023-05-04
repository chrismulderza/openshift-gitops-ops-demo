# openshift-gitops-ops-demo
OpenShift GitOps for Operations Demo


## BGD App

### Introduce change to test configuration drift

```bash
kubectl -n bgd patch deploy/bgd --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/env/0/value", "value":"green"}]'
```

- Patch ArgoCD Application with automated sync

```bash
kubectl patch application/bgd-app -n openshift-gitops --type=merge -p='{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
```
