import json

from src.shared.clients.github import get_teams_from_github_topics

if __name__ == '__main__':
    teams = get_teams_from_github_topics()
    with open("repos.json", "w") as file:
        file.write(json.dumps(teams, indent=2))
