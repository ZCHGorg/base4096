import json
from base4096 import decode, load_frozen_alphabet

# --- Helper Functions ---
def unfold_base4096_to_bytes(b4096_str: str) -> bytes:
    """Decode Base4096 string back into bytes."""
    return decode(b4096_str)

def unfold_alphabet(deltas_b: bytes) -> str:
    """Restore alphabet from delta bytes."""
    alphabet = [deltas_b[0]]
    for delta in deltas_b[1:]:
        alphabet.append((alphabet[-1] + delta) & 0xFF)
    return ''.join(chr(b) for b in alphabet)

def unfold_python_provisioner(prov_b: bytes) -> str:
    """Decode provisioner bytes into Python source code string."""
    return prov_b.decode("utf-8")

# --- Main Execution ---
if __name__ == "__main__":
    with open("base4096_hdgl_selfcontained.json", "r", encoding="utf-8") as f:
        hdgl_json = json.load(f)

    alphabet_b4096 = hdgl_json["data"]["alphabet"]
    fingerprint_b4096 = hdgl_json["data"]["fingerprint"]
    provisioner_b4096 = hdgl_json["data"]["provisioner"]

    alphabet_bytes = unfold_base4096_to_bytes(alphabet_b4096)
    provisioner_bytes = unfold_base4096_to_bytes(provisioner_b4096)

    # Restore Python source
    python_code = unfold_python_provisioner(provisioner_bytes)

    # Execute provisioner
    exec(python_code)

    print("✅ HDGL JSON successfully unfolded and provisioner executed.")
