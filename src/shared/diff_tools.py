from typing import List


def get_different_items_in_lists(list1: List[str], list2: List[str]) -> List[str]:
    return list(set(list1) - set(list2))

