# fold15_selfunfolding.py
# Fully self-unfolding HDGL Base4096 stream

from base4096 import encode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Self-provisioning Python code as string ---
PROVISIONER_CODE = r"""
# Self-provisioning HDGL Python provisioner
from base4096_hkdf_seal import canonical_base4096_fingerprint
from base4096 import BASE4096_ALPHABET

def provision_hdgl():
    print("✅ HDGL environment provisioned!")
    # Further provisioning logic goes here...

if __name__ == "__main__":
    provision_hdgl()
"""

# --- Alphabet + fingerprint ---
alphabet = BASE4096_ALPHABET
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Construct HDGL folding payload ---
hdgl_payload = b"".join([
    b"ALPHABET:", alphabet.encode("utf-8"),
    b"\nFINGERPRINT:", fingerprint.encode("utf-8"),
    b"\nPROVISIONER:", PROVISIONER_CODE.encode("utf-8")
])

# --- Encode entire payload into Base4096 ---
hdgl_stream = encode(hdgl_payload)

# --- Write self-unfolding stream ---
with open("base4096_hdgl_selfunfolding.txt", "w", encoding="utf-8") as f:
    f.write(hdgl_stream)

print("✅ Self-unfolding HDGL Base4096 stream written to base4096_hdgl_selfunfolding.txt")
