# diff.py
import difflib
from typing import List, Dict, Any

def compute_diff(a: List[str], b: List[str]) -> List[str]:
    """Compute a unified diff between two lists of strings."""
    return list(difflib.unified_diff(a, b, lineterm=""))


def diff_text(a: str, b: str) -> str:
    """Return a unified diff as a string between two text blocks."""
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    diff = compute_diff(a_lines, b_lines)
    return "\n".join(diff)


def diff_dicts(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a dict describing the differences between two dicts.
    """
    diff = {}
    for key in set(old) | set(new):
        if old.get(key) != new.get(key):
            diff[key] = {'old': old.get(key), 'new': new.get(key)}
    return diff


def diff_lists(old_list: List[Dict[str, Any]], new_list: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """
    Returns a list of diffs for items in old_list and new_list matched by key.
    """
    old_map = {item[key]: item for item in old_list}
    new_map = {item[key]: item for item in new_list}
    all_keys = set(old_map) | set(new_map)
    diffs = []
    for k in all_keys:
        old_item = old_map.get(k)
        new_item = new_map.get(k)
        if old_item and new_item:
            d = diff_dicts(old_item, new_item)
            if d:
                diffs.append({'key': k, 'diff': d})
        elif old_item:
            diffs.append({'key': k, 'diff': 'removed'})
        else:
            diffs.append({'key': k, 'diff': 'added'})
    return diffs
