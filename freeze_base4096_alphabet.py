# freeze_base4096_alphabet.py
# Run this ONCE to freeze the Base-4096 alphabet

import unicodedata

SEED = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "!@#$%^&*()-_+=[{]};:',\"<>?/"
    + ''.join(chr(i) for i in range(0x00, 0x42))  # Includes control chars
)

def is_valid_char(c):
    try:
        name = unicodedata.name(c)
        return not any(bad in name for bad in ['CONTROL', 'PRIVATE USE', 'SURROGATE', 'UNASSIGNED', 'TAG'])
    except ValueError:
        return False

def generate_frozen_base4096(seed):
    seen = set()
    base_chars = []

    # Preserve seed order
    for ch in seed:
        if ch not in seen:
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
        raise ValueError(f"Only generated {len(base_chars)} characters.")
    return ''.join(base_chars)

# Generate and export
frozen_alphabet = generate_frozen_base4096(SEED)

# Save as plain text (1 char per index, newline every 64 chars for readability)
with open("frozen_base4096_alphabet.txt", "w", encoding="utf-8") as f:
    for i, ch in enumerate(frozen_alphabet):
        f.write(ch)
        if (i + 1) % 64 == 0:
            f.write("\n")

# Save as Python constant
with open("frozen_base4096_alphabet.py", "w", encoding="utf-8") as f:
    f.write("# frozen_base4096_alphabet.py\n")
    f.write("# Canonical Base-4096 Alphabet (frozen, deterministic)\n\n")
    f.write("FROZEN_BASE4096_ALPHABET = (\n")
    for i in range(0, 4096, 64):
        chunk = frozen_alphabet[i:i+64]
        f.write(f"    \"{chunk}\"\n")
    f.write(")\n")

print("✅ Canonical Base-4096 alphabet frozen and exported.")
