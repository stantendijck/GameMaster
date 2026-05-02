import requests
import json
import re


SPELLING_MISTAKES = {
    "futuresight": "future-sight",
    "super_power": "superpower",
    "pyroball": "pyro-ball",
    "myst_fire": "mystical-fire",
}

MOVE_REGEX_MAP = {
    r"^weather-ball-[a-z]+$": "weather-ball",
    r"^techno-blast-[a-z]+$": "techno-blast",
    r"^aura-wheel-[a-z]+$": "aura-wheel",
}

SUPPORTED_LANGUAGES = {
    "en",
    "ja",
    "fr",
    "de",
    "es",
    "it",
    "ko",
    "zh",
}

with open("raw/type_translations.json", "r") as f:
    type_translations = json.load(f)

with open("raw/new_moves.json", "r") as f:
    manual_move_translations = json.load(f)



def get_only_supported_languages(translations):
    out = {}
    for supported_language in SUPPORTED_LANGUAGES:
        if supported_language not in translations:
            if (translations['en'] in manual_move_translations) and (supported_language in manual_move_translations[translations['en']]):
                out[supported_language] = manual_move_translations[translations['en']][supported_language]
            else:
                out[supported_language] = translations['en']
        else:
            if supported_language == "zh":
                out[supported_language] = translations["zh-hant"]
            else:
                out[supported_language] = translations[supported_language]
    return {"values": out}

def get_species_languages(pokemon_id):
    url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/"
    data = requests.get(url).json()

    # Extract all language → name pairs
    translations = {
        entry["language"]["name"]: entry["name"]
        for entry in data["names"]
    }
    return get_only_supported_languages(translations)

def get_moves_languages(pokemon_name):
    url = f"https://pokeapi.co/api/v2/move/{pokemon_name.lower()}/"
    data = requests.get(url).json()

    # Extract all language → name pairs
    translations = {
        entry["language"]["name"]: entry["name"]
        for entry in data["names"]
    }
    return get_only_supported_languages(translations)


def get_type_languages(type_template):
    type_template = type_template.replace('POKEMON_TYPE_', '')
    return get_only_supported_languages(type_translations[type_template.lower()])


def fix_move_name(move_name):
    if move_name in SPELLING_MISTAKES:
        move_name = SPELLING_MISTAKES[move_name]
    move_name = move_name.replace('_fast', '').replace('_', '-')
    for pattern, base in MOVE_REGEX_MAP.items():
        if re.match(pattern, move_name):
            return base
    return move_name  # fallback: already a normal move