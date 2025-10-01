# fold12_hdgl_fully_selfcontained.py
import base64

# Load frozen alphabet
with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
    alphabet_text = f.read().strip().replace("\n","")

from base4096_hkdf_seal import canonical_base4096_fingerprint
fingerprint_text = canonical_base4096_fingerprint(alphabet_text)

# Provisioner code
PROVISIONER_CODE = """
print('✅ HDGL Self-Provisioner Executed')
# You can restore alphabet/fingerprint and run setup here
"""

# --- Embed Base4096 module code ---
with open("base4096.py", "r", encoding="utf-8") as f:
    base4096_code = f.read()

# --- Create byte stream: alphabet + fingerprint + provisioner + base4096 ---
alphabet_bytes = alphabet_text.encode("utf-8")
fingerprint_bytes = fingerprint_text.encode("utf-8")
provisioner_bytes = PROVISIONER_CODE.encode("utf-8")
base4096_bytes = base4096_code.encode("utf-8")

# Layout: [alphabet len(2b)|alphabet][fingerprint len(2b)|fingerprint][provisioner len(4b)|provisioner][base4096 code]
stream = (
    len(alphabet_bytes).to_bytes(2,"big") + alphabet_bytes +
    len(fingerprint_bytes).to_bytes(2,"big") + fingerprint_bytes +
    len(provisioner_bytes).to_bytes(4,"big") + provisioner_bytes +
    base4096_bytes
)

# --- Encode everything as Base4096 ---
from base4096 import encode
hdgl_encoded = encode(stream)

# --- Self-unfolding Python stub ---
UNFOLDER = f"""
import sys
# Base4096 decoder included inline
{base4096_code}

hdgl_encoded = {hdgl_encoded!r}
hdgl_bytes = decode(hdgl_encoded)

# Extract alphabet
a_len = int.from_bytes(hdgl_bytes[:2],'big')
alphabet = hdgl_bytes[2:2+a_len].decode('utf-8')

# Extract fingerprint
f_len = int.from_bytes(hdgl_bytes[2+a_len:4+a_len],'big')
fingerprint = hdgl_bytes[4+a_len:4+a_len+f_len].decode('utf-8')

# Extract provisioner
p_len = int.from_bytes(hdgl_bytes[4+a_len+f_len:8+a_len+f_len],'big')
provisioner = hdgl_bytes[8+a_len+f_len:8+a_len+f_len+p_len].decode('utf-8')

# Execute provisioner
exec(provisioner)
"""

# --- Write fully self-contained HDGL file ---
with open("base4096_hdgl_fully_selfcontained.py","w",encoding="utf-8") as f:
    f.write(UNFOLDER)

print("✅ Fully self-contained HDGL written to base4096_hdgl_fully_selfcontained.py")
