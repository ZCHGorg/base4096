COPYRIGHT NOTICE:  https://zchg.org/t/legal-notice-copyright-applicable-ip-and-licensing-read-me/440

# 🔐 Base-4096 Encoder/Decoder — ZCHG.org

Author: Josef Kulovany  
Project: Canonical Base-4096 Encoding Toolkit  
Signature: `base4096.sig4096` (see below)  
License: https://zchg.org/t/legal-notice-copyright-applicable-ip-and-licensing-read-me/440
  
Version: 2.0.0  

---

## 📦 Overview

This toolkit defines a **canonical Base-4096 encoding system** using a deterministically frozen Unicode alphabet, capable of encoding binary data into a compact, printable, and internationalized character stream.

It includes:

- ✅ Alphabet generation from a curated Unicode seed
- ✅ Frozen 4096-character canonical alphabet
- ✅ Deterministic encoder/decoder with fixed lookup table
- ✅ Cryptographic fingerprint and `.sig4096` signature file
- ✅ Ready for integration in compression, obfuscation, or identity verification systems

---

## 📘 Components

### `base4096.py`

- Provides `encode(data: bytes) -> str` and `decode(text: str) -> bytes`
- Loads frozen alphabet from `frozen_base4096_alphabet.txt` or regenerates from seed if missing
- Uses a 4096-character deterministic alphabet for compact encoding (≈12 bits per char)

### `freeze_base4096_alphabet.py`

- Generates and **freezes** the Base-4096 alphabet from a curated Unicode seed
- Writes:
  - `frozen_base4096_alphabet.txt` (raw flat file)
  - `frozen_base4096_alphabet.py` (importable Python constant)

Run this **once** to lock the alphabet.

#### 'frozen_base4096_alphabet.py'

- This was yielded by running 'freeze_base_4096_alphabet.py' and explicitly contains the complete base4096 alphabet.


#### 'base4096_hkdf_seal.py' (optional)

- Inputs: any input (e.g. the frozen Base-4096 alphabet)

- Hashes: with SHA-256 (or BLAKE3 optional)

- Expands: into 384 bytes (3072 bits) using HMAC-based HKDF expansion

- Encodes: to exactly 256 Base-4096 characters

- Metadata included: version marker, domain binding, input digest

- UNWRAPPED

### `sign_base4096.py`

- Canonicalizes and cryptographically seals the frozen alphabet
- Uses:
  - SHA-256 → HKDF-SHA256 → 384-byte entropy blob
  - Base-4096 encode of blob → **256-character fingerprint**
- Produces:  
  `base4096.sig4096` (signed metadata block)

✅ A canonical Base-4096 alphabet

✅ A 256-character cryptographic fingerprint

✅ A versioned, metadata-bound, HMAC-derived expansion

✅ And now: a signed wrapper using that fingerprint as both the seal and the payload for verification.

---

## 🧬 Signature (Canonical Fingerprint) 'base4096.sig4096'

```text
---BEGIN BASE4096 SIGNATURE---
Version: 1
Hash: SHA-256
Domain: ZCHG-Base4096-Fingerprint
Length: 256
Alphabet-Fingerprint:
ˉۀଉתֲߊͪᅬMოൢЏ࿂ב৩Čཤᅏʽ෦ʵ႗ჸྛAྻၻဣᅶఙ൱eሠႩrڽøԖിՃႅᄚࡑᅹิॄࠩǡǠ๒ᅝሯ؍Ʌ͛ȑถౘ੨Ӧࢤ๖ϧŜ
แ࣍́ȥሰۇUઐሱܵဵҕಽðӦ˫ԁପୈႶఃઉॾ໓ܐണพڽ࢞ߴЍÊྨ༼ࡣ๑گˠয়ຢԃഡଏĔॅ໐ᄴࡖ֮ಙÎۦׯʹԤ٢ྯƞعਙѾٺచሡ
ݵ}۴ǲฦďࣔஉ૽ૢʔ੭yജ२ᆙၧљӗມᆧખથᅇࠂඅ௹ʫtමჺાѸሡྥᄱࠛࡌϕց෯໙Нܕࢀřݜմ๊ऐʩٕܟ़ࡵǋࠧڰࣿໍαा၏൴
࿑ɽ̚ঙӀ࡛¨ၨҩৗཙر൫൦༝ᆡӀǮΊô¦Ɖࡑ୦ලৌ၍ਚၤ༨ԾඤभუႤթе࠺ӉǦ͙ᄙવȡݛࡶɩวţ่ஒי̯ɭଏѝलઢরˠעճౌ૭
---END BASE4096 SIGNATURE---
