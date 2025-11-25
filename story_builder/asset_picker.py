from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


ASSET_DESCRIPTIONS_PATH = Path("assets/asset_descriptions.json")


def load_asset_descriptions(path: Path = ASSET_DESCRIPTIONS_PATH) -> List[Dict[str, Any]]:
    """
    Load the asset_descriptions.json file.

    Expected structure: a list of objects with:
        - filename: str
        - description: str
    """
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    # Normalise structure in case the file is wrapped in a top level key later
    if isinstance(data, dict) and "assets" in data:
        assets = data["assets"]
    else:
        assets = data

    normalised: List[Dict[str, Any]] = []
    for item in assets:
        filename = str(item.get("filename", "")).strip()
        desc = str(item.get("description", "")).strip()
        if not filename or not desc:
            continue
        normalised.append(
            {
                "filename": filename,
                "description": desc,
                "description_lower": desc.lower(),
            }
        )
    return normalised


def _score_asset_for_event(
    asset: Dict[str, Any],
    event_type: str,
    candidate_player_names: Sequence[str],
) -> int:
    """
    Compute a relevance score of a single asset for a given event.

    Heuristics:
    - Strong bonus if any player name appears in the description.
    - Extra bonuses based on event type keywords in the description.
    """
    desc = asset["description_lower"]
    score = 0

    # 1) Direct player name matches
    for name in candidate_player_names:
        n = name.strip()
        if not n:
            continue
        if n.lower() in desc:
            # Strong signal, this image clearly shows this player
            score += 100

    # 2) Event type specific keywords
    if event_type in ("goal", "penalty goal"):
        if "scores" in desc or "goal" in desc:
            score += 25
        if "celebrates" in desc or "celebration" in desc:
            score += 15

    if event_type == "penalty goal":
        if "penalty" in desc:
            score += 25

    if event_type in ("yellow card",):
        if "card" in desc:
            score += 10

    # More types could be added here if needed

    return score


def pick_asset_for_event(
    event: Dict[str, Any],
    player_names: Sequence[str],
    assets: Sequence[Dict[str, Any]],
    default_asset: str = "../assets/placeholder.png",
) -> str:
    """
    Choose the best image asset for a given event.

    - event: the match event dict
    - player_names: list of resolved player names involved in the event
    - assets: list returned by load_asset_descriptions
    - default_asset: used when nothing matches

    Returns a path relative to preview/index.html, for example:
        "../assets/21522436.jpg"
    """
    if not assets:
        return default_asset

    event_type = str(event.get("type", "")).lower().strip()

    best_score = 0
    best_filename: str | None = None

    for asset in assets:
        score = _score_asset_for_event(asset, event_type, player_names)
        if score > best_score:
            best_score = score
            best_filename = asset["filename"]

    if best_filename is None:
        return default_asset

    # preview/index.html is in preview/ and assets/ is a sibling of it
    return f"../assets/{best_filename}"
