# turingfoldtester.py
# Tests unfolding of the self-provisioning HDGL Base4096 stream

from base4096 import decode

# -----------------------------
# Load the Base4096 text
# -----------------------------
with open("base4096_hdgl_selfprovisioning.txt", "r", encoding="utf-8") as f:
    hdgl_text = f.read().strip()

data = decode(hdgl_text)
ptr = 0

# -----------------------------
# Extract sections
# -----------------------------
len_alpha = int.from_bytes(data[ptr:ptr+2], 'big'); ptr += 2
alphabet = data[ptr:ptr+len_alpha].decode("utf-8"); ptr += len_alpha

len_fp = int.from_bytes(data[ptr:ptr+2], 'big'); ptr += 2
fingerprint = data[ptr:ptr+len_fp].decode("utf-8"); ptr += len_fp

len_prov = int.from_bytes(data[ptr:ptr+4], 'big'); ptr += 4
provisioner = data[ptr:ptr+len_prov].decode("utf-8"); ptr += len_prov

len_lattice = int.from_bytes(data[ptr:ptr+4], 'big'); ptr += 4
lattice_bytes = data[ptr:ptr+len_lattice]; ptr += len_lattice

# -----------------------------
# Rebuild lattice floats
# -----------------------------
def bytes_to_float(b):
    return int.from_bytes(b, 'big') / 1e12

LATTICE_SLOTS = []
for i in range(0, len(lattice_bytes), 24):
    d = bytes_to_float(lattice_bytes[i:i+8])
    omega = bytes_to_float(lattice_bytes[i+8:i+16])
    r_dim = bytes_to_float(lattice_bytes[i+16:i+24])
    LATTICE_SLOTS.append((d, omega, r_dim))

# -----------------------------
# Verify & Print
# -----------------------------
print("✅ Unfolded successfully!")
print("Alphabet length:", len(alphabet))
print("Fingerprint:", fingerprint)
print("Provisioner (first 80 chars):", provisioner[:80].replace("\n"," "))
print("Lattice slots decoded:", len(LATTICE_SLOTS))
print("Example slot:", LATTICE_SLOTS[0])
