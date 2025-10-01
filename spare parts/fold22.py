# fold22_selfprovisioning.py
# Fully self-contained HDGL VM generator with embedded alphabet, fingerprint, and provisioner

import os
from base4096 import encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- 1️⃣ Load frozen Base4096 alphabet ---
try:
    with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
        alphabet = f.read().strip().replace("\n", "").replace("\r", "")
except FileNotFoundError:
    raise RuntimeError("Frozen alphabet not found. Please provide frozen_base4096_alphabet.txt")

if len(alphabet) != 4096 or len(set(alphabet)) != 4096:
    raise ValueError("Alphabet must have exactly 4096 unique characters.")

# --- 2️⃣ Compute canonical fingerprint ---
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- 3️⃣ Embed full HDGL provisioner logic ---
PROVISIONER_CODE = """
# HDGL Provisioner Instructions
# 1. Load Base4096 alphabet
LOAD_ALPHABET
# 2. Load canonical fingerprint
LOAD_FINGERPRINT
# 3. Initialize VM environment
INIT_VM
# 4. Map alphabet -> memory
MAP_ALPHABET
# 5. Map fingerprint -> memory
MAP_FINGERPRINT
# 6. Execute provisioner logic
EXEC_PROVISIONER
# 7. Ready for unfolding HDGL program
READY
"""

# --- 4️⃣ Encode components in Base4096 ---
alphabet_b4096 = encode(alphabet.encode("utf-8"))
fingerprint_b4096 = encode(fingerprint.encode("utf-8"))
provisioner_b4096 = encode(PROVISIONER_CODE.encode("utf-8"))

# --- 5️⃣ Compose self-unfolding HDGL stream ---
hdgl_stream = (
    f"⟪HEADER⟫Version:1"
    f"⟪ALPHABET⟫{alphabet_b4096}"
    f"⟪FINGERPRINT⟫{fingerprint_b4096}"
    f"⟪PROVISIONER⟫{provisioner_b4096}"
    f"⟪UNFOLD⟫ALPHABET->MEMORY,FINGERPRINT->MEMORY,PROVISIONER->EXEC"
)

# --- 6️⃣ Output single self-contained file ---
output_file = "base4096_hdgl_vm_selfprovisioning.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(hdgl_stream)

print(f"✅ Fully self-provisioning HDGL VM written to {output_file}")
print(f"Stream length: {len(hdgl_stream)} Base4096 characters")
