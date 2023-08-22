# Jit Customer Scripts

[![codecov](https://codecov.io/gh/jitsecurity/jit-customer-scripts/graph/badge.svg?token=76IhFwTPjv)](https://codecov.io/gh/jitsecurity/jit-customer-scripts)

This project provides customer scripts to help them with their JIT solution. \
The `create-teams.py` script's goal is to create teams and update assets based on the provided JSON file.

## Project Structure

The project has the following structure:

```
jit-customer-scripts/
├── src/
│   └── scripts/
│       └── create_teams.py
├── src/
│   └── utils/
│       └── github_topic_to_json_file.py
├── src/
│   └── shared/
│       └── models.py
│       └── ...
├── Makefile
└── README.md
```

- `scripts/`: Contains the customer scripts.
- `src/shared/models.py`: Contains the data models used by the scripts.
- `.env`: Configuration file generated by the Makefile.
- `Makefile`: Provides commands to help with project setup and execution.
- `README.md`: This file.

## Prerequisites

- Python 3.x
- Git

## Installation

1. Clone the repository:

   ```shell
   git clone git@github.com:jitsecurity/jit-customer-scripts.git
   ```

2. Change into the project directory:

   ```shell
   cd jit-customer-scripts
   ```

3. Create a virtual environment and install the required dependencies:

   ```shell
   make install
   ```

## Configuration

Before running the script, you need to configure the necessary environment variables. Follow these steps:

1. Run the configuration command:

   ```shell
   make configure
   ```

2. Enter the required information when prompted:
    - GitHub organization name
    - API client ID
    - API client secret
    - GitHub token

3. The command will generate a `.env` file with the provided information.

## Usage

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

This command will fetch the repository names and topics from the GitHub API and generate the JSON file. And then it will create the teams and update the assets.

### Using External JSON File

You can also provide a JSON file containing team details using a command line argument directly. The JSON file should have the following structure:

```json
{
  "teams": [
    {
      "name": "Team 1",
      "members": ["user1", "user2"],
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
      "members": ["user3", "user4"],
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

## Development

To override Jit's API endpoint, you can set the `JIT_API_ENDPOINT` environment variable. If the variable is not set, the default value will be used.
