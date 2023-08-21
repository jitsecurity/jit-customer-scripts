# Jit Customer Scripts

This project is a Python script that interacts with the GitHub API and the JIT Teams API.\
It lists the repository names and topics for a given GitHub organization and generates teams\
according to the topics from Github.

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

To run the script and retrieve the repository names and topics, use the following command:

```shell
   make run
   ```

### Using external json file with the --input argument

You can also provide a JSON file containing team details using the `--input` argument. The JSON file should\
have the following structure:

```json
[
  {
    "name": "Repository 1",
    "topics": [
      "topic1",
      "topic2"
    ]
  },
  {
    "name": "Repository 2",
    "topics": [
      "topic3"
    ]
  }
]
```

To use the `--input` argument, run the following command:

```shell
python main.py --input path/to/teams.json
```

Replace `path/to/teams.json` with the actual path to your JSON file.

## Development

To override the default Frontegg authentication endpoint, you can set the `FRONTEGG_AUTH_ENDPOINT` environment variable.\
If the variable is not set, the default value will be used.

To override Jit's API end point, you can set the `JIT_API_ENDPOINT` environment variable. If the variable is not set,
the default value will be used.
