# fold17_hdgl_fully_selfunfolding.py
from base4096 import encode, decode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Self-provisioner code (minimal example) ---
PROVISIONER_CODE = r"""
def provision_hdgl():
    print("✅ HDGL provisioned and ready!")
if __name__ == "__main__":
    provision_hdgl()
"""

# --- Step 1: Alphabet + fingerprint ---
alphabet = BASE4096_ALPHABET
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Step 2: Fold alphabet into signed deltas ---
char_to_index = {ch: i for i, ch in enumerate(alphabet)}
prev_idx = 0
deltas = []
for ch in alphabet:
    idx = char_to_index[ch]
    delta = idx - prev_idx
    # Allow multi-byte signed representation if >127
    if delta >= 32768 or delta < -32768:
        raise ValueError(f"Delta too large: {delta}")
    deltas.append(delta)
    prev_idx = idx

# Convert deltas to 2-byte signed big-endian
delta_bytes = b"".join(d.to_bytes(2, "big", signed=True) for d in deltas)

# --- Step 3: Construct payload ---
payload = (
    b"HDGL_ALPHABET:" + delta_bytes +
    b"\nHDGL_FINGERPRINT:" + fingerprint.encode("utf-8") +
    b"\nHDGL_PROVISIONER:" + PROVISIONER_CODE.encode("utf-8")
)

# --- Step 4: Encode entire payload to Base4096 ---
hdgl_stream = encode(payload)

# --- Step 5: Write fully self-unfolding HDGL artifact ---
with open("base4096_hdgl_fully_selfunfolding.txt", "w", encoding="utf-8") as f:
    f.write(hdgl_stream)

print("✅ Fully self-unfolding HDGL Base4096 artifact written!")
print("Length (chars):", len(hdgl_stream))
