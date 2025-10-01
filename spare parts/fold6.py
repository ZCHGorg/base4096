import json
from base4096 import load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

def zigzag_encode(n: int) -> int:
    return (n << 1) ^ (n >> 31)

def encode_varint(n: int) -> bytearray:
    bytes_out = bytearray()
    while True:
        to_write = n & 0x7F
        n >>= 7
        if n:
            bytes_out.append(to_write | 0x80)
        else:
            bytes_out.append(to_write)
            break
    return bytes_out

def compute_varint_index_deltas(alphabet, seq):
    result = bytearray()
    last_idx = alphabet.index(seq[0])
    result += encode_varint(last_idx)
    for ch in seq[1:]:
        idx = alphabet.index(ch)
        delta = idx - last_idx
        zz = zigzag_encode(delta)
        result += encode_varint(zz)
        last_idx = idx
    return result

def compute_deltas_bytes(seq):
    deltas = bytearray()
    last = ord(seq[0])
    deltas.append(0)
    for ch in seq[1:]:
        cp = ord(ch)
        delta = cp - last
        if not -128 <= delta <= 127:
            raise ValueError(f"Alphabet delta {delta} out of signed byte range")
        deltas.append(delta & 0xFF)
        last = cp
    return deltas

if __name__ == "__main__":
    alphabet = load_frozen_alphabet("frozen_base4096_alphabet.txt")
    fingerprint = canonical_base4096_fingerprint(alphabet)

    alphabet_deltas_bytes = compute_deltas_bytes(alphabet)
    fingerprint_index_varints = compute_varint_index_deltas(alphabet, fingerprint)

    # --- Self-provisioning JSON with embedded Python ---
    hdgl_json = {
        "metadata": {
            "version": 1,
            "domain": "ZCHG-Base4096-Fingerprint",
            "alphabet_length": len(alphabet),
            "fingerprint_length": len(fingerprint)
        },
        "data": {
            "alphabet_deltas": list(alphabet_deltas_bytes),
            "fingerprint_varints": list(fingerprint_index_varints)
        },
        "provisioner": {
            "python": """\
import json

def zigzag_decode(n):
    return (n >> 1) ^ -(n & 1)

def decode_varint(bytes_list):
    result = 0
    shift = 0
    for b in bytes_list:
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result

# Load this JSON (self) file
with open("base4096_hdgl_selfprovisioning_varint.json", "r", encoding="utf-8") as f:
    hdgl = json.load(f)

# Reconstruct alphabet
alphabet = []
last_cp = 0
for i, delta in enumerate(hdgl["data"]["alphabet_deltas"]):
    if i == 0:
        cp = delta
    else:
        cp = (last_cp + ((delta + 256) % 256))  # signed byte
    alphabet.append(chr(cp))
    last_cp = cp

# Reconstruct fingerprint
fingerprint = []
bytes_iter = iter(hdgl["data"]["fingerprint_varints"])
last_idx = decode_varint([next(bytes_iter) for _ in range(1)])
fingerprint.append(alphabet[last_idx])
while True:
    try:
        # Decode varint
        val_bytes = []
        while True:
            b = next(bytes_iter)
            val_bytes.append(b)
            if not (b & 0x80):
                break
        zz = decode_varint(val_bytes)
        delta = zigzag_decode(zz)
        last_idx += delta
        fingerprint.append(alphabet[last_idx])
    except StopIteration:
        break

print("✅ Alphabet and fingerprint successfully unfolded from self-provisioning JSON")
print("Alphabet length:", len(alphabet))
print("Fingerprint length:", len(fingerprint))
"""
        }
    }

    with open("base4096_hdgl_selfprovisioning_full.json", "w", encoding="utf-8") as f:
        json.dump(hdgl_json, f, ensure_ascii=False, separators=(',', ':'))

    print("✅ Self-provisioning HDGL JSON (full with Python) written to base4096_hdgl_selfprovisioning_full.json")
