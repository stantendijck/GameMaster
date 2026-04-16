# decode.py
from src.gamemaster_pb2 import GameMaster
from google.protobuf.json_format import MessageToDict
from google.protobuf.internal.decoder import _DecodeVarint
import base64
import json

# --- Helper functions ---

def uint64_to_int64(value):
    """Convert uint64 to signed int64, handling large numbers."""
    if isinstance(value, str) and value.isdigit():
        num = int(value)
        if num >= 2**63:
            return num - 2**64
        return num
    elif isinstance(value, int):
        if value >= 2**63:
            return value - 2**64
        return value
    return value

def fix_numbers(obj):
    """Recursively fix uint64 numbers in dict/list."""
    if isinstance(obj, dict):
        return {k: fix_numbers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_numbers(v) for v in obj]
    else:
        return uint64_to_int64(obj)

def decode_packed_varints(raw_bytes):
    """Decode packed varints from raw bytes (protobuf encoding)."""
    numbers = []
    i = 0
    while i < len(raw_bytes):
        n, new_i = _DecodeVarint(raw_bytes, i)
        numbers.append(n)
        i = new_i
    return numbers

import struct

def decode_packed_floats(raw_bytes):
    """Decode protobuf packed float field (4 bytes per float)."""
    floats = []
    for i in range(0, len(raw_bytes), 4):
        chunk = raw_bytes[i:i+4]
        if len(chunk) == 4:
            (value,) = struct.unpack("<f", chunk)  # little-endian float
            floats.append(value)
    return floats


def packed_varint_field_to_list(b64_str):
    """Convert base64-encoded packed varint field to integer list."""
    raw_bytes = base64.b64decode(b64_str)
    return decode_packed_varints(raw_bytes)

# def fix_packed_varints(obj):
#     """Recursively fix known packed varint fields in JSON dict."""
#     packed_fields = ("quickMoves", "cinematicMoves", "eliteCinematicMoves", "effectiveness")  # add more if needed
#     if isinstance(obj, dict):
#         new_obj = {}
#         for k, v in obj.items():
#             if isinstance(v, str) and k in packed_fields:
#                 try:
#                     new_obj[k] = packed_varint_field_to_list(v)
#                 except Exception:
#                     # fallback: keep as-is if decoding fails
#                     new_obj[k] = v
#             else:
#                 new_obj[k] = fix_packed_varints(v)
#         return new_obj
#     elif isinstance(obj, list):
#         return [fix_packed_varints(v) for v in obj]
#     else:
#         return obj

def fix_packed_varints(obj):
    packed_int_fields = ("quickMoves", "cinematicMoves", "eliteCinematicMoves")
    packed_float_fields = ("effectiveness",)

    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():

            # --- FLOAT PACKED FIELDS ---
            if isinstance(v, str) and k in packed_float_fields:
                try:
                    raw = base64.b64decode(v)
                    new_obj[k] = decode_packed_floats(raw)
                except Exception:
                    new_obj[k] = v
                continue

            # --- INT PACKED FIELDS ---
            if isinstance(v, str) and k in packed_int_fields:
                try:
                    new_obj[k] = packed_varint_field_to_list(v)
                except Exception:
                    new_obj[k] = v
                continue

            new_obj[k] = fix_packed_varints(v)

        return new_obj

    elif isinstance(obj, list):
        return [fix_packed_varints(v) for v in obj]

    return obj


# --- Main decoding ---

with open("raw/v2_GAME_MASTER", "rb") as f:
    data = f.read()

gm = GameMaster()
gm.ParseFromString(data)

# Convert protobuf to dict (uint64 fields will become strings)
raw_dict = MessageToDict(gm)

# Step 1: convert uint64 → signed int
fixed_dict = fix_numbers(raw_dict)

# Step 2: decode packed varints like quickMoves/cinematicMoves
fixed_dict = fix_packed_varints(fixed_dict)
# print(fixed_dict)

# Step 3: write JSON
with open("src/game_master.json", "w", encoding="utf-8") as out:
    json.dump(fixed_dict["templates"], out, indent=2)

print("✅ Game Master JSON written to src/game_master.json")

# Notes: - how to use:
# protoc --python_out=. ./python/gamemaster.proto
# /Users/stantendijjck/AndroidStudioProjects/PokemonGOQuiz/.venv/bin/python /Users/stantendijjck/AndroidStudioProjects/PokemonGOQuiz/python/decode.py
# or
# protoc --decode_raw < ./python/v2_GAME_MASTER > ./python/output.txt