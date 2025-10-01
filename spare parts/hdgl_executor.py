# hdgl_executor.py
# Runtime loader + executor + provisioner interpreter for HDGL self-provisioning seed

import struct
import math

# --------------------------
# Unfold helper
# --------------------------
def unfold_bin(path):
    with open(path, "rb") as f:
        data = f.read()
    ptr = 0

    # Alphabet (raw binary, not UTF-8)
    len_alpha = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    alphabet_bytes = data[ptr:ptr+len_alpha]; ptr += len_alpha

    # Fingerprint
    len_fp = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    fingerprint = data[ptr:ptr+len_fp].decode("utf-8", errors="replace"); ptr += len_fp

    # Provisioner
    len_prov = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    provisioner = data[ptr:ptr+len_prov].decode("utf-8", errors="replace"); ptr += len_prov

    # Lattice slots
    num_slots = struct.unpack("<I", data[ptr:ptr+4])[0]; ptr += 4
    lattice = []
    for _ in range(num_slots):
        triple = struct.unpack("<ddd", data[ptr:ptr+24])
        lattice.append(triple)
        ptr += 24

    return alphabet_bytes, fingerprint, provisioner, lattice


# --------------------------
# Provisioner Interpreter
# --------------------------
def run_provisioner(provisioner, lattice):
    """
    Tiny interpreter for provisioner instructions.
    Supported ops (line-based):
        SCALE a        -> scale all amplitudes by a
        PHASESHIFT b   -> add b to all phases
        OMEGAMULT c    -> multiply all omega by c
        NORM           -> normalize amplitudes to max=1
        ENERGY         -> compute & print total energy
    """
    slots = list(lattice)  # copy

    for line in provisioner.splitlines():
        parts = line.strip().split()
        if not parts or parts[0].startswith("#"):
            continue

        cmd = parts[0].upper()
        if cmd == "SCALE" and len(parts) == 2:
            a = float(parts[1])
            slots = [(amp*a, phase, omega) for (amp, phase, omega) in slots]

        elif cmd == "PHASESHIFT" and len(parts) == 2:
            b = float(parts[1])
            slots = [(amp, phase+b, omega) for (amp, phase, omega) in slots]

        elif cmd == "OMEGAMULT" and len(parts) == 2:
            c = float(parts[1])
            slots = [(amp, phase, omega*c) for (amp, phase, omega) in slots]

        elif cmd == "NORM":
            max_amp = max(abs(amp) for (amp, _, _) in slots)
            if max_amp > 0:
                slots = [(amp/max_amp, phase, omega) for (amp, phase, omega) in slots]

        elif cmd == "ENERGY":
            total = sum(amp*omega for (amp, _, omega) in slots)
            print(f"🔹 Provisioner computed energy = {total:.6e}")

        else:
            print(f"⚠️ Unknown provisioner instruction: {line}")

    return slots


# --------------------------
# Executor
# --------------------------
def execute_lattice(alphabet_bytes, fingerprint, provisioner, lattice):
    print("✅ Alphabet length (bytes):", len(alphabet_bytes))
    print("✅ Fingerprint length:", len(fingerprint))
    print("✅ Provisioner length:", len(provisioner))
    print("✅ Lattice slots:", len(lattice))

    print("\n--- Fingerprint excerpt ---")
    print(fingerprint[:120] + ("..." if len(fingerprint) > 120 else ""))

    print("\n--- Provisioner excerpt ---")
    for line in provisioner.splitlines()[:5]:
        print(line)

    print("\n--- Example slots (first 3) ---")
    for i in range(3):
        print(f"Slot[{i}] = {lattice[i]}")

    # Run provisioner
    print("\n--- Executing Provisioner ---")
    updated_slots = run_provisioner(provisioner, lattice)

    # Final energy check
    total_energy = sum(amp*omega for (amp, _, omega) in updated_slots)
    print(f"✅ Final total energy after provisioner = {total_energy:.6e}")

    return updated_slots


# --------------------------
# Main entry
# --------------------------
if __name__ == "__main__":
    print("🔹 HDGL Executor Starting...")

    alphabet_bytes, fingerprint, provisioner, lattice = unfold_bin("base4096_hdgl_selfprovisioning.bin")
    updated = execute_lattice(alphabet_bytes, fingerprint, provisioner, lattice)

    print("\n✅ Execution finished. Slots processed =", len(updated))
