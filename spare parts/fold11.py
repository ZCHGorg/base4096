# fold10_metisa.py — Self-provisioning HDGL JSON (full + ultra-compact Metisa64)
import json
from base4096 import encode, load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint
import base64

# --- Configuration ---
ALPHABET_FILE = "frozen_base4096_alphabet.txt"
FULL_JSON = "base4096_hdgl_selfbootstrap.json"
COMPACT_JSON = "base4096_hdgl_selfbootstrap_metisa.json"

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
    "import json, sys, base64; from base4096 import decode;"
    "hdgl=json.load(open(sys.argv[0]));"
    "exec(decode(hdgl['data']['provisioner']).decode('utf-8'))"
)

# --- Full JSON (Unicode Base4096) ---
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

# --- Compact JSON (Metisa64 / base64 bytes) ---
hdgl_compact = {
    "version": "1",
    "data": {
        "alphabet_bytes": base64.b85encode(alphabet_text.encode("utf-8")).decode("ascii"),
        "fingerprint_bytes": base64.b85encode(fingerprint_b4096.encode("utf-8")).decode("ascii"),
        "provisioner_bytes": base64.b85encode(PROVISIONER_CODE.encode("utf-8")).decode("ascii")
    },
    "unfolder": (
        "import json, sys, base64;"
        "hdgl=json.load(open(sys.argv[0]));"
        "exec(base64.b85decode(hdgl['data']['provisioner_bytes']).decode('utf-8'))"
    )
}

with open(COMPACT_JSON, "w", encoding="utf-8") as f:
    json.dump(hdgl_compact, f, ensure_ascii=False, indent=2)
print(f"✅ Compact Metisa64 HDGL JSON written to {COMPACT_JSON}")
