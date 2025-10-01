from base4096 import BASE4096_ALPHABET, encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

# Example provisioner code (self-contained byte sequence)
PROVISIONER_CODE = b'print("Provisioner executed")'

def delta_encode_alphabet(alphabet):
    deltas = []
    last_idx = 0
    for i, c in enumerate(alphabet):
        idx = ord(c)
        delta = idx - last_idx
        deltas.append(delta)
        last_idx = idx
    return deltas

def rle_fold(deltas):
    stream = []
    i = 0
    while i < len(deltas):
        run_val = deltas[i]
        run_len = 1
        while i + run_len < len(deltas) and deltas[i + run_len] == run_val and run_len < 255:
            run_len += 1
        if run_len > 1:
            stream.extend([0xF0, run_len, run_val & 0xFF])
        else:
            stream.append(run_val & 0xFF)
        i += run_len
    return bytes(stream)

# 1. Alphabet folding
alphabet_deltas = delta_encode_alphabet(BASE4096_ALPHABET)
alphabet_stream = rle_fold(alphabet_deltas)

# 2. Fingerprint folding
with open("frozen_base4096_alphabet.txt","r",encoding="utf-8") as f:
    canonical_text = f.read()
fingerprint_str = canonical_base4096_fingerprint(canonical_text)
fingerprint_bytes = bytes([ord(c) & 0xFF for c in fingerprint_str])

# 3. Provisioner folding
provisioner_stream = bytes([0xF2, len(PROVISIONER_CODE)>>8, len(PROVISIONER_CODE)&0xFF]) + PROVISIONER_CODE

# 4. Concatenate all
hdgl_stream = alphabet_stream + fingerprint_bytes + provisioner_stream

# 5. Base4096 encode for output
hdgl_base4096 = encode(hdgl_stream)

# 6. Write
with open("base4096_hdgl_selfunfolding.txt","w",encoding="utf-8") as f:
    f.write(hdgl_base4096)

print("✅ Self-unfolding Base4096 HDGL artifact written to base4096_hdgl_selfunfolding.txt")
