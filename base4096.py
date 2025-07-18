# base4096.py
# Author: Josef Kulovany - ZCHG.org
# Dynamic Base-4096 Encoder/Decoder with Extended Alphabet

import unicodedata
import os

# Generate or load the base4096 character set
def generate_base4096_alphabet(seed):
    seen = set()
    base_chars = []

    # Include seed chars first
    for ch in seed:
        if ch not in seen:
            seen.add(ch)
            base_chars.append(ch)

    # Fill to 4096 with valid Unicode chars
    for codepoint in range(0x20, 0x30000):
        c = chr(codepoint)
        if c not in seen and is_valid_char(c):
            base_chars.append(c)
            seen.add(c)
            if len(base_chars) == 4096:
                break

    if len(base_chars) < 4096:
        raise ValueError("Failed to generate 4096 unique characters.")
    
    return ''.join(base_chars)

# Validity check
def is_valid_char(c):
    try:
        name = unicodedata.name(c)
        return not any(x in name for x in ['CONTROL', 'PRIVATE USE', 'SURROGATE', 'UNASSIGNED', 'TAG'])
    except ValueError:
        return False

SEED = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "!@#$%^&*()-_+=[{]};:',\"<>?/" + ''.join(chr(i) for i in range(0x00, 0x42))
)

def load_frozen_alphabet(filepath="frozen_base4096_alphabet.txt") -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Frozen alphabet file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        alphabet = f.read().strip()
    if len(alphabet) != 4096:
        raise ValueError("Frozen alphabet length is not 4096 characters.")
    return alphabet

try:
    BASE4096_ALPHABET = load_frozen_alphabet()
except Exception as e:
    # Optional fallback, but warn
    print(f"Warning: Could not load frozen alphabet: {e}")
    print("Falling back to internal seed (not recommended).")
    BASE4096_ALPHABET = generate_base4096_alphabet(SEED)

CHAR_TO_INDEX = {ch: idx for idx, ch in enumerate(BASE4096_ALPHABET)}

# Encoder: bytes → base4096 string
def encode(data: bytes) -> str:
    num = int.from_bytes(data, byteorder='big')
    result = []
    while num > 0:
        num, rem = divmod(num, 4096)
        result.append(BASE4096_ALPHABET[rem])
    return ''.join(reversed(result)) or BASE4096_ALPHABET[0]

# Decoder: base4096 string → bytes
def decode(encoded: str) -> bytes:
    num = 0
    for char in encoded:
        if char not in CHAR_TO_INDEX:
            raise ValueError(f"Invalid character in input: {repr(char)}")
        num = num * 4096 + CHAR_TO_INDEX[char]
    # Determine minimum byte length
    length = (num.bit_length() + 7) // 8
    return num.to_bytes(length, byteorder='big')
