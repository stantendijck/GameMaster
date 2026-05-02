# decode.py
from src.gamemaster_pb2 import GameMaster
import src.PokeTranslations as PokeTranslation # import get_moves_languages, fix_move_name
import src.decoding as decoding
from google.protobuf.json_format import MessageToDict
import json


# --- Main decoding ---

with open("raw/v2_GAME_MASTER", "rb") as f:
    data = f.read()

gm = GameMaster()
gm.ParseFromString(data)

# Convert protobuf to dict (uint64 fields will become strings)
raw_dict = MessageToDict(gm)

# Step 1: convert uint64 → signed int
fixed_dict = decoding.fix_numbers(raw_dict)

# Step 2: decode packed varints like quickMoves/cinematicMoves
fixed_dict = decoding.fix_packed_varints(fixed_dict)

weird_moves = [
    "wrap_green",
    "wrap_pink",
    "hydro_pump_blastoise",
    "scald_blastoise",
    "water_gun_fast_blastoise",
]

# Step 3: subset json to only contain relevant fields
subset_json = [
    d 
    for d in fixed_dict["templates"]
    if (
        ("combatMove" in d["data"].keys() and not d["templateId"].endswith("_PLUS") and not d["data"]["combatMove"]["name"] in weird_moves )
        or "pokemonSettings" in d["data"].keys()
        or "pokemonType" in d["data"].keys()
    )
]
# print(subset_json)
print('here')

# Step 4: add translations for moves
# moves = [entry for entry in subset_json if 'combatMove' in entry['data']]
error_names = []
for i, entry in enumerate(subset_json):
    print(i, len(subset_json))
    print(entry)
    try:
        if 'combatMove' in entry["data"]:
            name = entry["data"]["combatMove"]["name"]
            fixed_name = PokeTranslation.fix_move_name(name)
            translations = PokeTranslation.get_moves_languages(fixed_name)
            entry["data"]["combatMove"]["translations"] = translations
        elif 'pokemonSettings' in entry["data"]:
            name = entry["data"]["pokemonSettings"]["pokemonId"]
            translations = PokeTranslation.get_species_languages(name)
            entry["data"]["pokemonSettings"]["translations"] = translations
        elif 'pokemonType' in entry["data"]:
            name = entry["data"]["templateId"]
            translations = PokeTranslation.get_type_languages(name)
            entry["data"]["pokemonType"]["translations"] = translations
    except:
        error_names.append(name)
        pass
print('error names:')
print(error_names)


# Step 5: write JSON
with open("src/game_master.json", "w", encoding="utf-8") as out:
    json.dump(subset_json, out, indent=2)

print("✅ Game Master JSON written to src/game_master.json")

# Notes: - how to use:
# protoc --python_out=. ./python/gamemaster.proto
# /Users/stantendijjck/AndroidStudioProjects/PokemonGOQuiz/.venv/bin/python /Users/stantendijjck/AndroidStudioProjects/PokemonGOQuiz/python/decode.py
# or
# protoc --decode_raw < ./python/v2_GAME_MASTER > ./python/output.txt