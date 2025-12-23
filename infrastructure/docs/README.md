# Docs

[tailscale-operator-values.yaml](./tailscale-operator-values.yaml) shows the values available to be set for the `tailscale-operator` helm chart.

To generate it:

```bash
helm show values tailscale-operator \
  --repo https://pkgs.tailscale.com/helmcharts > tailscale-operator-values.yaml
```
