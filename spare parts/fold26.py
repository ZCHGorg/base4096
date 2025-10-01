# fold_recursive_hdgl.py
from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Load alphabet ---
with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
    alphabet = f.read().strip()

# --- Fingerprint ---
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Provisioner HDGL instructions (actual logic) ---
PROVISIONER_CODE = """
INIT
LOAD_ALPHABET
LOAD_FINGERPRINT
MAP_ALPHABET
MAP_FINGERPRINT
EXEC
HALT
"""

# --- Convert to bytes ---
alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

# --- Concatenate with length prefixes ---
stream = (
    len(alphabet_bytes).to_bytes(2, 'big') + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(2, 'big') + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4, 'big') + provisioner_bytes
)

# --- Recursive delta folding ---
def delta_fold(bs):
    folded = []
    prev = 0
    for b in bs:
        delta = (b - prev) % 256
        folded.append(delta)
        prev = b
    return bytes(folded)

# --- Optional RLE compression ---
def run_length_fold(bs):
    result = bytearray()
    i = 0
    while i < len(bs):
        count = 1
        while i + count < len(bs) and bs[i + count] == bs[i] and count < 255:
            count += 1
        result.append(bs[i])
        if count > 1:
            result.append(count)
        i += count
    return bytes(result)

# --- First folding layer ---
folded_stream = run_length_fold(delta_fold(stream))

# --- Multi-level recursive folding ---
def recursive_fold(bs, levels=2):
    for _ in range(levels):
        bs = run_length_fold(delta_fold(bs))
    return bs

folded_recursive = recursive_fold(folded_stream, levels=2)

# --- Base4096 encode final self-hosting tape ---
selfhosting_tape = encode(folded_recursive)

# --- Write to file ---
with open("base4096_hdgl_selfhosting_recursive.b4096", "w", encoding="utf-8") as f:
    f.write(selfhosting_tape)

print(f"✅ Recursive self-hosting HDGL tape written ({len(selfhosting_tape)} Base4096 chars)")
