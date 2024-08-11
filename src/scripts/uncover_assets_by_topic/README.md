## Script to uncover assets by github topic

This script allows automatically uncovering Jit Github repo assets that have a specified Github topic on them.

### Prerequisites

To run the script, you'll need to prepare:

- A Jit client & secret
- The name of your Github organization
- The name of the Github topic
- A valid Github token with read permissions to your organization

### Quickstart

- Copy the `uncover_assets_by_topic.py` and `requirements.txt` files locally.
- Run `pip install -r requirements.txt`
- Set the following environment variables locally:
  ```
  GITHUB_TOKEN=<your github token>
  GITHUB_ORGANIZATION=<your github org name>
  JIT_CLIENT_ID=<jit client>
  JIT_SECRET=<jit secret>
  TOPIC_TO_UNCOVER=<topic name to uncover by>
  ```
- Run `python uncover_asets_by_topic.py`

You should now see that the script runs successfully, and the relevat repos get uncovered from Jit. Note that organizations with a large number of repos can take a few minutes to complete.

### Running in Github actions

If you want to run the script from a Github action, choose a repository in the same organization and use the following YAML:

```
name: Deactivate Repos by Topic

on:
  workflow_dispatch:

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.x" # Specify your Python version here

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install requests
          python -m pip install PyGithub
          python -m pip install urllib3

      - name: Run Python script
        env:
          JIT_CLIENT_ID: ${{ secrets.JIT_CLIENT_ID }}
          JIT_SECRET: ${{ secrets.JIT_SECRET }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # GITHUB_TOKEN provided by GitHub Actions by default
          GITHUB_ORGANIZATION: ${{ github.repository_owner }}
          TOPIC_TO_UNCOVER: <your topic name>
        run: python uncover_assets_by_topic.py
```
