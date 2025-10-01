# fold_hdgl_selfprovisioning.py
from base4096 import encode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# -----------------------------
# Config / Inputs
# -----------------------------
ALPHABET_FILE = "frozen_base4096_alphabet.txt"
PROVISIONER_CODE = """
# HDGL Provisioner Instructions
# Strand / Slots / Wave / Recursion / Omega
# Example: D_1(r)=0.000560067164145165
# Full instructions folded here
"""
LATTICE_SLOTS = [
    # Example lattice slots: (d, omega, r_dim)
    (0.000560067164145165, 8.12e-9, 0.3),
    (0.0009700647839504441, 8.12e-9, 0.3),
    (0.002504696501988244, 8.12e-9, 0.3),
    (0.005133100347908953, 8.12e-9, 0.3),
    # ... extend for all 32 D_n slots ...
]

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
# Serialize sections
# -----------------------------
def float_to_bytes(f):
    return int(f*1e12).to_bytes(8, 'big')  # 8-byte fixed-point

alphabet_bytes = alphabet.encode("latin1")
fingerprint_bytes = fingerprint.encode("latin1")
provisioner_bytes = PROVISIONER_CODE.encode("latin1")

lattice_bytes = b"".join(
    float_to_bytes(d) + float_to_bytes(omega) + float_to_bytes(r_dim)
    for d, omega, r_dim in LATTICE_SLOTS
)

# Prefix lengths
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
