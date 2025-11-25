from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def load_squad_players(path: Path) -> Dict[str, str]:
    """
    Load a squad JSON file and return a mapping:
        player_id -> 'FirstName LastName'

    Expected structure:
    {
      "squad": [
        {
          "person": [ {...}, {...}, ... ]
        }
      ]
    }
    """
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    players_by_id: Dict[str, str] = {}

    squad_list = data.get("squad", [])
    if not squad_list:
        return players_by_id

    # In the sample, there is one entry in "squad"
    entry = squad_list[0]
    persons = entry.get("person", [])

    for person in persons:
        if person.get("type") != "player":
            continue

        player_id = person.get("id")
        first = str(person.get("firstName", "")).strip()
        last = str(person.get("lastName", "")).strip()

        if not player_id or not (first or last):
            continue

        full_name = f"{first} {last}".strip()
        players_by_id[player_id] = full_name

    return players_by_id


def resolve_player_name(player_id: str,
                        players_by_id: Dict[str, str]) -> Optional[str]:
    """
    Given a playerRef (id) and a mapping produced by load_squad_players,
    return the player's full name, or None if unknown.
    """
    return players_by_id.get(player_id)
