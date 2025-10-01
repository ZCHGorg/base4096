from base4096 import encode, decode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Layer 2: Provisioner + fingerprint ---
PROVISIONER_CODE = r'''
def provision_hdgl():
    print("✅ HDGL provisioned from nested layer!")
if __name__=="__main__":
    provision_hdgl()
'''

alphabet = BASE4096_ALPHABET
fingerprint = canonical_base4096_fingerprint(alphabet)

# Encode alphabet as 2-byte signed deltas
char_to_index = {ch: i for i,ch in enumerate(alphabet)}
prev_idx = 0
deltas = []
for ch in alphabet:
    idx = char_to_index[ch]
    deltas.append(idx - prev_idx)
    prev_idx = idx
delta_bytes = b''.join(d.to_bytes(2,'big',signed=True) for d in deltas)

# Payload = alphabet deltas + fingerprint + provisioner
layer2_payload = b'ALPHABET:' + delta_bytes + \
                 b'\nFINGERPRINT:' + fingerprint.encode('utf-8') + \
                 b'\nPROVISIONER:' + PROVISIONER_CODE.encode('utf-8')

layer2_b4096 = encode(layer2_payload)

# --- Layer 1: HDGL VM as Base4096 string, embeds Layer 2 ---
HDGL_VM = f'''
import sys
from base4096 import decode

def run_hdgl_layer2(stream_b4096: str):
    payload_bytes = decode(stream_b4096)
    sections = payload_bytes.split(b'\\nFINGERPRINT:')
    alphabet_bytes = sections[0].split(b'ALPHABET:')[1]
    fingerprint = sections[1].split(b'\\nPROVISIONER:')[0].decode()
    provisioner = sections[1].split(b'\\nPROVISIONER:')[1].decode()
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
    from base4096_hkdf_seal import canonical_base4096_fingerprint
    if canonical_base4096_fingerprint(reconstructed_alphabet) != fingerprint:
        raise ValueError("Fingerprint mismatch!")
    # Execute provisioner
    exec(provisioner)

if __name__=="__main__":
    run_hdgl_layer2("{layer2_b4096}")
'''

# --- Layer 1 Base4096 encoding ---
layer1_b4096 = encode(HDGL_VM.encode('utf-8'))

# --- Layer 0: Outer Python bootstrap ---
with open("base4096_hdgl_multilayer.py",'w',encoding='utf-8') as f:
    f.write(f'''
from base4096 import decode
layer1_b4096 = "{layer1_b4096}"
exec(decode(layer1_b4096).decode('utf-8'))
''')

print("✅ Multi-layer self-unfolding HDGL artifact written!")
