with open("frozen_base4096_alphabet.txt", "r", encoding="utf-8") as f:
    alphabet = f.read()

print("Total length:", len(alphabet))
print("Unique chars:", len(set(alphabet)))
print("First 100:", alphabet[:100])
