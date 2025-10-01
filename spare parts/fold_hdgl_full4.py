# fold_hdgl_full4.py
# Full self-provisioning HDGL generator
# Writes Base4096 text + raw binary, ready for executor

import struct
from base4096 import encode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# -----------------------------
# Config / Inputs
# -----------------------------
ALPHABET_FILE = "frozen_base4096_alphabet.txt"

# Expanded provisioner: steps for self-provisioning
PROVISIONER_CODE = """
# HDGL Provisioner Instructions
# Strand / Slots / Wave / Recursion / Omega

# Step 1: normalize amplitudes
NORM

# Step 2: scale amplitudes up to usable range
SCALE 1e6

# Step 3: phase alignment
PHASESHIFT 0.25

# Step 4: frequency tuning
OMEGAMULT 2.0

# Step 5: measure system energy
ENERGY

# Step 6: fold lattice slots into superposition
FOLD256
"""

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
# Lattice slots: 256 slots (8 instances × 32)
# Each: (D_n, Ω_n, r_dim)
# Example values; replace with full superposition data
# -----------------------------
LATTICE_SLOTS = []
# Instance 1–8, each 32 slots
for instance_idx in range(8):
    base_d = 1e-6 * (2 ** instance_idx)      # scaled D_n
    omega = 1 / (1.6180339887 ** (instance_idx+1)) ** 7
    r_dim = 0.3 + 0.1 * instance_idx
    for slot_idx in range(32):
        LATTICE_SLOTS.append((
            base_d * (slot_idx+1),
            omega,
            r_dim
        ))

assert len(LATTICE_SLOTS) == 8*32, f"Must have 256 slots, got {len(LATTICE_SLOTS)}"

# -----------------------------
# Serialize sections
# -----------------------------
alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

# Convert floats to 8-byte little-endian doubles
lattice_bytes = b"".join(
    struct.pack("<ddd", d, omega, r_dim)
    for d, omega, r_dim in LATTICE_SLOTS
)

# Prefix lengths: 4-byte little-endian
data = (
    len(alphabet_bytes).to_bytes(4, 'little') + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(4, 'little') + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4, 'little') + provisioner_bytes +
    len(LATTICE_SLOTS).to_bytes(4, 'little') +
    lattice_bytes
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
print(f"Alphabet length: {len(alphabet_bytes)}")
print(f"Fingerprint length: {len(fingerprint_bytes)}")
print(f"Provisioner length: {len(provisioner_bytes)}")
print(f"Lattice slots serialized: {len(LATTICE_SLOTS)}")
