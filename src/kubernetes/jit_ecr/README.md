# JIT Container Registry Credentials Manager

## Overview

This Helm chart deploys a system to manage and rotate Jit container registry secrets automatically. It ensures that containers (which are controls) can be pulled from the Jit Container Registry by maintaining up-to-date credentials.

## Purpose

The main purpose of this chart is to:

1. Authenticate with the Jit API to obtain container registry credentials.
2. Create and update a Kubernetes secret containing these credentials.
3. Periodically refresh the credentials to ensure continued access to the Jit Container Registry.

## Components

The chart consists of the following main components:

1. **Initial Login Job**: A one-time job that runs immediately after chart installation to set up the initial container registry credentials.
2. **Refresh CronJob**: A periodically running job that refreshes the container registry credentials to ensure they remain valid.
3. **ConfigMap**: Contains the script used by both the initial job and the CronJob to fetch and update the credentials.
4. **ServiceAccount and RBAC**: Provides necessary permissions for the jobs to create and update secrets in the specified namespace.

## Prerequisites

- Kubernetes 1.16+
- Helm 3.0+
- A valid Jit account with API credentials (Client ID and Secret)
  - These can be obtained from https://docs.jit.io/docs/managing-users#generating-api-tokens
  - The API credentials should be created with the Member role
  - The secret should be kept securely and not shared or exposed publicly

## Installation

To install the chart with the release name `jit-registry`:

```bash
helm install jit-registry . \
  --set client_id=your-client-id \
  --set secret=your-secret \
  --set namespace=your-namespace
```

## Configuration

The following table lists the configurable parameters of the JIT Container Registry Credentials Manager chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `client_id` | Jit API Client ID (Member role) | `"<JIT_API_CLIENT_ID>"` |
| `secret` | Jit API Secret | `"<JIT_API_SECRET>"` |
| `jit_base_url` | Jit API Base URL | `"https://api.jit.io"` |
| `registry_name` | Jit Container Registry Name | `"registry.jit.io"` |
| `keep_job_history_seconds` | Time (in seconds) to keep job history | `86400` |
| `namespace` | Kubernetes namespace to deploy to | `"default"` |
| `jit_ecr_secret_name` | Name of the Kubernetes secret for container registry credentials | `"jit-registry-creds"` |

To modify any of these parameters, you can use the `--set key=value[,key=value]` argument to `helm install` or `helm upgrade`, or modify the `values.yaml` file directly.

Note: The `client_id` and `secret` should be obtained from https://docs.jit.io/docs/managing-users#generating-api-tokens. Make sure to use the "Member" role when generating these credentials. Please store these values in a secure place and never expose them publicly.

The `jit_ecr_secret_name` should match the Kubernetes runner configuration. For example, in GitLab:

```yaml
[runners.kubernetes]
   poll_timeout = 2000
   node_selector_overwrite_allowed = ".*"
   image_pull_secrets=["jit-registry-creds"]
```

## Usage

After installation, the chart will:

1. Create an initial Kubernetes secret with container registry credentials.
2. Set up a CronJob to refresh these credentials periodically.

You can use the created secret (`jit-registry-creds` by default) in your pod specifications to pull images from the Jit Container Registry:

```yaml
spec:
  imagePullSecrets:
    - name: jit-registry-creds
  containers:
    - name: your-container
      image: registry.jit.io/your-image:tag
```

## Monitoring and Troubleshooting

To check the status of the initial login job:

```bash
kubectl get jobs -n your-namespace jit-registry-initial-login
```

To check the status of the refresh CronJob:

```bash
kubectl get cronjobs -n your-namespace jit-registry-refresh
```

To view logs of the most recent job execution:

```bash
kubectl logs -n your-namespace job/jit-registry-refresh-<job-id>
```

For more detailed instructions, please refer to the NOTES.txt file that is displayed after chart installation.

## Uninstalling the Chart

To uninstall/delete the `jit-registry` deployment:

```bash
helm delete jit-registry
```

This command removes all the Kubernetes components associated with the chart and deletes the release.

## Security Considerations

- The Jit API Secret is sensitive information. Always handle it securely and avoid exposing it in logs, command-line arguments, or version control systems.
- Use Kubernetes Secrets or a secure secrets management system to store the `client_id` and `secret`.
- Regularly rotate your Jit API credentials as per your organization's security policies.

## Support

For any issues or questions, please contact Jit support or open an issue in the chart's repository.
