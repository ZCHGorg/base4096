from base4096 import encode, decode, BASE4096_ALPHABET
from base4096_hkdf_seal import canonical_base4096_fingerprint

# --- Layer 2: Provisioner + fingerprint ---
PROVISIONER_CODE = r'''
def provision_hdgl():
    print("✅ HDGL provisioned from nested layer with folding operators!")
if __name__=="__main__":
    provision_hdgl()
'''

alphabet = BASE4096_ALPHABET
fingerprint = canonical_base4096_fingerprint(alphabet)

# --- Delta encode alphabet ---
char_to_index = {ch: i for i,ch in enumerate(alphabet)}
prev_idx = 0
deltas = []
for ch in alphabet:
    idx = char_to_index[ch]
    delta = idx - prev_idx
    # HDGL compression: if delta > 127, split into multiple bytes with 0xF0 marker
    while delta > 127:
        deltas.append(0xF0)  # "extend delta" operator
        delta -= 127
    deltas.append(delta & 0xFF)
    prev_idx = idx

delta_bytes = bytes(deltas)

# --- Payload: alphabet deltas + fingerprint + provisioner ---
layer2_payload = b'ALPHABET:' + delta_bytes + \
                 b'\nFINGERPRINT:' + fingerprint.encode('utf-8') + \
                 b'\nPROVISIONER:' + PROVISIONER_CODE.encode('utf-8')

layer2_b4096 = encode(layer2_payload)

# --- Layer 1: HDGL VM embeds layer 2 ---
HDGL_VM = f'''
import sys
from base4096 import decode

def run_hdgl_layer2(stream_b4096: str):
    payload_bytes = decode(stream_b4096)
    # parse ALPHABET deltas
    sections = payload_bytes.split(b'\\nFINGERPRINT:')
    delta_bytes = sections[0].split(b'ALPHABET:')[1]
    chars = []
    prev = 0
    i = 0
    while i < len(delta_bytes):
        b = delta_bytes[i]
        if b == 0xF0:
            # extend operator
            i += 1
            b2 = delta_bytes[i]
            delta = 127 + b2
        else:
            delta = b
        idx = prev + delta
        chars.append(chr(idx))
        prev = idx
        i += 1
    reconstructed_alphabet = ''.join(chars)
    fingerprint = sections[1].split(b'\\nPROVISIONER:')[0].decode()
    provisioner = sections[1].split(b'\\nPROVISIONER:')[1].decode()
    from base4096_hkdf_seal import canonical_base4096_fingerprint
    if canonical_base4096_fingerprint(reconstructed_alphabet) != fingerprint:
        raise ValueError("Fingerprint mismatch!")
    exec(provisioner)

if __name__=="__main__":
    run_hdgl_layer2("{layer2_b4096}")
'''

# Layer 1 Base4096
layer1_b4096 = encode(HDGL_VM.encode('utf-8'))

# --- Layer 0: Outer Python bootstrap ---
with open("base4096_hdgl_folded.py",'w',encoding='utf-8') as f:
    f.write(f'''
from base4096 import decode
layer1_b4096 = "{layer1_b4096}"
exec(decode(layer1_b4096).decode('utf-8'))
''')

print("✅ HDGL multi-layer with folding operators written!")
