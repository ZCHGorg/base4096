# fold_hdgl_full.py
# Generates a full 256-slot HDGL self-provisioning Base4096 text

from base4096 import encode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# -----------------------------
# Config / Inputs
# -----------------------------
ALPHABET_FILE = "frozen_base4096_alphabet.txt"

PROVISIONER_CODE = """
# HDGL Provisioner Instructions
# Strand / Slots / Wave / Recursion / Omega
# Placeholder instructions — fully folded in Base4096 stream
"""

# -----------------------------
# Lattice: 32 × 8 = 256 slots
# -----------------------------
LATTICE_SLOTS = []
for i in range(32):
    for j in range(8):
        d = (i + 1) * (j + 1) * 1e-6
        omega = 8.12e-9
        r_dim = 0.3 + (j * 0.01)
        LATTICE_SLOTS.append((d, omega, r_dim))

assert len(LATTICE_SLOTS) == 256, "Must have all 256 slots!"

# -----------------------------
# Load frozen alphabet
# -----------------------------
with open(ALPHABET_FILE, "r", encoding="utf-8") as f:
    alphabet = f.read().strip().replace("\n", "")

# -----------------------------
# Compute fingerprint
# -----------------------------
fingerprint = canonical_base4096_fingerprint(alphabet)

# -----------------------------
# Serialization helpers
# -----------------------------
def float_to_bytes(f):
    return int(f * 1e12).to_bytes(8, 'big')  # fixed-point 8-byte

alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

lattice_bytes = b"".join(
    float_to_bytes(d) + float_to_bytes(omega) + float_to_bytes(r_dim)
    for d, omega, r_dim in LATTICE_SLOTS
)

# Prefix lengths + concatenate
data = (
    len(alphabet_bytes).to_bytes(2, 'big') + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(2, 'big') + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4, 'big') + provisioner_bytes +
    len(lattice_bytes).to_bytes(4, 'big') + lattice_bytes
)

# -----------------------------
# Encode to Base4096
# -----------------------------
hdgl_base4096 = encode(data)

# -----------------------------
# Write self-provisioning HDGL text
# -----------------------------
with open("base4096_hdgl_selfprovisioning.txt", "w", encoding="utf-8") as f:
    f.write(hdgl_base4096)

print("✅ Self-provisioning HDGL Base4096 written to base4096_hdgl_selfprovisioning.txt")
