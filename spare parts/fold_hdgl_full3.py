# fold_hdgl_full3.py
# HDGL full self-provisioning fold generator
# Author: Josef Kulovany - ZCHG.org

from base4096 import encode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint
from hdgl_slots import get_hdgl_slots

# -----------------------------
# Provisioner Instructions
# -----------------------------
PROVISIONER_CODE = """
# HDGL Provisioner Instructions
# Strand / Slots / Wave / Recursion / Omega
# All 256 lattice slots are folded below.
# Each slot is (d, omega, r_dim), stored as fixed-point 8-byte triples.
# Self-describing and self-provisioning.
"""

# -----------------------------
# Load Alphabet
# -----------------------------
alphabet = BASE4096_ALPHABET
assert len(alphabet) == 4096, "Alphabet must be 4096 characters!"

# -----------------------------
# Compute Fingerprint
# -----------------------------
fingerprint = canonical_base4096_fingerprint(alphabet)

# -----------------------------
# Load 256 Lattice Slots
# -----------------------------
LATTICE_SLOTS = get_hdgl_slots()
assert len(LATTICE_SLOTS) == 256, "Must have 256 slots!"

# -----------------------------
# Serialization Helpers
# -----------------------------
def float_to_bytes(f: float) -> bytes:
    """
    Fixed-point: scale floats to 1e12 and store as 8 bytes.
    """
    return int(f * 1e12).to_bytes(8, "big", signed=False)

# Serialize alphabet, fingerprint, provisioner
alphabet_bytes = alphabet.encode("utf-8")      # Full Unicode alphabet
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

# Serialize lattice
lattice_bytes = b"".join(
    float_to_bytes(d) + float_to_bytes(omega) + float_to_bytes(r_dim)
    for d, omega, r_dim in LATTICE_SLOTS
)

# -----------------------------
# Prefix lengths + concatenate
# -----------------------------
data = (
    len(alphabet_bytes).to_bytes(2, "big") + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(2, "big") + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4, "big") + provisioner_bytes +
    len(lattice_bytes).to_bytes(4, "big") + lattice_bytes
)

# -----------------------------
# Encode to Base4096
# -----------------------------
hdgl_base4096 = encode(data)

# -----------------------------
# Write outputs
# -----------------------------
with open("base4096_hdgl_selfprovisioning.txt", "w", encoding="utf-8") as f:
    f.write(hdgl_base4096)

with open("base4096_hdgl_selfprovisioning.bin", "wb") as f:
    f.write(data)

print("✅ Self-provisioning HDGL Base4096 written to base4096_hdgl_selfprovisioning.txt")
print("✅ Raw binary written to base4096_hdgl_selfprovisioning.bin")
print(f"Alphabet length: {len(alphabet)}")
print(f"Fingerprint length: {len(fingerprint_bytes)} bytes")
print(f"Provisioner length: {len(provisioner_bytes)} bytes")
print(f"Lattice slots serialized: {len(LATTICE_SLOTS)}")
