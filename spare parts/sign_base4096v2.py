# sign_base4096V3.py
import hashlib
import hmac
import json
import base64
from base4096 import encode  # uses frozen alphabet + encode(bytes) -> str

VERSION = b'\x01'
DOMAIN = b'ZCHG-Base4096-Fingerprint'
EXPAND_SIZE = 384  # bytes = 3072 bits = 256 base4096 chars

def hkdf_expand_sha256(secret: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    """HKDF-Expand (RFC 5869) using SHA-256"""
    output = b''
    prev = b''
    counter = 1
    while len(output) < length:
        data = prev + info + bytes([counter])
        prev = hmac.new(salt, data, hashlib.sha256).digest()
        output += prev
        counter += 1
    return output[:length]

def canonical_fingerprint(canonical_text: str):
    """Return both Base4096 string fingerprint and raw bytes"""
    flattened = canonical_text.replace("\n", "").encode("utf-8")
    digest = hashlib.sha256(flattened).digest()
    salt = hashlib.sha256(VERSION + DOMAIN).digest()
    expanded = hkdf_expand_sha256(digest, salt, DOMAIN + VERSION, EXPAND_SIZE)
    fp_base4096 = encode(expanded)
    assert len(fp_base4096) == 256
    return fp_base4096, expanded

def write_signed_json(alphabet_text, fingerprint_base4096, filename="base4096_alphabet_signed.json"):
    data = {
        "version": 1,
        "domain": DOMAIN.decode("utf-8"),
        "length": len(alphabet_text),
        "alphabet": list(alphabet_text),
        "fingerprint": {
            "hash": "SHA-256",
            "expanded_length": EXPAND_SIZE,
            "base4096_signature": fingerprint_base4096
        }
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Signed JSON written to {filename}")

def write_compact_json(alphabet_text, fingerprint_bytes, filename="base4096_alphabet_compact.json"):
    fingerprint_b64 = base64.b64encode(fingerprint_bytes).decode("ascii")
    data = {
        "version": 1,
        "domain": DOMAIN.decode("utf-8"),
        "length": len(alphabet_text),
        "alphabet": list(alphabet_text),
        "fingerprint": {
            "hash": "SHA-256",
            "expanded_length": EXPAND_SIZE,
            "fingerprint_bytes_b64": fingerprint_b64
        }
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Compact JSON written to {filename}")

def write_ultracompact_json(alphabet_text, fp_base4096, fp_bytes, filename="base4096_alphabet_ultracompact.json"):
    fp_b64 = base64.b64encode(fp_bytes).decode("ascii")
    data = {
        "version": 1,
        "domain": DOMAIN.decode("utf-8"),
        "length": len(alphabet_text),
        "alphabet": alphabet_text,  # single string
        "fingerprint": {
            "base4096": fp_base4096,
            "base64_bytes": fp_b64,
            "expanded_length": EXPAND_SIZE,
            "hash": "SHA-256"
        }
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Ultra-compact JSON written to {filename}")

if __name__ == "__main__":
    with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
        canonical_text = f.read().strip()

    fp_base4096, fp_bytes = canonical_fingerprint(canonical_text)

    # Existing two JSONs
    write_signed_json(canonical_text, fp_base4096)
    write_compact_json(canonical_text, fp_bytes)

    # Third ultra-compact JSON
    write_ultracompact_json(canonical_text, fp_base4096, fp_bytes)
