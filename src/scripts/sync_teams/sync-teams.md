# Sync Teams

This target has three sub-targets:

- `install`: Ensures Python 3 is installed, sets up a virtual environment, and installs the required dependencies.
- `configure`: Prompts the user to input configuration details like GitHub organization name, API client ID, client
  secret, and GitHub token. The responses are written to a `.env` file.
- `run`: Activates the virtual environment and runs two Python scripts in succession to generate teams.

## Creating Teams from Github Topics

To run the script and create teams and update assets, use the following command:

```shell
make create-teams
```

This command is a convenience utility that extracts the teams to generate from Github topics. \
It runs these commands:

```bash
python src/utils/github_topics_to_json_file.py
python src/scripts/create_teams.py teams.json
```

This command will fetch the repository names and topics from the GitHub API and generate the JSON file. And then it will
create the teams and update the assets.

> We recommend using something like Github Actions and Github secrets to run this script on a schedule to make sure you
> are always synced.

### Using External JSON File

You can also provide a JSON file containing team details using a command line argument directly. The JSON file should
have the following structure:

```json
{
  "teams": [
    {
      "name": "Team 1",
      "members": [
        "user1",
        "user2"
      ],
      "resources": [
        {
          "type": "{resource_type}",
          "name": "Resource 1"
        },
        {
          "type": "{resource_type}",
          "name": "Resource 2"
        }
      ]
    },
    {
      "name": "Team 2",
      "members": [
        "user3",
        "user4"
      ],
      "resources": [
        {
          "type": "{resource_type}",
          "name": "Resource 3"
        }
      ]
    }
  ]
}
```

You can run the command like this:

```shell
python scripts/create_teams.py path/to/teams.json
```

Replace `path/to/teams.json` with the actual path to your JSON file.

### Excluding Topics

You can exclude certain topics from being considered when creating teams. \
To exclude topics, you could add them in the `make configure` command or update this env var in
the `.env` file: `TEAM_WILDCARD_TO_EXCLUDE`.

For example, to exclude topics that contain the word "test", you can set the variable as follows:

    TEAM_WILDCARD_TO_EXCLUDE=*test*

This will exclude topics with names like "test", "test123", and "abc-testing".
