# GitLab Team Resource Manager

This tool manages team resources in GitLab by automatically updating asset coverage based on team metadata configuration.

## Overview

The GitLab Team Resource Manager script:
1. Fetches uncovered assets from JIT API
2. Matches assets with team resources defined in metadata
3. Updates coverage status for matching assets

## Configuration

### 1. Environment Variables

Set the following environment variables in your GitLab CI/CD settings:

```bash
JIT_CLIENT_ID=your_client_id
JIT_CLIENT_SECRET=your_client_secret
```

### 2. Team Metadata File

Create a `team_metadata.json` file in your repository with the following structure:

```json
{
  "teams": [
    {
      "name": "Team Name",
      "members": ["member1", "member2"],
      "resources": [
        {
          "type": "repository",
          "name": "repo-name",
          "vendor": "gitlab"
        }
      ]
    }
  ]
}
```

### 3. GitLab CI/CD Pipeline

1. Copy the `.gitlab-ci.yml` file to your repository root
2. The pipeline is configured to run:
   - On schedule
   - When manually triggered via web interface
3. Copy the `gitlab_team_resource_manager.py` to `src/scripts/gitlab_team_resource_manager gitlab_team_resource_manager.py`
4. Copy the `team_metadata.json` to `src/scripts/gitlab_team_resource_manager/team_metadata.json`


### 4. GitLab CI/CD  `JIT_CLIENT_ID` and `JIT_CLIENT_SECRET`
1. Navigate to Jit platform => Settings => User and Permissions => API Tokens => Generate Token
2. Copy the `JIT_CLIENT_ID` and `JIT_CLIENT_SECRET`


1. Add the environment variables in GitLab:
   - Go to Settings > CI/CD > Variables
   - Add `JIT_CLIENT_ID` and `JIT_CLIENT_SECRET`

2. Configure pipeline schedule:
   - Go to CI/CD > Schedules
   - Create a new schedule
   - Set desired frequency (e.g., daily, weekly)

3. Monitor execution:
   - View pipeline status in CI/CD > Pipelines
   - Check job logs for detailed execution information

## Script Behavior

1. Authentication:
   - Authenticates with JIT API using provided credentials
   - Exits if authentication fails

2. Asset Processing:
   - Fetches uncovered assets from JIT API
   - Matches assets with team resources
   - Updates coverage status for matching assets

3. Team Selection:
   - Processes the first team that has resources matching uncovered assets
   - Logs matching resources and team information

## Troubleshooting

1. Authentication Issues:
   - Verify JIT_CLIENT_ID and JIT_CLIENT_SECRET are correct
   - Check API endpoint accessibility

2. No Assets Found:
   - Verify API endpoint configuration
   - Check if there are uncovered assets

3. No Matching Resources:
   - Verify team_metadata.json structure
   - Ensure resource names match asset names
