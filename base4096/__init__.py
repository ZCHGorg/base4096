import sys
import os

# Allow import from repo root even if not in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from base4096 import encode, decode
from frozen_base4096_alphabet import BASE4096_ALPHABET, CHAR_TO_INDEX

__version__ = '2.0'
