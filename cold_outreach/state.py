import json
import os
from datetime import datetime, timezone


def load_state(state_file: str) -> dict:
    if not os.path.exists(state_file):
        return {}
    with open(state_file, "r") as f:
        return json.load(f)


def save_state(state_file: str, state: dict) -> None:
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def mark_sent(state: dict, email: str, company: str, website: str) -> None:
    state[email] = {
        "company": company,
        "website": website,
        "status": "sent",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "replied_at": None,
    }


def mark_replied(state: dict, email: str) -> None:
    state[email]["status"] = "replied"
    state[email]["replied_at"] = datetime.now(timezone.utc).isoformat()


def count_sent_today(state: dict) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    return sum(1 for v in state.values() if (v.get("sent_at") or "").startswith(today))
