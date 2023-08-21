from typing import List


def get_different_items_in_lists(list1: List[str], list2: List[str]) -> List[str]:
    return list(set(list1) - set(list2))


def get_teams_to_create(topic_names: List[str], existing_team_names: List[str]) -> List[str]:
    return get_different_items_in_lists(topic_names, existing_team_names)


def get_teams_to_delete(topic_names: List[str], existing_team_names: List[str]) -> List[str]:
    return get_different_items_in_lists(existing_team_names, topic_names)
