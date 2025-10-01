import json
from base4096 import encode, load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Helper Functions ---
def fold_bytes_to_base4096(data: bytes) -> str:
    """Encode raw bytes into Base4096 string."""
    return encode(data)

def encode_alphabet_deltas(alphabet: str) -> str:
    """Compute delta bytes and fold to Base4096."""
    deltas = bytearray()
    last_cp = ord(alphabet[0])
    deltas.append(last_cp & 0xFF)
    for ch in alphabet[1:]:
        delta = ord(ch) - last_cp
        deltas.append(delta & 0xFF)
        last_cp = ord(ch)
    return fold_bytes_to_base4096(deltas)

def encode_fingerprint_varints(alphabet: str, fingerprint: str) -> str:
    """Compute varint indices and fold to Base4096."""
    result = bytearray()
    last_idx = alphabet.index(fingerprint[0])
    result.append(last_idx & 0xFF)
    for ch in fingerprint[1:]:
        idx = alphabet.index(ch)
        delta = idx - last_idx
        # Zigzag encoding
        zz = (delta << 1) ^ (delta >> 31)
        # simple 7-bit varint
        while True:
            byte = zz & 0x7F
            zz >>= 7
            if zz:
                result.append(byte | 0x80)
            else:
                result.append(byte)
                break
        last_idx = idx
    return fold_bytes_to_base4096(result)

# --- Embedded Provisioner ---
python_code = """
# Self-provisioner embedded directly
from base4096_hkdf_seal import canonical_base4096_fingerprint
from base4096 import load_frozen_alphabet

alphabet = load_frozen_alphabet()
fingerprint = canonical_base4096_fingerprint(alphabet)

print("Provisioner ready. Alphabet length:", len(alphabet))
"""

def encode_python_provisioner(provisioner_code: str) -> str:
    return fold_bytes_to_base4096(provisioner_code.encode("utf-8"))

# --- Main Execution ---
if __name__ == "__main__":
    alphabet = load_frozen_alphabet("frozen_base4096_alphabet.txt")
    fingerprint = canonical_base4096_fingerprint(alphabet)

    alphabet_b4096 = encode_alphabet_deltas(alphabet)
    fingerprint_b4096 = encode_fingerprint_varints(alphabet, fingerprint)
    provisioner_b4096 = encode_python_provisioner(python_code)

    hdgl_b4096_json = {
        "metadata": {
            "version": 1,
            "domain": "ZCHG-Base4096-Fingerprint",
            "alphabet_length": len(alphabet),
            "fingerprint_length": len(fingerprint)
        },
        "data": {
            "alphabet": alphabet_b4096,
            "fingerprint": fingerprint_b4096,
            "provisioner": provisioner_b4096
        }
    }

    with open("base4096_hdgl_selfcontained.json", "w", encoding="utf-8") as f:
        json.dump(hdgl_b4096_json, f, ensure_ascii=False, separators=(',', ':'))

    print("✅ Fully Base4096 HDGL JSON written to base4096_hdgl_selfcontained.json")
