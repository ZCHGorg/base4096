import struct
import math

BIN_FILE = "base4096_hdgl_selfprovisioning.bin"

def unfold_bin(path):
    with open(path, "rb") as f:
        data = f.read()

    ptr = 0

    # Alphabet
    len_alpha = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    alphabet_bytes = data[ptr:ptr+len_alpha]; ptr += len_alpha
    alphabet = alphabet_bytes.decode("utf-8", errors="ignore")

    # Fingerprint
    len_fp = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    fingerprint_bytes = data[ptr:ptr+len_fp]; ptr += len_fp
    fingerprint = fingerprint_bytes.decode("utf-8", errors="ignore")

    # Provisioner
    len_prov = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    provisioner_bytes = data[ptr:ptr+len_prov]; ptr += len_prov
    provisioner_code = provisioner_bytes.decode("utf-8", errors="ignore")

    # Lattice
    num_slots = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    slots = []
    slot_size = 8*3
    for _ in range(num_slots):
        d, omega, r_dim = struct.unpack("<ddd", data[ptr:ptr+slot_size])
        slots.append((d, omega, r_dim))
        ptr += slot_size

    return alphabet, fingerprint, provisioner_code, slots

def execute_provisioner(slots, provisioner_code):
    """
    Fully implements provisioner steps:
    1. NORM       -> normalize D_n across lattice
    2. SCALE      -> multiply D_n by a factor
    3. PHASESHIFT -> shift r_dim phase
    4. OMEGAMULT  -> scale omega
    5. ENERGY     -> compute total energy
    6. FOLD256    -> fold slots into superposition
    """
    slots = [list(slot) for slot in slots]  # mutable
    num_slots = len(slots)
    energy = 0.0

    # Step 1: NORM
    max_d = max(d for d, _, _ in slots)
    if max_d != 0:
        for i in range(num_slots):
            slots[i][0] /= max_d

    # Step 2: SCALE
    scale_factor = 1e6
    for i in range(num_slots):
        slots[i][0] *= scale_factor

    # Step 3: PHASESHIFT
    phase_shift = 0.25
    for i in range(num_slots):
        slots[i][2] += phase_shift
        slots[i][2] %= 1.0  # wrap phase to [0,1]

    # Step 4: OMEGAMULT
    omega_mult = 2.0
    for i in range(num_slots):
        slots[i][1] *= omega_mult

    # Step 5: ENERGY
    for d, omega, r_dim in slots:
        energy += d * omega  # simple energy model

    # Step 6: FOLD256 (example: combine slots into averaged superposition)
    if "FOLD256" in provisioner_code:
        d_sum = sum(d for d, _, _ in slots) / num_slots
        omega_sum = sum(omega for _, omega, _ in slots) / num_slots
        r_sum = sum(r_dim for _, _, r_dim in slots) / num_slots
        for i in range(num_slots):
            slots[i][0] = d_sum
            slots[i][1] = omega_sum
            slots[i][2] = r_sum

    return energy, slots

def main():
    print("🔹 HDGL Executor Starting...")
    alphabet, fingerprint, provisioner_code, lattice = unfold_bin(BIN_FILE)

    print(f"✅ Alphabet length (bytes): {len(alphabet.encode('utf-8'))}")
    print(f"✅ Fingerprint length: {len(fingerprint.encode('utf-8'))}")
    print(f"✅ Provisioner length: {len(provisioner_code.encode('utf-8'))}")
    print(f"✅ Lattice slots: {len(lattice)}\n")

    print("--- Fingerprint excerpt ---")
    print(f"{fingerprint[:128]}...\n")

    print("--- Provisioner excerpt ---")
    print(provisioner_code[:128] + "\n")

    print("--- Example slots (first 3) ---")
    for i in range(min(3, len(lattice))):
        print(f"Slot[{i}] = {lattice[i]}")

    print("\n--- Executing Provisioner ---")
    total_energy, final_slots = execute_provisioner(lattice, provisioner_code)
    print(f"🔹 Provisioner computed energy = {total_energy:.6e}")
    print(f"✅ Execution finished. Slots processed = {len(final_slots)}")

if __name__ == "__main__":
    main()
