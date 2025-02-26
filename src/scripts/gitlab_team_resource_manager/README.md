# GitLab Team Resource Manager

This tool manages team resources in GitLab by automatically updating asset coverage based on team metadata configuration.

## Important Notes

- This script is designed to be run on a daily schedule.
- The script will only update assets that are not currently covered by a team resource.
- The script will update the coverage ordered alphabetically by the json file name.

## Configuration
1. Clone the repository:
   ```bash
   git clone https://github.com/jitsecurity/jit-customer-scripts.git
   cd jit-customer-scripts
   ```

2. Push to your own GitLab registry:
   ```bash
   # Remove the original remote
   git remote remove origin

   # Add your GitLab repository as the new remote
   git remote add origin https://gitlab.com/your-organization/jit-customer-scripts.git

   # Push to your GitLab repository
   git push -u origin main
   ```

3. Navigate to [Jit platform](https://platform.jit.io/) => Settings => User and Permissions => API Tokens => Generate Token
   ![image](https://github.com/user-attachments/assets/897cdc35-fb01-48b0-9ffa-6ed65f3b62de)
   ![image](https://github.com/user-attachments/assets/7ba48c2f-01dc-43fa-ad12-0d33bb8789eb)


4. Copy the `JIT_CLIENT_ID` and `JIT_CLIENT_SECRET`
5. Add the environment variables in GitLab:
    - Go to Project > Build > Pipeline Schedules > New schedule
    - Select Description, Timezone, Interval Pattern: everyday, branch: main, Variables: JIT_CLIENT_ID and JIT_CLIENT_SECRET
    - Click on Create pipeline schedule
  ![image](https://github.com/user-attachments/assets/c5b25d63-d2be-44fc-a0bf-1f7089df4794)


1. Copy you teams json files to the `src/scripts/gitlab_team_resource_manager` folder.

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
   - ![image](https://github.com/user-attachments/assets/ab502aee-116c-49f7-a906-e37b754a5b98)



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
