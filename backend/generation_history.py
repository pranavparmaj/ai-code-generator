import json
import os
from datetime import datetime


HISTORY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "generation_history.json"))


def ensure_history_store():
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    if not os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "w", encoding="utf-8") as handle:
            json.dump([], handle)


def load_history():
    ensure_history_store()
    with open(HISTORY_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_history(entries):
    ensure_history_store()
    with open(HISTORY_PATH, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)


def append_history(entry):
    entries = load_history()
    entry["created_at"] = datetime.utcnow().isoformat()
    entries.insert(0, entry)
    save_history(entries[:30])
    return entry


def build_analytics():
    entries = load_history()
    success_count = len([entry for entry in entries if entry.get("status") == "success"])
    return {
        "total_generations": len(entries),
        "successful_generations": success_count,
        "failed_generations": len(entries) - success_count,
        "last_project": entries[0]["project_name"] if entries else "None yet",
    }
