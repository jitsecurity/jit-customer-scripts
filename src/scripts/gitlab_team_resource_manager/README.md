# GitLab Team Resource Manager

This tool manages team resources in GitLab by automatically updating asset coverage based on team metadata configuration.

## Overview

## Configuration
1. Run git clone https://github.com/jitsecurity/jit-customer-scripts.git
2. Navigate to [Jit platform](https://platform.jit.io/) => Settings => User and Permissions => API Tokens => Generate Token
3. Copy the `JIT_CLIENT_ID` and `JIT_CLIENT_SECRET`
4. Add the environment variables in GitLab:
    - Go to Project > Build > Pipeline Schedules > New schedule
    - Select Description, Timezone, Interval Pattern: everyday, branch: main, Variables: JIT_CLIENT_ID and JIT_CLIENT_SECRET
    - Click on Create pipeline schedule

5. Update `team_metadata.json` file in the repository with the following structure:

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

### Monitor execution:
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


The GitLab Team Resource Manager script:
1. Fetches uncovered assets from JIT API
2. Matches assets with team resources defined in metadata
3. Updates coverage status for matching assets
