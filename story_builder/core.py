BASE_SCORES = {
    "goal": 100,
    "penalty goal": 95,
    "red card": 90,
    "penalty won": 70,
    "penalty lost": 60,
    "attempt saved": 60,
    "attempt blocked": 55,
    "post": 50,
    "miss": 40,
    "yellow card": 30,
    "corner": 10,
}


def get_base_score(event_type: str) -> int:
    """
    Return base score for event type.
    Unknown event types default to 0.
    """
    return BASE_SCORES.get(event_type.lower().strip(), 0)

def _parse_minute(event) -> int:
    raw = event.get("minute", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def compute_context_bonus(event, score_home, score_away, home_team_id: str, away_team_id: str) -> dict:
    """
    Compute a context bonus based on game state BEFORE this event.
    Returns {"bonus": int, "reasons": [str, ...]}
    home_team_id / away_team_id are the IDs from matchInfo.contestant.
    
    Bonus categories:
    - late_game: +15 at minute 80+, +5 extra at 90+ 
    - penalty_goal_bonus: +10 for penalty goals 
    - first_goal: +25 (opens scoring)
    - equalizer: +30 (ties match)
    - go_ahead: +30 (breaks tie)
    - extend_lead: +15 (1-goal to 2-goal lead)
    - extend_big_lead: +5 (already winning by 2+)
    - tight_game_chance: +20 (crucial saves/blocks in close matches at min 75+)
    """
    minute = _parse_minute(event)
    event_type = str(event.get("type", "")).lower().strip()

    bonus = 0
    reasons = []

    # 1. TIME-BASED BONUS
    if minute >= 80:
        bonus += 15
        reasons.append("late_game=15")
        if minute >= 90:
            bonus += 5
            reasons.append("very_late=5")

    # 2. PENALTY SITUATION BONUS
    if event_type == "penalty goal":
        bonus += 10
        reasons.append("penalty_goal_bonus=10")

    # 3. GOAL / SCORELINE CONTEXT
    if event_type in ("goal", "penalty goal"):
        diff_before = abs(score_home - score_away)

        team = event.get("teamRef1")
        if team == home_team_id:
            new_home = score_home + 1
            new_away = score_away
        elif team == away_team_id:
            new_home = score_home
            new_away = score_away + 1
        else:
            # Unknown team, do not try to reason about score
            return {"bonus": bonus, "reasons": reasons}

        diff_after = abs(new_home - new_away)

        # First goal of match
        if score_home == 0 and score_away == 0:
            bonus += 25
            reasons.append("first_goal=25")

        # Equalizer
        if diff_after == 0:
            bonus += 30
            reasons.append("equalizer=30")

        # Go-ahead goal (breaking a tie)
        if diff_before == 0 and diff_after == 1:
            bonus += 30
            reasons.append("go_ahead=30")

        # Extends one-goal lead to two-goal lead
        if diff_before == 1 and diff_after == 2:
            bonus += 15
            reasons.append("extend_lead=15")

        # Extends bigger lead
        if diff_before >= 2:
            bonus += 5
            reasons.append("extend_big_lead=5")

    # 4. BIG CHANCE IN TIGHT GAME
    if event_type in ("attempt saved", "attempt blocked", "miss", "post"):
        if abs(score_home - score_away) <= 1 and minute >= 75:
            bonus += 20
            reasons.append("tight_game_chance=20")

    return {"bonus": bonus, "reasons": reasons}


def compute_final_score(event, score_home, score_away, home_team_id: str, away_team_id: str) -> dict:
    """
    Compute final score for an event using:
    - base score
    - context bonus
    Returns {"score": int, "base": int, "context_bonus": int, "bonus_reasons": [str, ...]}
    """
    base = get_base_score(event.get("type", ""))
    if base == 0:
        return {"score": 0, "base": 0, "context_bonus": 0, "bonus_reasons": []}
    context_data = compute_context_bonus(event, score_home, score_away, home_team_id, away_team_id)
    context_bonus = context_data["bonus"]
    bonus_reasons = context_data["reasons"]
    return {
        "score": base + context_bonus,
        "base": base,
        "context_bonus": context_bonus,
        "bonus_reasons": bonus_reasons,
    }
