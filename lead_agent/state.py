import json
import os


def load_seen_ids(state_file: str) -> set:
    if not os.path.exists(state_file):
        return set()
    with open(state_file, "r") as f:
        return set(json.load(f))


def save_seen_ids(state_file: str, seen_ids: set) -> None:
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)
