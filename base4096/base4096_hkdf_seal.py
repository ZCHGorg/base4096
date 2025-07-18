# base4096_hkdf_seal.py
# Canonical Base-4096 256-character fingerprint sealer with HKDF and embedded metadata

import hashlib
import hmac
from base4096 import encode  # Uses frozen alphabet + encode(bytes) -> str

# --- CONFIGURATION ---
VERSION = b'\x01'                     # Version 1
DOMAIN = b'ZCHG-Base4096-Fingerprint'  # Purpose binding
EXPAND_SIZE = 384                     # 384 bytes = 3072 bits = 256 base4096 chars

def hkdf_expand_sha256(secret: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    """
    Implements HKDF-Expand (RFC 5869) using SHA-256
    """
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

def canonical_base4096_fingerprint(canonical_text: str) -> str:
    """
    Generates a 256-character Base-4096 fingerprint from a frozen alphabet source
    using versioned metadata + secure HKDF-based expansion.
    """
    flattened = canonical_text.replace("\n", "").encode("utf-8")
    
    # Primary digest of the source
    digest = hashlib.sha256(flattened).digest()
    
    # Salt = H(version + DOMAIN)
    salt = hashlib.sha256(VERSION + DOMAIN).digest()

    # Expand digest into 384 bytes using HKDF with purpose/domain binding
    expanded = hkdf_expand_sha256(secret=digest, salt=salt, info=DOMAIN + VERSION, length=EXPAND_SIZE)

    # Base-4096 encode
    fingerprint = encode(expanded)
    assert len(fingerprint) == 256
    return fingerprint

# --- EXECUTION ---
if __name__ == "__main__":
    with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
        canonical_text = f.read()

    fingerprint = canonical_base4096_fingerprint(canonical_text)
    print("🔐 Canonical Base-4096 Fingerprint (256 chars):\n")
    print(fingerprint)
