from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .core import compute_final_score
from .asset_picker import load_asset_descriptions, pick_asset_for_event
from .squad_utils import load_squad_players, resolve_player_name

OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _flatten_events(match_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Take the match_events.json structure and return a flat, time-sorted list of events.
    """
    messages = match_data["messages"][0]["message"]

    def key(ev: Dict[str, Any]) -> Tuple[int, int]:
        # minute and second come as strings in the JSON
        try:
            minute = int(ev.get("minute", 0))
        except (TypeError, ValueError):
            minute = 0
        try:
            second = int(ev.get("second", 0))
        except (TypeError, ValueError):
            second = 0
        return minute, second

    return sorted(messages, key=key)


def _get_home_away_ids(match_info: Dict[str, Any]) -> Tuple[str, str]:
    """
    Determine home and away team IDs from matchInfo.contestant.
    """
    home_id = None
    away_id = None
    for c in match_info.get("contestant", []):
        if c.get("position") == "home":
            home_id = c["id"]
        elif c.get("position") == "away":
            away_id = c["id"]

    # Fallback to first/second if position is missing for some reason
    if home_id is None or away_id is None:
        contestants = match_info["contestant"]
        home_id = home_id or contestants[0]["id"]
        away_id = away_id or contestants[1]["id"]

    return home_id, away_id


def _make_cover_page(match_info: Dict[str, Any],
                     final_home: int,
                     final_away: int) -> Dict[str, Any]:
    home = match_info["contestant"][0]["name"]
    away = match_info["contestant"][1]["name"]
    title = f"{home} vs {away}"
    date = match_info.get("localDate", "Unknown Date")
    final_score_str = f"{final_home}-{final_away}"

    return {
        "id": str(uuid.uuid4()),
        "type": "cover",
        # keys the viewer actually uses:
        "headline": title + " - " + date,
        "image": "../assets/cover.jpg",
        # extra metadata is fine, schema allows extra fields:
        "caption": f"Final score {final_score_str}",
        "created_at": _utc_now_iso(),
    }

def _make_highlight_page(event: Dict[str, Any],
                         score: int,
                         asset: str,
                         players: List[str]) -> Dict[str, Any]:
    # minute should be an integer
    try:
        minute_val = int(event.get("minute", 0))
    except (TypeError, ValueError):
        minute_val = 0

    headline_parts = []

    etype = str(event.get("type", "")).lower()
    if etype in ("goal", "penalty goal"):
        headline_parts.append("GOAL")
    elif etype == "yellow card":
        headline_parts.append("YELLOW CARD")
    else:
        headline_parts.append(event.get("type", "").title() or "Highlight")

    if players:
        headline_parts.append("— " + ", ".join(players))

    headline = " ".join(headline_parts)

    caption = event.get("comment", "").strip()

    return {
        "id": str(uuid.uuid4()),
        "type": "highlight",
        # what the viewer reads:
        "minute": minute_val,
        "headline": headline,
        "caption": caption,
        "image": asset,
        # extra fields for debugging / explanation:
        "explanation": f"heuristic_score={score}",
        "players": players,
        "event_type": event.get("type"),
        "created_at": _utc_now_iso(),
    }



def _make_no_highlights_page() -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": "info",
        "headline": "No highlights available",
        "body": "No events reached the highlight threshold for this match.",
        "created_at": _utc_now_iso(),
    }



def build_story_from_files(
    match_events_path: Path,
    celtic_squad_path: Path,
    kilmarnock_squad_path: Path,
    top_n: int = 7,
) -> Dict[str, Any]:
    """
    High level entry:
    - load match events
    - load squads
    - compute highlight scores
    - pick top N
    - build story dict
    """

    # Load match data
    match_data = json.loads(match_events_path.read_text(encoding="utf-8"))
    match_info = match_data["matchInfo"]
    events = _flatten_events(match_data)

    # Team IDs for scoring context
    home_team_id, away_team_id = _get_home_away_ids(match_info)

    # Load squads: player_id -> "First Last"
    home_players = load_squad_players(celtic_squad_path)
    away_players = load_squad_players(kilmarnock_squad_path)
    players_by_id = {**home_players, **away_players}

    # Load asset descriptions
    asset_db = load_asset_descriptions()

    # 1. Compute scores and track running scoreline
    scored_events: List[Tuple[int, int, Dict[str, Any]]] = []
    score_home = 0
    score_away = 0

    for idx, ev in enumerate(events):
        final_score = compute_final_score(ev, score_home, score_away, home_team_id, away_team_id)
        if final_score > 0:
            scored_events.append((idx, final_score, ev))

        # Update internal score state for future context
        ev_type = str(ev.get("type", "")).lower().strip()
        if ev_type in ("goal", "penalty goal"):
            team = ev.get("teamRef1")
            if team == home_team_id:
                score_home += 1
            elif team == away_team_id:
                score_away += 1

    final_home, final_away = score_home, score_away

    # 2. Choose top N by score, tie breaking by original index for stability
    scored_events.sort(key=lambda t: (-t[1], t[0]))
    selected = scored_events[:top_n]

    # Reorder selected by original index to keep story chronological
    selected.sort(key=lambda t: t[0])

    pages: List[Dict[str, Any]] = []

    # Always add cover page
    pages.append(_make_cover_page(match_info, final_home, final_away))

    # If we have no selected events, add "no highlights"
    if not selected:
        pages.append(_make_no_highlights_page())
    else:
        for idx, event_score, ev in selected:
            # Resolve involved players
            players: List[str] = []
            p1_id = ev.get("playerRef1")
            p2_id = ev.get("playerRef2")

            if p1_id:
                p1_name = resolve_player_name(p1_id, players_by_id)
                if p1_name:
                    players.append(p1_name)

            if p2_id:
                p2_name = resolve_player_name(p2_id, players_by_id)
                if p2_name and p2_name not in players:
                    players.append(p2_name)

            # Pick best visual asset
            asset_path = pick_asset_for_event(ev, players, asset_db)

            page = _make_highlight_page(ev, event_score, asset_path, players)
            pages.append(page)

    # 3. Build story object
    home_name = match_info["contestant"][0]["name"]
    away_name = match_info["contestant"][1]["name"]
    title = f"{home_name} vs {away_name}"

    # metrics for debugging
    highlight_pages = [p for p in pages if p["type"] == "highlight"]
    goal_like = [p for p in highlight_pages
                 if p.get("event_type") in ("goal", "penalty goal")]

    story = {
        "story_id": str(uuid.uuid4()),
        "title": title,
        "pages": pages,
        "metrics": {
            "goals": len(goal_like),
            "highlights": len(highlight_pages),
        },
        # source should be the path to the events file, not a label
        "source": "../data/match_events.json",
        "created_at": _utc_now_iso(),
    }

  

    return story


def save_story(story: Dict[str, Any], filename: str = "story.json") -> str:
    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / filename
    out_path.write_text(json.dumps(story, indent=2), encoding="utf-8")
    return str(out_path)


def main():
    match_events_path = Path("data/match_events.json")
    celtic_path = Path("data/celtic-squad.json")
    kilmarnock_path = Path("data/kilmarnock-squad.json")

    story = build_story_from_files(
        match_events_path=match_events_path,
        celtic_squad_path=celtic_path,
        kilmarnock_squad_path=kilmarnock_path,
        top_n=7,
    )
    out = save_story(story)
    print(f"Story written to {out}")


if __name__ == "__main__":
    main()
