from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint
import struct

# --- Load alphabet ---
with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
    alphabet = f.read().strip()

fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Provisioner HDGL instructions (minimal example) ---
PROVISIONER_CODE = "INIT\nLOAD_ALPHABET\nLOAD_FINGERPRINT\nEXEC\nHALT\n"

# --- HDGL lattice analog/digital slots ---
HDGL_LATTICE = [
    # D_n(r), Ω_i, r_dim as float tuples
    (0.000560067164145165, 8.12e-9, 0.3),
    (0.0009700647839504441, 5.02e-9, 0.4),
    (0.002504696501988244, 3.10e-9, 0.5),
    # ... all 32 D_n(r) entries ...
]

# Convert lattice floats → int bytes (fixed-point 1e12)
lattice_bytes = b""
for d, omega, r_dim in HDGL_LATTICE:
    for f in (d, omega, r_dim):
        lattice_bytes += struct.pack(">Q", int(f*1e12))  # 64-bit unsigned

# --- Concatenate all segments with length prefixes ---
segments = [
    len(alphabet).to_bytes(2,'big') + alphabet.encode("utf-8"),
    len(fingerprint).to_bytes(2,'big') + fingerprint.encode("utf-8"),
    len(PROVISIONER_CODE).to_bytes(4,'big') + PROVISIONER_CODE.encode("utf-8"),
    len(lattice_bytes).to_bytes(4,'big') + lattice_bytes
]

stream = b"".join(segments)

# --- Recursive delta + RLE fold ---
def delta_fold(bs):
    folded = []
    prev = 0
    for b in bs:
        folded.append((b - prev) % 256)
        prev = b
    return bytes(folded)

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

folded = run_length_fold(delta_fold(stream))

# Optional: recursive folding
def recursive_fold(bs, levels=2):
    for _ in range(levels):
        bs = run_length_fold(delta_fold(bs))
    return bs

folded_recursive = recursive_fold(folded, 2)

# --- Base4096 encode ---
selfhosting_tape = encode(folded_recursive)

with open("base4096_hdgl_selfhosting_lattice.b4096", "w", encoding="utf-8") as f:
    f.write(selfhosting_tape)

print(f"✅ Self-hosting HDGL tape with lattice written ({len(selfhosting_tape)} Base4096 chars)")
