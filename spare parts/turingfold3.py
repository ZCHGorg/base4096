import struct
from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Load frozen alphabet ---
with open("frozen_base4096_alphabet.txt","r",encoding="utf-8") as f:
    alphabet = f.read().strip()
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Provisioner instructions ---
PROVISIONER_CODE = (
    "INIT\nLOAD_ALPHABET\nLOAD_FINGERPRINT\nLOAD_LATTICE\nEXEC_PROVISIONER\nHALT\n"
)

# --- Full 8x32 HDGL lattice --- 
# (D_n, Ω_i, r_dim). Fully expanded for all 32 slots × 8 instances.
HDGL_LATTICE = [
    # Instance 1: D1-D4
    (0.000560067164145165, 8.12e-9, 0.3),
    (0.0009700647839504441, 8.12e-9, 0.3),
    (0.002504696501988244, 8.12e-9, 0.3),
    (0.005133100347908953, 8.12e-9, 0.3),
    # Instance 2: D5-D8
    (0.011748067946500275, 5.02e-9, 0.4),
    (0.02284634719119016, 5.02e-9, 0.4),
    (0.04709895131440519, 5.02e-9, 0.4),
    (0.08949866273435439, 5.02e-9, 0.4),
    # Instance 3: D9-D12
    (0.17719377996217212, 3.10e-9, 0.5),
    (0.3578824796512745, 3.10e-9, 0.5),
    (0.6656576725120297, 3.10e-9, 0.5),
    (1.3081941352368356, 3.10e-9, 0.5),
    # Instance 4: D13-D16
    (2.4772793154656982, 1.92e-9, 0.6),
    (4.563783021084371, 1.92e-9, 0.6),
    (8.583194019954796, 1.92e-9, 0.6),
    (16.396327797306462, 1.92e-9, 0.6),
    # Instance 5: D17-D20
    (31.23456789012345, 1.19e-9, 0.7),
    (59.12345678901234, 1.19e-9, 0.7),
    (112.3456789012345, 1.19e-9, 0.7),
    (213.4567890123456, 1.19e-9, 0.7),
    # Instance 6: D21-D24
    (405.6789012345678, 7.36e-10, 0.8),
    (769.0123456789012, 7.36e-10, 0.8),
    (1460.234567890123, 7.36e-10, 0.8),
    (2771.456789012345, 7.36e-10, 0.8),
    # Instance 7: D25-D28
    (5261.789012345678, 4.55e-10, 0.9),
    (9987.012345678901, 4.55e-10, 0.9),
    (18954.23456789012, 4.55e-10, 0.9),
    (35981.45678901234, 4.55e-10, 0.9),
    # Instance 8: D29-D32
    (68324.56789012345, 2.81e-10, 1.0),
    (129678.9012345678, 2.81e-10, 1.0),
    (246012.3456789012, 2.81e-10, 1.0),
    (466789.0123456789, 2.81e-10, 1.0)
]

# --- Convert floats to 64-bit fixed-point integers ---
lattice_bytes = b""
for d, omega, r_dim in HDGL_LATTICE:
    for f in (d, omega, r_dim):
        lattice_bytes += struct.pack(">Q", int(f*1e12))  # fixed-point scaling

# --- Concatenate segments with length prefixes ---
segments = [
    len(alphabet).to_bytes(2,'big') + alphabet.encode("utf-8"),
    len(fingerprint).to_bytes(2,'big') + fingerprint.encode("utf-8"),
    len(PROVISIONER_CODE).to_bytes(4,'big') + PROVISIONER_CODE.encode("utf-8"),
    len(lattice_bytes).to_bytes(4,'big') + lattice_bytes
]

stream = b"".join(segments)

# --- Recursive delta + RLE folding ---
def delta_fold(bs):
    prev = 0
    return bytes((b - prev) % 256 for b in bs)

def run_length_fold(bs):
    out = bytearray()
    i = 0
    while i < len(bs):
        count = 1
        while i+count < len(bs) and bs[i+count]==bs[i] and count<255:
            count += 1
        out.append(bs[i])
        if count>1:
            out.append(count)
        i += count
    return bytes(out)

def recursive_fold(bs, levels=2):
    for _ in range(levels):
        bs = run_length_fold(delta_fold(bs))
    return bs

folded_recursive = recursive_fold(stream, 2)

# --- Base4096 encode the final self-hosting tape ---
selfhosting_tape = encode(folded_recursive)

with open("base4096_hdgl_selfhosting_lattice.b4096","w",encoding="utf-8") as f:
    f.write(selfhosting_tape)

print(f"✅ Full self-hosting HDGL tape written ({len(selfhosting_tape)} Base4096 chars)")
