# fold9.py — Self-bootstrapping HDGL JSON generator
import json
from base4096 import encode, load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Configuration ---
ALPHABET_FILE = "frozen_base4096_alphabet.txt"
OUTPUT_JSON = "base4096_hdgl_selfbootstrap.json"

# Load frozen alphabet
alphabet_text = load_frozen_alphabet(ALPHABET_FILE)

# --- Embed the provisioner code directly as a string ---
PROVISIONER_CODE = """
print('✅ HDGL Self-Provisioner Executed')
# Add your full provisioner logic here
"""

# Base4096 encode everything
alphabet_b4096 = encode(alphabet_text.encode("utf-8"))
provisioner_b4096 = encode(PROVISIONER_CODE.encode("utf-8"))
fingerprint_b4096 = canonical_base4096_fingerprint(alphabet_text)

# Minimal unfolder embedded in JSON
unfolder_code = (
    "import json, sys; from base4096 import decode;"
    "hdgl=json.load(open(sys.argv[0]));"
    "exec(decode(hdgl['data']['provisioner']).decode('utf-8'))"
)

# Construct JSON
hdgl_selfbootstrap = {
    "version": "1",
    "data": {
        "alphabet": alphabet_b4096,
        "fingerprint": fingerprint_b4096,
        "provisioner": provisioner_b4096
    },
    "unfolder": unfolder_code
}

# Write JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(hdgl_selfbootstrap, f, ensure_ascii=False, indent=2)

print(f"✅ Self-bootstrapping HDGL JSON written to {OUTPUT_JSON}")
print("▶ Run with: python base4096_hdgl_selfbootstrap.json")
