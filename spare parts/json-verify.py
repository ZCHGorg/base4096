import json
import base64
from base4096 import encode, decode, load_frozen_alphabet

# Load frozen alphabet
ALPHABET = load_frozen_alphabet("frozen_base4096_alphabet.txt")

def load_json_fingerprint(json_file):
    """Load fingerprint info from any of the three JSON formats."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    alphabet_text = data.get("alphabet")
    fp_info = data.get("fingerprint", {})

    # Try Base4096 first
    fp_base4096 = fp_info.get("base4096")
    if fp_base4096:
        fp_bytes = decode(fp_base4096)
    else:
        # Try Base64 bytes
        fp_b64 = fp_info.get("base64_bytes")
        if fp_b64:
            fp_bytes = base64.b64decode(fp_b64)
            fp_base4096 = encode(fp_bytes)
        else:
            raise ValueError("No recognizable fingerprint found in JSON")

    return alphabet_text, fp_base4096, fp_bytes

def compare_with_sig4096(sig_file, fp_base4096):
    """Compare JSON fingerprint with a .sig4096 file."""
    with open(sig_file, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Extract fingerprint lines from .sig4096
    start = lines.index("Alphabet-Fingerprint:") + 1
    end = lines.index("---END BASE4096 SIGNATURE---")
    sig_fp = "".join(lines[start:end]).strip()

    if sig_fp == fp_base4096:
        print("✅ Fingerprint matches .sig4096 file!")
    else:
        print("❌ Fingerprint does NOT match .sig4096 file!")
        print("JSON fingerprint:", fp_base4096)
        print(".sig4096 fingerprint:", sig_fp)

# --- USAGE EXAMPLES ---

# 1. Load JSON fingerprint
alphabet, fp_base4096, fp_bytes = load_json_fingerprint("base4096_alphabet_signed.json")
print(f"Alphabet length: {len(alphabet)}")
print(f"Fingerprint (Base4096): {fp_base4096}")

# 2. Compare with a sig4096 file (optional)
compare_with_sig4096("base4096.sig4096", fp_base4096)
