# fold25_hdgl_selfhosting.py
# Fully self-hosting HDGL tape generator

from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Load alphabet ---
with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
    alphabet = f.read().strip()

# --- Fingerprint ---
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Provisioner HDGL instructions ---
PROVISIONER_CODE = """
INIT
LOAD_ALPHABET
LOAD_FINGERPRINT
MAP_ALPHABET
MAP_FINGERPRINT
EXEC
HALT
"""

# --- Encode components to bytes ---
alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

# --- Concatenate with length prefixes ---
stream = (
    len(alphabet_bytes).to_bytes(2, 'big') + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(2, 'big') + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4, 'big') + provisioner_bytes
)

# --- Delta folding (recursive) ---
def delta_fold(bs):
    folded = []
    prev = 0
    for b in bs:
        delta = (b - prev) % 256
        folded.append(delta)
        prev = b
    return bytes(folded)

folded_stream = delta_fold(stream)

# --- Run-length / repetition folding ---
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

folded_compressed = run_length_fold(folded_stream)

# --- Base4096 encode final tape ---
selfhosting_tape = encode(folded_compressed)

# --- Write to file ---
with open("base4096_hdgl_selfhosting.b4096", "w", encoding="utf-8") as f:
    f.write(selfhosting_tape)

print(f"✅ Self-hosting HDGL tape written ({len(selfhosting_tape)} Base4096 chars)")
