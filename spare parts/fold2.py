import json
from base4096 import load_frozen_alphabet, encode
from base4096_hkdf_seal import canonical_base4096_fingerprint

def compute_deltas(seq):
    """Compute delta encoding for a sequence of characters (codepoints)."""
    deltas = []
    last = ord(seq[0])
    deltas.append(0)  # first delta relative to itself
    for ch in seq[1:]:
        cp = ord(ch)
        deltas.append(cp - last)
        last = cp
    return deltas

def compute_index_deltas(alphabet, seq):
    """Compute deltas of indices in alphabet."""
    deltas = []
    last_idx = alphabet.index(seq[0])
    deltas.append(0)
    for ch in seq[1:]:
        idx = alphabet.index(ch)
        deltas.append(idx - last_idx)
        last_idx = idx
    return deltas

def fold_blocks(deltas, block_size=32):
    """Fold a long delta array into repeated blocks for compactness."""
    blocks = []
    for i in range(0, len(deltas), block_size):
        block = deltas[i:i+block_size]
        blocks.append({"deltas": block, "repeat": 1})
    return blocks

if __name__ == "__main__":
    # Load canonical alphabet
    alphabet = load_frozen_alphabet("frozen_base4096_alphabet.txt")

    # Compute Base4096 canonical fingerprint
    fingerprint = canonical_base4096_fingerprint(alphabet)

    # Delta-encode alphabet and fingerprint
    alphabet_deltas = compute_deltas(alphabet)
    fingerprint_deltas = compute_index_deltas(alphabet, fingerprint)

    # Fold into blocks
    alphabet_blocks = fold_blocks(alphabet_deltas, block_size=64)
    fingerprint_blocks = fold_blocks(fingerprint_deltas, block_size=32)

    # Construct JSON
    hdgl_json = {
        "metadata": {
            "version": 1,
            "domain": "ZCHG-Base4096-Fingerprint",
            "alphabet_length": len(alphabet),
            "fingerprint_length": len(fingerprint)
        },
        "alphabet": alphabet_blocks,
        "fingerprint": fingerprint_blocks
    }

    # Write JSON
    with open("base4096_hdgl.json", "w", encoding="utf-8") as f:
        json.dump(hdgl_json, f, ensure_ascii=False, indent=2)

    print("✅ HDGL JSON written to base4096_hdgl.json")
