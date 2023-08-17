# jit-create-teams-from-github-topics

This project is a Python script that interacts with the GitHub API and the JIT Teams API.\
It lists the repository names and topics for a given GitHub organization and generates teams according to the topics from Github.

## Prerequisites

- Python 3.x
- Git

## Installation

1. Clone the repository:

   ```shell
   git clone git@github.com:jitsecurity/jit-create-teams-from-github-topics.git
   ```

2. Change into the project directory:

   ```shell
   cd jit-create-teams-from-github-topics
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

## Development

To override the default Frontegg authentication endpoint, you can set the `FRONTEGG_AUTH_ENDPOINT` environment variable. If the variable is not set, the default value will be used.

To override Jit's API end point, you can set the `JIT_API_ENDPOINT` environment variable. If the variable is not set, the default value will be used.