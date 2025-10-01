import json
from base4096 import CHAR_TO_INDEX, BASE4096_ALPHABET, encode, decode

def fold_alphabet(alphabet, block_size=64):
    folded = []
    prev_idx = 0
    for i in range(0, len(alphabet), block_size):
        block = alphabet[i:i+block_size]
        deltas = [ord(ch) - prev_idx for ch in block]
        folded.append({"delta": deltas, "length": len(block)})
        prev_idx = ord(block[-1])
    return folded

def fold_fingerprint(fp_str, block_size=8):
    folded = []
    prev_idx = 0
    for i in range(0, len(fp_str), block_size):
        block = fp_str[i:i+block_size]
        deltas = [CHAR_TO_INDEX[ch] - prev_idx for ch in block]
        folded.append({"start_index": i, "deltas": deltas, "length": len(block)})
        prev_idx = CHAR_TO_INDEX[block[-1]]
    return folded

if __name__ == "__main__":
    with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
        alphabet_text = f.read().strip()

    fp_bytes = b'\x00'*384  # placeholder: replace with canonical fingerprint bytes
    fp_base4096 = encode(fp_bytes)

    json_data = {
        "version": 1,
        "domain": "ZCHG-Base4096-Fingerprint",
        "length": 4096,
        "hash": "SHA-256",
        "folded_alphabet": fold_alphabet(alphabet_text),
        "folded_fingerprint": fold_fingerprint(fp_base4096)
    }

    with open("base4096_alphabet_hdgl.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print("✅ HDGL-folded JSON written to base4096_alphabet_hdgl.json")
