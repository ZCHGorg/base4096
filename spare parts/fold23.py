# fold23_hdgl_byte_stream.py
# Generates a fully self-unfolding HDGL byte stream with alphabet + fingerprint + provisioner

import os
from base4096 import encode, decode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- 1️⃣ Load frozen Base4096 alphabet ---
try:
    with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
        alphabet = f.read().strip().replace("\n", "").replace("\r", "")
except FileNotFoundError:
    raise RuntimeError("Frozen alphabet not found. Please provide frozen_base4096_alphabet.txt")

if len(alphabet) != 4096 or len(set(alphabet)) != 4096:
    raise ValueError("Alphabet must have exactly 4096 unique characters.")

# --- 2️⃣ Compute canonical fingerprint ---
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- 3️⃣ Embed full HDGL provisioner instructions ---
PROVISIONER_CODE = """
# HDGL Provisioner Instructions
LOAD_ALPHABET
LOAD_FINGERPRINT
INIT_VM
MAP_ALPHABET
MAP_FINGERPRINT
EXEC_PROVISIONER
READY
"""

# --- 4️⃣ Encode all components to bytes ---
alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

# --- 5️⃣ Concatenate into a single byte stream ---
hdgl_bytes = b''.join([
    b'HDGLv1',                   # header
    len(alphabet_bytes).to_bytes(2, 'big'), alphabet_bytes,
    len(fingerprint_bytes).to_bytes(2, 'big'), fingerprint_bytes,
    len(provisioner_bytes).to_bytes(4, 'big'), provisioner_bytes
])

# Optional: Encode entire byte stream in Base4096 for textual storage
hdgl_b4096_stream = encode(hdgl_bytes)

# --- 6️⃣ Write self-unfolding HDGL byte stream ---
output_file = "base4096_hdgl_selfunfolding.b4096"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(hdgl_b4096_stream)

print(f"✅ Fully self-unfolding HDGL byte stream written to {output_file}")
print(f"Stream length: {len(hdgl_b4096_stream)} Base4096 characters")
