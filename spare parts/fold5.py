import json
from base4096 import load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

def zigzag_encode(n: int) -> int:
    """Zigzag encoding maps signed integers to unsigned for varint."""
    return (n << 1) ^ (n >> 31)

def encode_varint(n: int) -> bytearray:
    """Encode integer as LEB128-style variable-length bytes."""
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
    """Compute fingerprint index deltas as zigzag-varint encoded bytes."""
    result = bytearray()
    last_idx = alphabet.index(seq[0])
    # store first index as absolute varint
    result += encode_varint(last_idx)
    for ch in seq[1:]:
        idx = alphabet.index(ch)
        delta = idx - last_idx
        zz = zigzag_encode(delta)
        result += encode_varint(zz)
        last_idx = idx
    return result

def compute_deltas_bytes(seq):
    """Alphabet codepoint deltas (1-byte safe)."""
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

    hdgl_json = {
        "metadata": {
            "version": 1,
            "domain": "ZCHG-Base4096-Fingerprint",
            "alphabet_length": len(alphabet),
            "fingerprint_length": len(fingerprint)
        },
        "operations": [
            {
                "type": "alphabet_unfold",
                "deltas_bytes": list(alphabet_deltas_bytes)
            },
            {
                "type": "fingerprint_unfold",
                "alphabet_ref": "alphabet",
                "index_varints": list(fingerprint_index_varints)
            }
        ]
    }

    with open("base4096_hdgl_selfprovisioning_varint.json", "w", encoding="utf-8") as f:
        json.dump(hdgl_json, f, ensure_ascii=False, separators=(',', ':'))

    print("✅ Self-provisioning HDGL JSON (varint) written to base4096_hdgl_selfprovisioning_varint.json")
