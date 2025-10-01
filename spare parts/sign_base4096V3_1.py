# sign_base4096V3_1.py
import hashlib
import hmac
import json
import base64
from base4096 import encode  # frozen alphabet; encode(bytes) -> str

VERSION = b'\x01'
DOMAIN = b'ZCHG-Base4096-Fingerprint'
EXPAND_SIZE = 384  # bytes = 3072 bits = 256 base4096 chars

# --- HKDF-Expand (RFC 5869) ---
def hkdf_expand_sha256(secret: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    output = b''
    prev = b''
    counter = 1
    while len(output) < length:
        data = prev + info + bytes([counter])
        prev = hmac.new(salt, data, hashlib.sha256).digest()
        output += prev
        counter += 1
    return output[:length]

# --- Compute canonical fingerprint ---
def canonical_fingerprint(*layers: bytes):
    """Flatten layers deterministically, hash, HKDF-expand, encode."""
    concatenated = b''.join(layers)
    digest = hashlib.sha256(concatenated).digest()
    salt = hashlib.sha256(VERSION + DOMAIN).digest()
    expanded = hkdf_expand_sha256(digest, salt, DOMAIN + VERSION, EXPAND_SIZE)
    fp_base4096 = encode(expanded)
    return fp_base4096, expanded

# --- Compute per-layer fingerprints ---
def layer_fingerprint(data: bytes):
    digest = hashlib.sha256(data).digest()
    salt = hashlib.sha256(VERSION + DOMAIN).digest()
    expanded = hkdf_expand_sha256(digest, salt, DOMAIN + VERSION, EXPAND_SIZE)
    return {
        "base4096": encode(expanded),
        "base64_bytes": base64.b64encode(expanded).decode("ascii"),
        "expanded_length": EXPAND_SIZE,
        "hash": "SHA-256"
    }

# --- Load file as bytes ---
def load_file_bytes(filename: str) -> bytes:
    with open(filename, "rb") as f:
        return f.read()

# --- Write ultracompact JSON ---
def write_ultracompact_json(layers_dict, per_layer_fps, fp_base4096, fp_bytes,
                            filename="base4096_hdgl_all_layers.json"):
    fp_b64 = base64.b64encode(fp_bytes).decode("ascii")
    data = {
        "version": 1,
        "domain": DOMAIN.decode("utf-8"),
        "layers": layers_dict,
        "layer_fingerprints": per_layer_fps,
        "fingerprint": {
            "base4096": fp_base4096,
            "base64_bytes": fp_b64,
            "expanded_length": EXPAND_SIZE,
            "hash": "SHA-256"
        }
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Unified ultracompact JSON written to {filename}")

# --- Main ---
if __name__ == "__main__":
    # Load canonical files
    txt_bytes = load_file_bytes("base4096_hdgl_selfprovisioning.txt")
    bin_bytes = load_file_bytes("base4096_hdgl_selfprovisioning.bin")
    lattice_bytes = load_file_bytes("base4096_hdgl_selfhosting_lattice.b4096")

    # Construct layers dict for JSON
    layers_dict = {
        "txt": txt_bytes.decode("utf-8"),
        "bin_b64": base64.b64encode(bin_bytes).decode("ascii"),
        "lattice_b4096": lattice_bytes.decode("utf-8")
    }

    # Compute per-layer fingerprints
    per_layer_fps = {
        "txt": layer_fingerprint(txt_bytes),
        "bin": layer_fingerprint(bin_bytes),
        "lattice": layer_fingerprint(lattice_bytes)
    }

    # Compute top-level fingerprint over all layers concatenated
    fp_base4096, fp_bytes = canonical_fingerprint(txt_bytes, bin_bytes, lattice_bytes)

    # Write ultracompact JSON
    write_ultracompact_json(layers_dict, per_layer_fps, fp_base4096, fp_bytes)
