# Settings Up Self-Hosted Runners

This Command and its sub-targets facilitate setting up a GitHub self-hosted runner on different OS:

- `centos`: Setup self hosted runner on CentOS.
- `ubuntu`: Setup self hosted runner on Ubuntu.

You need to take the self hosted runners token from the Github Actions page of your repository.
`https://github.com/<your-github-org-name>/jit/settings/actions/runners`

## Running on CentOS

```shell
make self-hosted-runner centos runner_token=<runner-token> github_org=<github-organization>
```

You will be prompted to answer some questions about your runner. \
When you complete this step, restart your EC2 machine. \
The runner will be automatically started on boot.

Replace `<runner-token>` and `<github-organization>` with the appropriate values.

## Running on Ubuntu

```shell
make self-hosted-runner ubuntu runner_token=<runner-token> github_org=<github-organization>
```

You will be prompted to answer some questions about your runner. \
When you complete this step, restart your EC2 machine. \
The runner will be automatically started on boot.

Replace `<runner-token>` and `<github-organization>` with the appropriate values.