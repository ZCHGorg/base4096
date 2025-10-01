import json
from base4096 import load_frozen_alphabet
from base4096_hkdf_seal import canonical_base4096_fingerprint

def compute_deltas(seq):
    """Compute delta encoding for a sequence of characters (codepoints)."""
    deltas = []
    last = ord(seq[0])
    deltas.append(0)
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
    """Fold a delta array into repeated blocks for compactness."""
    blocks = []
    for i in range(0, len(deltas), block_size):
        block = deltas[i:i+block_size]
        blocks.append({"deltas": block, "repeat": 1})
    return blocks

if __name__ == "__main__":
    # Load canonical alphabet
    alphabet = load_frozen_alphabet("frozen_base4096_alphabet.txt")

    # Compute canonical fingerprint
    fingerprint = canonical_base4096_fingerprint(alphabet)

    # Compute delta blocks
    alphabet_blocks = fold_blocks(compute_deltas(alphabet), block_size=64)
    fingerprint_blocks = fold_blocks(compute_index_deltas(alphabet, fingerprint), block_size=32)

    # Construct self-provisioning JSON
    hdgl_json = {
        "metadata": {
            "version": 1,
            "domain": "ZCHG-Base4096-Fingerprint",
            "alphabet_length": len(alphabet),
            "fingerprint_length": len(fingerprint)
        },
        "operations": [
            {
                "type": "alphabet_unfold",
                "base": 32,
                "deltas_blocks": [blk["deltas"] for blk in alphabet_blocks],
                "repeat_blocks": [blk["repeat"] for blk in alphabet_blocks]
            },
            {
                "type": "fingerprint_unfold",
                "alphabet_ref": "alphabet",
                "index_deltas_blocks": [blk["deltas"] for blk in fingerprint_blocks],
                "repeat_blocks": [blk["repeat"] for blk in fingerprint_blocks]
            }
        ],
        # Optional: embed mini-interpreter as HDGL operations
        "interpreter": [
            "alphabet = []",
            "for blk, rpt in zip(operations[0]['deltas_blocks'], operations[0]['repeat_blocks']):",
            "    for _ in range(rpt):",
            "        last = ord(alphabet[-1]) if alphabet else 0",
            "        alphabet.extend([chr(last + d) for d in blk])",
            "",
            "fingerprint = []",
            "last_idx = 0",
            "for blk, rpt in zip(operations[1]['index_deltas_blocks'], operations[1]['repeat_blocks']):",
            "    for _ in range(rpt):",
            "        for d in blk:",
            "            last_idx += d",
            "            fingerprint.append(alphabet[last_idx])"
        ]
    }

    # Write JSON
    with open("base4096_hdgl_selfprovisioning.json", "w", encoding="utf-8") as f:
        json.dump(hdgl_json, f, ensure_ascii=False, indent=2)

    print("✅ Self-provisioning HDGL JSON written to base4096_hdgl_selfprovisioning.json")
