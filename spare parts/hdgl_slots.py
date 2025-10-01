# hdgl_slots.py
# Provides 256 HDGL lattice slots for folding
# Falls back if SGRA not available

try:
    from gra_cra_full_framework import build_periodic_table
    import math

    def get_hdgl_slots():
        slots = []
        table = build_periodic_table()
        for idx, elem in enumerate(table[:256]):
            d = float(getattr(elem, "radius", (idx+1)*1e-6))
            omega = float(getattr(elem, "omega", 8.12e-9))
            r_dim = float(getattr(elem, "dimension", 0.3))
            slots.append((d, omega, r_dim))
        return slots

except ImportError:
    # Deterministic fallback
    def get_hdgl_slots():
        slots = []
        for i in range(32):
            for j in range(8):
                d = (i+1)*(j+1)*1e-6
                omega = 8.12e-9
                r_dim = 0.3
                slots.append((d, omega, r_dim))
        return slots
