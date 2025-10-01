# fold10.py — Self-provisioning HDGL JSON (full + compact)
import json
from base4096 import encode, load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Configuration ---
ALPHABET_FILE = "frozen_base4096_alphabet.txt"
FULL_JSON = "base4096_hdgl_selfbootstrap.json"
COMPACT_JSON = "base4096_hdgl_selfbootstrap_compact.json"

# Load frozen alphabet
alphabet_text = load_frozen_alphabet(ALPHABET_FILE)

# --- Embed provisioner code ---
PROVISIONER_CODE = """
print('✅ HDGL Self-Provisioner Executed')
# Add your full provisioner logic here
"""

# Base4096 encode
alphabet_b4096 = encode(alphabet_text.encode("utf-8"))
provisioner_b4096 = encode(PROVISIONER_CODE.encode("utf-8"))
fingerprint_b4096 = canonical_base4096_fingerprint(alphabet_text)

# --- Minimal unfolder ---
unfolder_code = (
    "import json, sys; from base4096 import decode;"
    "hdgl=json.load(open(sys.argv[0]));"
    "exec(decode(hdgl['data']['provisioner']).decode('utf-8'))"
)

# --- Full JSON ---
hdgl_full = {
    "version": "1",
    "data": {
        "alphabet": alphabet_b4096,
        "fingerprint": fingerprint_b4096,
        "provisioner": provisioner_b4096
    },
    "unfolder": unfolder_code
}

with open(FULL_JSON, "w", encoding="utf-8") as f:
    json.dump(hdgl_full, f, ensure_ascii=False, indent=2)
print(f"✅ Full HDGL JSON written to {FULL_JSON}")

# --- Compact JSON (bytes instead of Unicode) ---
hdgl_compact = {
    "version": "1",
    "data": {
        "alphabet_bytes": alphabet_text.encode("utf-8").hex(),
        "fingerprint_bytes": canonical_base4096_fingerprint(alphabet_text).encode("utf-8").hex(),
        "provisioner_bytes": PROVISIONER_CODE.encode("utf-8").hex()
    },
    "unfolder": (
        "import json, sys;"
        "hdgl=json.load(open(sys.argv[0]));"
        "exec(bytes.fromhex(hdgl['data']['provisioner_bytes']).decode('utf-8'))"
    )
}

with open(COMPACT_JSON, "w", encoding="utf-8") as f:
    json.dump(hdgl_compact, f, ensure_ascii=False, indent=2)
print(f"✅ Compact HDGL JSON written to {COMPACT_JSON}")
