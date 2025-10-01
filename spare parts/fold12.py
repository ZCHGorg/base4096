# fold11_hdgl_selfcontained.py
import base64
from base4096 import encode, load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Configuration ---
ALPHABET_FILE = "frozen_base4096_alphabet.txt"
OUTPUT_FILE = "base4096_hdgl_selfcontained.hdgl"

# Load frozen alphabet
alphabet_text = load_frozen_alphabet(ALPHABET_FILE)

# Compute fingerprint
fingerprint_text = canonical_base4096_fingerprint(alphabet_text)

# Provisioner code
PROVISIONER_CODE = """
print('✅ HDGL Self-Provisioner Executed')
# Example: restore alphabet/fingerprint, run additional setup...
"""

# --- Combine everything into a single byte stream ---
# Layout: [alphabet length(2 bytes) | alphabet bytes | fingerprint length(2 bytes) | fingerprint bytes | provisioner bytes]
def make_hdgl_stream(alphabet, fingerprint, provisioner):
    alphabet_bytes = alphabet.encode("utf-8")
    fingerprint_bytes = fingerprint.encode("utf-8")
    provisioner_bytes = provisioner.encode("utf-8")
    
    stream = (
        len(alphabet_bytes).to_bytes(2, "big") + alphabet_bytes +
        len(fingerprint_bytes).to_bytes(2, "big") + fingerprint_bytes +
        provisioner_bytes
    )
    return stream

hdgl_bytes = make_hdgl_stream(alphabet_text, fingerprint_text, PROVISIONER_CODE)

# --- Encode stream with Base4096 or Metisa64 ---
hdgl_encoded = encode(hdgl_bytes)  # Base4096 encoding
# For Metisa64 (optional compression), you can use: base64.b85encode(hdgl_bytes).decode('ascii')

# --- Embed tiny self-unfolder stub ---
UNFOLDER_CODE = f"""
import sys
from base4096 import decode
hdgl_data = decode({hdgl_encoded!r})
# Extract alphabet
a_len = int.from_bytes(hdgl_data[:2], 'big')
alphabet = hdgl_data[2:2+a_len].decode('utf-8')
# Extract fingerprint
f_len = int.from_bytes(hdgl_data[2+a_len:4+a_len], 'big')
fingerprint = hdgl_data[4+a_len:4+a_len+f_len].decode('utf-8')
# Extract provisioner and execute
provisioner = hdgl_data[4+a_len+f_len:].decode('utf-8')
exec(provisioner)
"""

# --- Write single self-unfolding file ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(UNFOLDER_CODE)

print(f"✅ Self-contained HDGL written to {OUTPUT_FILE}")
