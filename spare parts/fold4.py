import json
from base4096 import load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

def compute_deltas_bytes(seq):
    """Delta encode Unicode codepoints as signed bytes (still safe for alphabet)."""
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

def compute_index_deltas_2bytes(alphabet, seq):
    """Compute fingerprint index deltas in alphabet as 2-byte signed integers."""
    deltas = bytearray()
    last_idx = alphabet.index(seq[0])
    deltas += last_idx.to_bytes(2, byteorder="big", signed=True)  # first index absolute
    for ch in seq[1:]:
        idx = alphabet.index(ch)
        delta = idx - last_idx
        deltas += delta.to_bytes(2, byteorder="big", signed=True)
        last_idx = idx
    return deltas

if __name__ == "__main__":
    # Load alphabet
    alphabet = load_frozen_alphabet("frozen_base4096_alphabet.txt")

    # Compute fingerprint
    fingerprint = canonical_base4096_fingerprint(alphabet)

    # Delta encode alphabet (still 1-byte deltas)
    alphabet_deltas_bytes = compute_deltas_bytes(alphabet)

    # Delta encode fingerprint indices (2-byte signed deltas)
    fingerprint_index_deltas_bytes = compute_index_deltas_2bytes(alphabet, fingerprint)

    # Self-provisioning HDGL JSON
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
                "index_deltas_2bytes": list(fingerprint_index_deltas_bytes)
            }
        ]
    }

    # Write JSON
    with open("base4096_hdgl_selfprovisioning.json", "w", encoding="utf-8") as f:
        json.dump(hdgl_json, f, ensure_ascii=False, separators=(',', ':'))

    print("✅ Self-provisioning HDGL JSON written to base4096_hdgl_selfprovisioning.json")
