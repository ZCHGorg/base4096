# verify_base4096v4.py
import hashlib
import hmac
import json
import base64
from pathlib import Path
from base4096 import encode  # same frozen alphabet as signing

VERSION = b'\x01'
DOMAIN = b'ZCHG-Base4096-Fingerprint'
EXPAND_SIZE = 384

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

def fingerprint_bytes(data: bytes):
    digest = hashlib.sha256(data).digest()
    salt = hashlib.sha256(VERSION + DOMAIN).digest()
    expanded = hkdf_expand_sha256(digest, salt, DOMAIN + VERSION, EXPAND_SIZE)
    fp_base4096 = encode(expanded)
    return fp_base4096, expanded

def verify_layer(name: str, content_bytes: bytes, fp_data: dict) -> bool:
    fp_base4096, fp_bytes = fingerprint_bytes(content_bytes)
    fp_b64 = base64.b64encode(fp_bytes).decode("ascii")

    match_base4096 = fp_base4096 == fp_data["base4096"]
    match_b64 = fp_b64 == fp_data["base64_bytes"]

    if not match_base4096 or not match_b64:
        print(f"❌ Layer '{name}' mismatch:")
        if not match_base4096:
            print(f"   Base4096: expected {fp_data['base4096']} got {fp_base4096}")
        if not match_b64:
            print(f"   Base64 bytes: expected {fp_data['base64_bytes']} got {fp_b64}")
        return False
    print(f"✅ Layer '{name}' verified")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify ultracompact HDGL/Base4096 JSON")
    parser.add_argument("json_file", type=Path, help="Ultracompact JSON file to verify")
    args = parser.parse_args()

    data = json.loads(args.json_file.read_text(encoding="utf-8"))

    layers = data["layers"]
    layer_fps = data["layer_fingerprints"]

    all_ok = True
    # Verify each layer
    for name, content in layers.items():
        try:
            content_bytes = content.encode("utf-8")
        except Exception:
            # Assume base64-encoded binary
            content_bytes = base64.b64decode(content)
        ok = verify_layer(name, content_bytes, layer_fps[name])
        all_ok &= ok

    # Verify top-level fingerprint
    concatenated = b"".join(
        content.encode("utf-8") if isinstance(content, str) else base64.b64decode(content)
        for content in layers.values()
    )
    top_fp_base4096, top_fp_bytes = fingerprint_bytes(concatenated)
    top_b64 = base64.b64encode(top_fp_bytes).decode("ascii")

    top_fp_data = data["fingerprint"]
    match_base4096 = top_fp_base4096 == top_fp_data["base4096"]
    match_b64 = top_b64 == top_fp_data["base64_bytes"]

    if match_base4096 and match_b64:
        print("✅ Top-level fingerprint verified")
    else:
        print("❌ Top-level fingerprint mismatch!")
        print(f"   Base4096: expected {top_fp_data['base4096']} got {top_fp_base4096}")
        print(f"   Base64 bytes: expected {top_fp_data['base64_bytes']} got {top_b64}")
        all_ok = False

    if all_ok:
        print("\n🎉 All layers and top-level fingerprint verified successfully!")
    else:
        print("\n⚠️ Verification failed for one or more layers/fingerprints.")

if __name__ == "__main__":
    main()
