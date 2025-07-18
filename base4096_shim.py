# base4096_shim.py

import sys
# Remap this shim module to appear as 'base4096' in sys.modules
sys.modules['base4096'] = sys.modules[__name__]

# Import all relevant items from actual files
from base4096 import encode, decode
from frozen_base4096_alphabet import BASE4096_ALPHABET, CHAR_TO_INDEX

__version__ = '2.0'
