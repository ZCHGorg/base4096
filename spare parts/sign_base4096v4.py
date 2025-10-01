# sign_base4096v4.py
import hashlib
import hmac
import json
import base64
import argparse
from pathlib import Path
from base4096 import encode  # assumes frozen alphabet

VERSION = b'\x01'
DOMAIN = b'ZCHG-Base4096-Fingerprint'
EXPAND_SIZE = 384  # bytes = 3072 bits = 256 Base4096 chars

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

def fingerprint_bytes(data: bytes) -> (str, bytes):
    """Compute SHA-256 + HKDF expanded fingerprint"""
    digest = hashlib.sha256(data).digest()
    salt = hashlib.sha256(VERSION + DOMAIN).digest()
    expanded = hkdf_expand_sha256(digest, salt, DOMAIN + VERSION, EXPAND_SIZE)
    fp_base4096 = encode(expanded)
    return fp_base4096, expanded

def process_layer(file_path: Path):
    """Read a file and return content bytes + Base4096 + Base64 fingerprints"""
    content_bytes = file_path.read_bytes()
    fp_base4096, fp_bytes = fingerprint_bytes(content_bytes)
    return {
        "filename": file_path.name,
        "content_bytes": content_bytes,
        "base4096": fp_base4096,
        "base64_bytes": base64.b64encode(fp_bytes).decode("ascii"),
        "expanded_length": EXPAND_SIZE,
        "hash": "SHA-256"
    }

def build_ultracompact_json(layers: list, output_file: Path):
    """Assemble final JSON with per-layer and top-level fingerprints"""
    json_layers = {}
    layer_fingerprints = {}
    
    for layer in layers:
        # Encode text/binary content as appropriate
        try:
            text_content = layer["content_bytes"].decode("utf-8")
            json_layers[layer["filename"]] = text_content
        except UnicodeDecodeError:
            json_layers[layer["filename"]] = base64.b64encode(layer["content_bytes"]).decode("ascii")
        
        layer_fingerprints[layer["filename"]] = {
            "base4096": layer["base4096"],
            "base64_bytes": layer["base64_bytes"],
            "expanded_length": layer["expanded_length"],
            "hash": layer["hash"]
        }

    # Compute top-level fingerprint over concatenated layer bytes
    concatenated = b"".join(layer["content_bytes"] for layer in layers)
    top_base4096, top_bytes = fingerprint_bytes(concatenated)
    
    data = {
        "version": 1,
        "domain": DOMAIN.decode("utf-8"),
        "layers": json_layers,
        "layer_fingerprints": layer_fingerprints,
        "fingerprint": {
            "base4096": top_base4096,
            "base64_bytes": base64.b64encode(top_bytes).decode("ascii"),
            "expanded_length": EXPAND_SIZE,
            "hash": "SHA-256"
        }
    }

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Ultracompact JSON written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Sign multiple HDGL/Base4096 files into a single JSON")
    parser.add_argument("files", nargs="+", type=Path, help="Files to include as layers")
    parser.add_argument("-o", "--output", type=Path, default=Path("hdgl_layers_signed.json"), help="Output JSON file")
    args = parser.parse_args()

    layers = [process_layer(fp) for fp in args.files]
    build_ultracompact_json(layers, args.output)

if __name__ == "__main__":
    main()
