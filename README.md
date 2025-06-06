The era of AI demands stronger security and explicit clarity. Previously, our extended alphabet was only implied from the seed alphabet, which is no longer sufficient in today’s environment. We have now made the extended alphabet an explicit, canonical definition, ensuring deterministic and reproducible encoding.

Additionally, we have introduced cryptographic signing of the canonical alphabet using our own Base-4096 encoding layered (or “shelled”) over SHA-256. This enhancement provides tamper-evident guarantees and fosters both backward and forward compatibility.

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

### 'frozen_base4096_alphabet.py'

- This was yielded by running 'freeze_base_4096_alphabet.py' and explicitly contains the complete base4096 alphabet.

### 'base4096_hkdf_seal.py' (optional)

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

**Full Changelog**: https://github.com/ZCHGorg/base4096/compare/base4096...v2.0.0

# OLD Base4096 V1.0

A Base4096 algorithm is a specific type of Base4096 algorithm that uses a base of 4096. It represents numeric values using a set of 4096 characters, which can include the upper and lower case letters, the digits 0-9, and various special characters.

Base4096 algorithms are useful for a number of different purposes, including:

Data compression: Base4096 algorithms can be used to compress large numbers into shorter strings, which can be more convenient to store or transmit.

Data encoding: Base4096 algorithms can be used to encode data in a way that makes it more difficult to read or understand. This can be useful for data security or privacy purposes.

Data transmission: Base4096 algorithms can be used to transmit data over networks or through other communication channels more efficiently, by encoding the data in a more compact form.

Data storage: Base4096 algorithms can be used to store data more efficiently, by using fewer characters to represent the same data.

Base4096 algorithms can be used to encode and compress data that is stored on a blockchain, allowing for more efficient storage and faster transaction times. The compact size of the encoded data can also help to reduce the overall size of the blockchain, which can be beneficial for decentralization and security purposes.



<B>USE OR INSTALLATION:</B>

To use the `base4096` package, you can import it into your Python project. To do so, follow the steps below:

**Install from PyPI:**

**Install Dependencies:**
   - **Copy and Paste into terminal**
     Open a terminal and run the following command to install Base4096 and its dependencies:
     ```bash
     pip install base4096
     ```

Then you can use :

- **Copy and Paste into terminal**
     ```bash
     import base4096
     ```

Otherwise, to run the script, you will need to have a Python interpreter installed on your system. You can then run the script by using the following command:

python base4096.py
This will execute the script and run the functions defined in it.

If you want to pass arguments to the script, you can do so by providing them after the script name. For example, to pass the integer 123 to the encode() function in the script, you could use the following command:

python base4096.py 123
This would call the encode() function with the argument 123, and the function would return the encoded string.

You may also wish to simply copy and paste the code directly into your own script.  Be sure to show attribution per the licensing requirements, please!

<b>Examples:</b>

For example, if you have defined the following functions in your base4096 module:

def encode(number):
    # Encode a number as base4096
    pass

def decode(encoded):
    # Decode a base4096 encoded number
    pass

You can use these functions in your code like this:

result = base4096.encode(12345)
decoded = base4096.decode(result)



<B>HOW IT WORKS</B>

The script takes an integer as input and returns a string as output. The decode() function takes a string as input and returns an integer as output.

The encode() function works by first initializing an empty string called encoded. It then enters a loop that continues as long as number is greater than 0. In each iteration of the loop, the function adds the character at the index number % 4096 in the alphabet string to the beginning of encoded and then updates number to be number // 4096. The loop terminates when number becomes 0.

The decode() function works by initializing a variable called decoded to 0. It then iterates over each character c in the input string encoded, starting from the end and working backwards. For each character c, it adds the value of alphabet.index(c) * 4096**i to decoded, where i is the index of the character in the reversed string.

<B>PREMISE:</B>

In general, storing characters in a string or a file will have a much lower impact on computer performance compared to generating characters on the fly. Generating characters on the fly can be a computationally expensive operation, especially if the characters are being generated randomly or based on some complex algorithm.

Storing characters in a string or a file simply involves allocating memory to hold the characters and writing the characters to the memory or file. This is a relatively fast and simple operation that has a minimal impact on computer performance.

On the other hand, generating characters on the fly typically involves executing some kind of computation or algorithm to produce the characters. This can be a much more resource-intensive operation, as it requires the computer to perform additional calculations and possibly access external resources.

In general, it is more efficient to store characters in a string or file rather than generating them on the fly, as this can help to reduce the overall computational load on the computer and improve performance.

With the advent of AI being brought to the fore, the need for stored memory for a given character set will naturally increase at a much higher rate than anticipated.

Written by Josef Kulovany - ZCHG.org
