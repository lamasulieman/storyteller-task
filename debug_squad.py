from pathlib import Path
from story_builder.squad_utils import load_squad_players, resolve_player_name

celtic_players = load_squad_players(Path("data/celtic-squad.json"))

print("Total Celtic players loaded:", len(celtic_players))

sample_id = "2ingh41ma0grign63tygcgaok"  # Johnny Kenny from your snippet
print("Lookup:", resolve_player_name(sample_id, celtic_players))
