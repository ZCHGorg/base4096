# freeze_base4096_alphabet.py (fixed robust)
import unicodedata
import json

SEED = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "!@#$%^&*()-_+=[{]};:',\"<>?/`|~"
)

def is_valid_char(c):
    try:
        name = unicodedata.name(c)
        # Exclude control, surrogates, private, tags, unassigned
        if any(bad in name for bad in ['CONTROL','PRIVATE USE','SURROGATE','UNASSIGNED','TAG']):
            return False
        # Exclude whitespace that may duplicate
        if c in '\n\r\t\u00A0':
            return False
        return True
    except ValueError:
        return False

def generate_frozen_base4096(seed):
    seen = set()
    base_chars = []

    # Preserve seed order
    for ch in seed:
        if ch not in seen and is_valid_char(ch):
            seen.add(ch)
            base_chars.append(ch)

    for codepoint in range(0x20, 0x30000):
        c = chr(codepoint)
        if c not in seen and is_valid_char(c):
            base_chars.append(c)
            seen.add(c)
            if len(base_chars) == 4096:
                break

    if len(base_chars) != 4096:
        raise ValueError(f"Only generated {len(base_chars)} valid characters.")
    return ''.join(base_chars)

# Generate
frozen_alphabet = generate_frozen_base4096(SEED)

# Save as plain text (continuous, no line breaks)
with open("frozen_base4096_alphabet.txt","w",encoding="utf-8") as f:
    f.write(frozen_alphabet)

# Save as Python constant (escaped safely)
with open("frozen_base4096_alphabet.py","w",encoding="utf-8") as f:
    f.write("# frozen_base4096_alphabet.py\n")
    f.write("# Canonical Base-4096 Alphabet (frozen, deterministic)\n\n")
    f.write("FROZEN_BASE4096_ALPHABET = (\n")
    for i in range(0, 4096, 64):
        chunk = frozen_alphabet[i:i+64]
        f.write(f"    {json.dumps(chunk, ensure_ascii=False)}\n")
    f.write(")\n")

print("✅ Fixed canonical Base-4096 alphabet exported.")
print("Length:", len(frozen_alphabet), "Unique:", len(set(frozen_alphabet)))
