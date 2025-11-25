from story_builder.asset_picker import load_asset_descriptions, pick_asset_for_event

HOME_TEAM_ID = "dvnjvad3p09dugr79gktlrtll"   # Celtic
AWAY_TEAM_ID = "enzoyc121va61wtmjf4cm7p3d"   # Kilmarnock

assets = load_asset_descriptions()

# Fake event for Engels penalty
event = {
    "type": "penalty goal",
    "minute": "92",
}

player_names = ["Arne Engels"]

chosen = pick_asset_for_event(event, player_names, assets)
print("Chosen asset:", chosen)
