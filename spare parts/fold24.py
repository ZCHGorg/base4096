# fold24_hdgl_recursive.py
# Fully recursive self-expressive HDGL program generator

from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Load frozen Base4096 alphabet ---
with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
    alphabet = f.read().strip().replace("\n","").replace("\r","")

# --- Compute fingerprint ---
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Provisioner instructions (HDGL logic) ---
PROVISIONER_CODE = """
LOAD_ALPHABET
LOAD_FINGERPRINT
INIT_VM
MAP_ALPHABET
MAP_FINGERPRINT
EXEC_PROVISIONER
READY
"""

# --- Encode everything as bytes ---
alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

# --- Concatenate components with length prefixes ---
stream = b''.join([
    len(alphabet_bytes).to_bytes(2, 'big') + alphabet_bytes,
    len(fingerprint_bytes).to_bytes(2, 'big') + fingerprint_bytes,
    len(provisioner_bytes).to_bytes(4, 'big') + provisioner_bytes
])

# --- Recursive folding: delta encode each byte w.r.t previous, produce signed bytes ---
def fold_bytes_delta(bs):
    folded = []
    prev = 0
    for b in bs:
        delta = (b - prev) % 256
        folded.append(delta)
        prev = b
    return bytes(folded)

folded_stream = fold_bytes_delta(stream)

# --- Encode folded byte stream in Base4096 for self-expressive storage ---
hdgl_recursive_b4096 = encode(folded_stream)

# --- Write output ---
output_file = "base4096_hdgl_recursive_selfprovisioning.b4096"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(hdgl_recursive_b4096)

print(f"✅ Fully recursive self-provisioning HDGL program written to {output_file}")
print(f"Stream length: {len(hdgl_recursive_b4096)} Base4096 chars")
