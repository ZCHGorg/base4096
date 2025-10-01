# fold18_hdgl_selfunfolding.py
from base4096 import encode, decode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Minimal HDGL interpreter embedded in artifact ---
HDGL_VM_STUB = r'''
import sys
from base4096 import decode

def run_hdgl_stream(stream_b4096: str):
    payload_bytes = decode(stream_b4096)
    sections = payload_bytes.split(b'\nHDGL_')
    data = {}
    for sec in sections:
        if b':' in sec:
            key, val = sec.split(b':', 1)
            data[key.decode()] = val
    # Verify fingerprint
    alphabet_bytes = data.get('ALPHABET')
    fingerprint = data.get('FINGERPRINT').decode()
    provisioner = data.get('PROVISIONER').decode()
    # Reconstruct alphabet
    delta_pairs = [int.from_bytes(alphabet_bytes[i:i+2],'big',signed=True)
                   for i in range(0,len(alphabet_bytes),2)]
    chars = []
    prev = 0
    for d in delta_pairs:
        idx = prev + d
        chars.append(chr(idx))
        prev = idx
    reconstructed_alphabet = ''.join(chars)
    # Verify fingerprint matches
    from base4096_hkdf_seal import canonical_base4096_fingerprint
    if canonical_base4096_fingerprint(reconstructed_alphabet) != fingerprint:
        raise ValueError("Fingerprint mismatch! HDGL stream corrupted.")
    # Execute provisioner
    exec(provisioner)

if __name__=="__main__":
    # The embedded Base4096 HDGL stream is appended at the end of this file
    with open(__file__,'r',encoding='utf-8') as f:
        content = f.read()
    # Find marker
    marker = '#---HDGL_STREAM_START---\n'
    hdgl_b4096 = content.split(marker)[1]
    run_hdgl_stream(hdgl_b4096.strip())
'''

# --- Step 1: Alphabet + fingerprint + provisioner ---
alphabet = BASE4096_ALPHABET
fingerprint = canonical_base4096_fingerprint(alphabet)
PROVISIONER_CODE = r'''
def provision_hdgl():
    print("✅ HDGL provisioned and fully self-executing!")
if __name__=="__main__":
    provision_hdgl()
'''

# --- Step 2: Alphabet as 2-byte signed deltas ---
char_to_index = {ch: i for i,ch in enumerate(alphabet)}
prev_idx = 0
deltas = []
for ch in alphabet:
    idx = char_to_index[ch]
    delta = idx - prev_idx
    deltas.append(delta)
    prev_idx = idx
delta_bytes = b''.join(d.to_bytes(2,'big',signed=True) for d in deltas)

# --- Step 3: Construct payload ---
payload = (
    b'ALPHABET:' + delta_bytes +
    b'\nFINGERPRINT:' + fingerprint.encode('utf-8') +
    b'\nPROVISIONER:' + PROVISIONER_CODE.encode('utf-8')
)

# --- Step 4: Encode payload to Base4096 ---
hdgl_stream = encode(payload)

# --- Step 5: Write self-executing artifact ---
with open("base4096_hdgl_selfunfolding.py",'w',encoding='utf-8') as f:
    f.write(HDGL_VM_STUB)
    f.write('\n#---HDGL_STREAM_START---\n')
    f.write(hdgl_stream)

print("✅ Fully self-unfolding, self-provisioning HDGL artifact written!")
print("Length (chars):", len(hdgl_stream))
