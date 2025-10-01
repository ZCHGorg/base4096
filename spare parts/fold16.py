# fold16_hdgl_selfunfolding.py
from base4096 import encode, decode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Self-provisioner code ---
PROVISIONER_CODE = r"""
def provision_hdgl():
    print("✅ HDGL provisioned and ready!")
if __name__ == "__main__":
    provision_hdgl()
"""

# --- Alphabet + fingerprint ---
alphabet = BASE4096_ALPHABET
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Fold alphabet into deltas for compact representation ---
char_to_index = {ch: i for i, ch in enumerate(alphabet)}
prev_idx = 0
deltas = []
for ch in alphabet:
    idx = char_to_index[ch]
    deltas.append(idx - prev_idx)
    prev_idx = idx
# Convert deltas to bytes, allow >255 with multi-byte encoding
delta_bytes = b"".join(d.to_bytes(2, "big", signed=True) for d in deltas)

# --- Build payload ---
payload = b"FOLD_ALPHABET:" + delta_bytes + b"\nFINGERPRINT:" + fingerprint.encode("utf-8") + b"\nPROVISIONER:" + PROVISIONER_CODE.encode("utf-8")

# --- Encode entire payload to Base4096 ---
hdgl_stream = encode(payload)

# --- Write self-unfolding artifact ---
with open("base4096_hdgl_selfunfolding_v2.txt", "w", encoding="utf-8") as f:
    f.write(hdgl_stream)

print("✅ Self-unfolding HDGL Base4096 artifact written!")
