import json

from src.shared.clients.github import get_repos_from_github

if __name__ == '__main__':
    repos = get_repos_from_github()
    with open("repos.json", "w") as file:
        file.write(json.dumps([repo.model_dump() for repo in repos], indent=2))
