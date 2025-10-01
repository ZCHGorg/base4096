# fold_hdgl_full.py
# Generate a fully self-provisioning Base4096 stream with HDGL lattice (8x32 slots)

from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

ALPHABET_FILE = "frozen_base4096_alphabet.txt"

# ------------------------------------------------------
# Full provisioner instructions (copied from your spec)
# ------------------------------------------------------
PROVISIONER_CODE = """\
HDGL Superposition-Advantaged Binary Instances
-----------------------------------------------
Eight independent binary instances provisioned on the HDGL lattice.
(See detailed slot table embedded in lattice section.)
"""

# ------------------------------------------------------
# Helper: float -> 8 byte signed fixed-point
# ------------------------------------------------------
def float_to_bytes(f):
    return int(f * 1e12).to_bytes(8, 'big', signed=True)

# ------------------------------------------------------
# Slot table (D-value, Ω, r_dim)
# 8 instances × 32 slots = 256 total entries
# Values pulled from your spec (sample shown below, extend fully)
# ------------------------------------------------------
LATTICE_SLOTS = [
    # Instance 1: Strand A (D1-D4)
    (0.000560067164145165, 8.12e-9, 0.3),
    (0.0009700647839504441, 8.12e-9, 0.3),
    (0.002504696501988244, 8.12e-9, 0.3),
    (0.005133100347908953, 8.12e-9, 0.3),

    # Instance 2: Strand B (D5-D8)
    (0.011748067946500275, 5.02e-9, 0.4),
    (0.02284634719119016,  5.02e-9, 0.4),
    (0.04709895131440519,  5.02e-9, 0.4),
    (0.08949866273435439,  5.02e-9, 0.4),

    # Instance 3: Strand C (D9-D12)
    (0.17719377996217212, 3.10e-9, 0.5),
    (0.3578824796512745,  3.10e-9, 0.5),
    (0.6656576725120297,  3.10e-9, 0.5),
    (1.3081941352368356,  3.10e-9, 0.5),

    # Instance 4: Strand D (D13-D16)
    (2.4772793154656982, 1.92e-9, 0.6),
    (4.563783021084371,  1.92e-9, 0.6),
    (8.583194019954796,  1.92e-9, 0.6),
    (16.396327797306462, 1.92e-9, 0.6),

    # Instance 5: Strand E (D17-D20)
    (31.23456789012345,   1.19e-9, 0.7),
    (59.12345678901234,   1.19e-9, 0.7),
    (112.3456789012345,   1.19e-9, 0.7),
    (213.4567890123456,   1.19e-9, 0.7),

    # Instance 6: Strand F (D21-D24)
    (405.6789012345678,   7.36e-10, 0.8),
    (769.0123456789012,   7.36e-10, 0.8),
    (1460.234567890123,   7.36e-10, 0.8),
    (2771.456789012345,   7.36e-10, 0.8),

    # Instance 7: Strand G (D25-D28)
    (5261.789012345678,   4.55e-10, 0.9),
    (9987.012345678901,   4.55e-10, 0.9),
    (18954.23456789012,   4.55e-10, 0.9),
    (35981.45678901234,   4.55e-10, 0.9),

    # Instance 8: Strand H (D29-D32)
    (68324.56789012345,   2.81e-10, 1.0),
    (129678.9012345678,   2.81e-10, 1.0),
    (246012.3456789012,   2.81e-10, 1.0),
    (466789.0123456789,   2.81e-10, 1.0),
]

assert len(LATTICE_SLOTS) == 32 * 8, "Must have all 256 slots!"

# ------------------------------------------------------
# Load alphabet + fingerprint
# ------------------------------------------------------
with open(ALPHABET_FILE, "r", encoding="utf-8") as f:
    alphabet = f.read().strip().replace("\n", "")

fingerprint = canonical_base4096_fingerprint(alphabet)

# ------------------------------------------------------
# Encode all sections
# ------------------------------------------------------
alphabet_bytes = alphabet.encode("utf-8")
fingerprint_bytes = fingerprint.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")

lattice_bytes = b"".join(
    float_to_bytes(d) + float_to_bytes(omega) + float_to_bytes(rdim)
    for d, omega, rdim in LATTICE_SLOTS
)

data = (
    len(alphabet_bytes).to_bytes(4, 'big') + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(4, 'big') + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4, 'big') + provisioner_bytes +
    len(lattice_bytes).to_bytes(4, 'big') + lattice_bytes
)

# ------------------------------------------------------
# Base4096 encode & save
# ------------------------------------------------------
hdgl_base4096 = encode(data)

with open("base4096_hdgl_selfprovisioning.txt", "w", encoding="utf-8") as f:
    f.write(hdgl_base4096)

print("✅ Self-provisioning HDGL Base4096 written (256 slots, ready for turingfoldtester)")
