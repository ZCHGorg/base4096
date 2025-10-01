import struct
from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Load frozen alphabet ---
with open("frozen_base4096_alphabet.txt","r",encoding="utf-8") as f:
    alphabet = f.read().strip()
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Minimal provisioner HDGL logic ---
PROVISIONER_CODE = (
    "INIT\nLOAD_ALPHABET\nLOAD_FINGERPRINT\nLOAD_LATTICE\nEXEC_PROVISIONER\nHALT\n"
)

# --- Full 8x32 lattice: D_n(r), Ω_i, r_dim ---
# For brevity, partial numbers here; in actual code, all 32 per instance should be listed.
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
    # ... Instances 4-8: D13-D32 (fill all 32 slots) ...
]

# --- Encode floats to fixed-point 64-bit unsigned integers ---
lattice_bytes = b""
for d, omega, r_dim in HDGL_LATTICE:
    for f in (d, omega, r_dim):
        lattice_bytes += struct.pack(">Q", int(f*1e12))  # multiply by 1e12 for precision

# --- Concatenate segments with length prefixes ---
segments = [
    len(alphabet).to_bytes(2,'big') + alphabet.encode("utf-8"),
    len(fingerprint).to_bytes(2,'big') + fingerprint.encode("utf-8"),
    len(PROVISIONER_CODE).to_bytes(4,'big') + PROVISIONER_CODE.encode("utf-8"),
    len(lattice_bytes).to_bytes(4,'big') + lattice_bytes
]

stream = b"".join(segments)

# --- Delta-fold and RLE-fold ---
def delta_fold(bs):
    prev = 0
    return bytes((b - prev) % 256 for b in bs)

def run_length_fold(bs):
    out = bytearray()
    i = 0
    while i < len(bs):
        count = 1
        while i + count < len(bs) and bs[i+count] == bs[i] and count<255:
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

print(f"✅ Self-hosting HDGL tape written ({len(selfhosting_tape)} Base4096 chars)")
