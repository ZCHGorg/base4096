# sign_base4096.py
# Seals the canonical Base-4096 alphabet and emits a versioned .sig4096 file

import hashlib
import hmac
from base4096 import encode

VERSION = b'\x01'
DOMAIN = b'ZCHG-Base4096-Fingerprint'
EXPAND_SIZE = 384  # For 256 Base-4096 characters

def hkdf_expand_sha256(secret: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    blocks = []
    output = b''
    prev = b''
    counter = 1
    while len(output) < length:
        data = prev + info + bytes([counter])
        prev = hmac.new(salt, data, hashlib.sha256).digest()
        output += prev
        counter += 1
    return output[:length]

def canonical_fingerprint(txt: str) -> str:
    flattened = txt.replace("\n", "").encode("utf-8")
    digest = hashlib.sha256(flattened).digest()
    salt = hashlib.sha256(VERSION + DOMAIN).digest()
    expanded = hkdf_expand_sha256(digest, salt, DOMAIN + VERSION, EXPAND_SIZE)
    result = encode(expanded)
    assert len(result) == 256
    return result

def emit_signature_block(fp_text: str, version="1", hash_type="SHA-256", domain="ZCHG-Base4096-Fingerprint") -> str:
    lines = [fp_text[i:i+64] for i in range(0, len(fp_text), 64)]
    return (
        "---BEGIN BASE4096 SIGNATURE---\n"
        f"Version: {version}\n"
        f"Hash: {hash_type}\n"
        f"Domain: {domain}\n"
        f"Length: {len(fp_text)}\n"
        "Alphabet-Fingerprint:\n" +
        "\n".join(lines) +
        "\n---END BASE4096 SIGNATURE---\n"
    )

if __name__ == "__main__":
    with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
        canonical_text = f.read()

    fingerprint = canonical_fingerprint(canonical_text)
    signature_block = emit_signature_block(fingerprint)

    with open("base4096.sig4096", "w", encoding="utf-8") as f:
        f.write(signature_block)

    print("✅ Signature file written to base4096.sig4096")
