#!/usr/bin/env python3
"""
Production-Ready fold26 Implementation
Delta + RLE compression with full encode/decode + validation
Ready for C porting
"""

import struct
import hashlib
import json
from typing import Tuple, Optional

class Fold26Compressor:
    """
    Production implementation of fold26 algorithm
    Combines delta encoding + run-length encoding
    Fully reversible with validation
    """

    VERSION = "1.0.0"
    MAGIC_HEADER = b'F26\x01'  # File magic for validation

    def __init__(self):
        self.stats = {
            'compressions': 0,
            'decompressions': 0,
            'bytes_in': 0,
            'bytes_out': 0,
            'errors': 0
        }

    def delta_encode(self, data: bytes) -> bytes:
        """
        Stage 1: Delta encoding
        Encodes differences between consecutive bytes
        """
        if len(data) == 0:
            return b''

        # First byte stored as-is
        out = bytearray([data[0]])

        # Encode deltas
        for i in range(1, len(data)):
            delta = (data[i] - data[i-1]) % 256
            out.append(delta)

        return bytes(out)

    def delta_decode(self, data: bytes) -> bytes:
        """
        Stage 1 (reverse): Delta decoding
        Reconstructs original from deltas
        """
        if len(data) == 0:
            return b''

        # First byte stored as-is
        out = bytearray([data[0]])

        # Reconstruct from deltas
        for i in range(1, len(data)):
            value = (out[-1] + data[i]) % 256
            out.append(value)

        return bytes(out)

    def rle_encode(self, data: bytes) -> bytes:
        """
        Stage 2: Run-length encoding
        Format: [value, count] for runs, [value] for singles
        Uses escape sequence for disambiguation
        """
        if len(data) == 0:
            return b''

        out = bytearray()
        i = 0

        while i < len(data):
            value = data[i]
            count = 1

            # Count consecutive identical bytes
            while i + count < len(data) and data[i + count] == value and count < 255:
                count += 1

            if count >= 3:
                # For runs >= 3, use RLE encoding
                # Format: [0xFF] [value] [count]
                out.append(0xFF)  # Escape marker
                out.append(value)
                out.append(count)
            elif count == 2:
                # For pairs, just write twice (cheaper than RLE overhead)
                out.append(value)
                out.append(value)
            else:
                # Single byte
                # If value is 0xFF, escape it
                if value == 0xFF:
                    out.append(0xFF)
                    out.append(0xFF)
                    out.append(0x01)  # Count of 1
                else:
                    out.append(value)

            i += count

        return bytes(out)

    def rle_decode(self, data: bytes) -> bytes:
        """
        Stage 2 (reverse): RLE decoding
        Reconstructs original from RLE format
        """
        if len(data) == 0:
            return b''

        out = bytearray()
        i = 0

        while i < len(data):
            if data[i] == 0xFF:
                # Escape sequence detected
                if i + 2 >= len(data):
                    raise ValueError(f"Truncated RLE escape at position {i}")

                value = data[i + 1]
                count = data[i + 2]

                # Expand run
                out.extend([value] * count)
                i += 3
            else:
                # Regular byte
                out.append(data[i])
                i += 1

        return bytes(out)

    def compress(self, data: bytes, validate: bool = True) -> Tuple[bytes, dict]:
        """
        Full fold26 compression pipeline
        Returns (compressed_data, metadata)
        """
        if len(data) == 0:
            return b'', {'error': 'Empty input'}

        original_size = len(data)
        original_hash = hashlib.sha256(data).digest()

        try:
            # Stage 1: Delta encoding
            delta_encoded = self.delta_encode(data)

            # Stage 2: RLE
            rle_encoded = self.rle_encode(delta_encoded)

            # Build header
            header = self.MAGIC_HEADER
            header += struct.pack('<I', original_size)  # Original size (4 bytes)
            header += original_hash  # SHA-256 hash (32 bytes)

            compressed = header + rle_encoded

            # Validation (optional but recommended)
            if validate:
                decompressed = self.decompress(compressed)[0]
                if decompressed != data:
                    raise ValueError("Validation failed: decompressed != original")

            # Update stats
            self.stats['compressions'] += 1
            self.stats['bytes_in'] += original_size
            self.stats['bytes_out'] += len(compressed)

            # Metadata
            metadata = {
                'original_size': original_size,
                'compressed_size': len(compressed),
                'ratio': original_size / len(compressed) if len(compressed) > 0 else 0,
                'reduction_pct': (1 - len(compressed)/original_size) * 100 if original_size > 0 else 0,
                'original_hash': original_hash.hex(),
                'validated': validate,
                'algorithm': 'fold26',
                'version': self.VERSION
            }

            return compressed, metadata

        except Exception as e:
            self.stats['errors'] += 1
            return b'', {'error': str(e)}

    def decompress(self, data: bytes, validate: bool = True) -> Tuple[bytes, dict]:
        """
        Full fold26 decompression pipeline
        Returns (decompressed_data, metadata)
        """
        if len(data) < 40:  # Minimum: magic(4) + size(4) + hash(32)
            return b'', {'error': 'Data too short for valid fold26 format'}

        try:
            # Parse header
            magic = data[:4]
            if magic != self.MAGIC_HEADER:
                return b'', {'error': f'Invalid magic header: {magic.hex()}'}

            original_size = struct.unpack('<I', data[4:8])[0]
            original_hash = data[8:40]

            # Extract compressed payload
            compressed_payload = data[40:]

            # Stage 2 (reverse): RLE decode
            rle_decoded = self.rle_decode(compressed_payload)

            # Stage 1 (reverse): Delta decode
            decompressed = self.delta_decode(rle_decoded)

            # Validation
            if validate:
                computed_hash = hashlib.sha256(decompressed).digest()
                if computed_hash != original_hash:
                    return b'', {'error': 'Hash mismatch: data corrupted'}

                if len(decompressed) != original_size:
                    return b'', {'error': f'Size mismatch: expected {original_size}, got {len(decompressed)}'}

            # Update stats
            self.stats['decompressions'] += 1

            metadata = {
                'original_size': original_size,
                'compressed_size': len(data),
                'decompressed_size': len(decompressed),
                'original_hash': original_hash.hex(),
                'validated': validate,
                'algorithm': 'fold26',
                'version': self.VERSION
            }

            return decompressed, metadata

        except Exception as e:
            self.stats['errors'] += 1
            return b'', {'error': str(e)}

    def compress_file(self, input_path: str, output_path: Optional[str] = None) -> dict:
        """Compress a file"""
        if output_path is None:
            output_path = input_path + '.f26'

        with open(input_path, 'rb') as f:
            data = f.read()

        compressed, metadata = self.compress(data)

        if 'error' in metadata:
            return metadata

        with open(output_path, 'wb') as f:
            f.write(compressed)

        metadata['input_path'] = input_path
        metadata['output_path'] = output_path

        return metadata

    def decompress_file(self, input_path: str, output_path: Optional[str] = None) -> dict:
        """Decompress a file"""
        if output_path is None:
            if input_path.endswith('.f26'):
                output_path = input_path[:-4]
            else:
                output_path = input_path + '.decompressed'

        with open(input_path, 'rb') as f:
            data = f.read()

        decompressed, metadata = self.decompress(data)

        if 'error' in metadata:
            return metadata

        with open(output_path, 'wb') as f:
            f.write(decompressed)

        metadata['input_path'] = input_path
        metadata['output_path'] = output_path

        return metadata

    def get_stats(self) -> dict:
        """Get compression statistics"""
        stats = self.stats.copy()

        if stats['bytes_in'] > 0:
            stats['overall_ratio'] = stats['bytes_in'] / stats['bytes_out'] if stats['bytes_out'] > 0 else 0
            stats['overall_reduction_pct'] = (1 - stats['bytes_out']/stats['bytes_in']) * 100
        else:
            stats['overall_ratio'] = 0
            stats['overall_reduction_pct'] = 0

        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'compressions': 0,
            'decompressions': 0,
            'bytes_in': 0,
            'bytes_out': 0,
            'errors': 0
        }


def test_fold26():
    """Comprehensive test suite for fold26"""
    print("="*80)
    print("FOLD26 PRODUCTION TEST SUITE")
    print("="*80)

    compressor = Fold26Compressor()

    # Test 1: Empty data
    print("\n📋 Test 1: Empty data")
    result = compressor.compress(b'')
    print(f"   Result: {'✓ PASS' if 'error' in result[1] else '✗ FAIL'}")

    # Test 2: Single byte
    print("\n📋 Test 2: Single byte")
    test_data = b'\x42'
    compressed, meta = compressor.compress(test_data, validate=True)
    if 'error' not in meta:
        decompressed, _ = compressor.decompress(compressed)
        print(f"   Original: 1 byte")
        print(f"   Compressed: {len(compressed)} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        result = '✓ PASS' if decompressed == test_data else '✗ FAIL'
        print(f"   Result: {result}")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Test 3: Repeated bytes (best case for RLE)
    print("\n📋 Test 3: Repeated bytes (100 × 0xAA)")
    data = b'\xAA' * 100
    compressed, meta = compressor.compress(data, validate=True)
    if 'error' not in meta:
        print(f"   Original: {len(data)} bytes")
        print(f"   Compressed: {len(compressed)} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        print(f"   Reduction: {meta['reduction_pct']:.1f}%")
        print(f"   Result: ✓ PASS")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Test 4: Sequential data (best case for delta)
    print("\n📋 Test 4: Sequential data (0-255)")
    data = bytes(range(256))
    compressed, meta = compressor.compress(data, validate=True)
    if 'error' not in meta:
        print(f"   Original: {len(data)} bytes")
        print(f"   Compressed: {len(compressed)} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        print(f"   Reduction: {meta['reduction_pct']:.1f}%")
        print(f"   Result: ✓ PASS")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Test 5: Random data (worst case)
    print("\n📋 Test 5: Random data (1000 bytes)")
    import random
    random.seed(42)
    data = bytes([random.randint(0, 255) for _ in range(1000)])
    compressed, meta = compressor.compress(data, validate=True)
    if 'error' not in meta:
        print(f"   Original: {len(data)} bytes")
        print(f"   Compressed: {len(compressed)} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        print(f"   Reduction: {meta['reduction_pct']:.1f}%")
        print(f"   Result: ✓ PASS")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Test 6: Time-series data (realistic)
    print("\n📋 Test 6: Time-series data (smooth changes)")
    value = 128
    data = bytearray()
    for i in range(1000):
        value = max(0, min(255, value + (i % 7) - 3))
        data.append(value)
    data = bytes(data)
    compressed, meta = compressor.compress(data, validate=True)
    if 'error' not in meta:
        print(f"   Original: {len(data)} bytes")
        print(f"   Compressed: {len(compressed)} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        print(f"   Reduction: {meta['reduction_pct']:.1f}%")
        print(f"   Result: ✓ PASS")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Test 7: Escape byte (0xFF) handling
    print("\n📋 Test 7: Escape byte handling (0xFF)")
    test_data = b'\xFF' * 50 + b'\x00' * 50
    compressed, meta = compressor.compress(test_data, validate=True)
    if 'error' not in meta:
        decompressed, _ = compressor.decompress(compressed)
        print(f"   Original: {len(test_data)} bytes")
        print(f"   Compressed: {len(compressed)} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        result = '✓ PASS' if decompressed == test_data else '✗ FAIL'
        print(f"   Result: {result}")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Test 8: Large data (10 MB)
    print("\n📋 Test 8: Large data (10 MB time-series)")
    import time
    value = 128
    data = bytearray()
    for i in range(10 * 1024 * 1024):
        value = max(0, min(255, value + ((i * 7) % 11) - 5))
        data.append(value)
    data = bytes(data)

    start = time.perf_counter()
    compressed, meta = compressor.compress(data, validate=False)  # Skip validation for speed
    compress_time = time.perf_counter() - start

    if 'error' not in meta:
        start = time.perf_counter()
        decompressed, _ = compressor.decompress(compressed, validate=False)
        decompress_time = time.perf_counter() - start

        print(f"   Original: {len(data):,} bytes")
        print(f"   Compressed: {len(compressed):,} bytes")
        print(f"   Ratio: {meta['ratio']:.2f}×")
        print(f"   Compress time: {compress_time:.3f}s ({len(data)/(1024*1024)/compress_time:.2f} MB/s)")
        print(f"   Decompress time: {decompress_time:.3f}s ({len(data)/(1024*1024)/decompress_time:.2f} MB/s)")
        result = '✓ PASS' if decompressed == data else '✗ FAIL'
        print(f"   Result: {result}")
    else:
        print(f"   Result: ✗ FAIL - {meta['error']}")

    # Statistics
    print("\n" + "="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    stats = compressor.get_stats()
    print(f"Compressions: {stats['compressions']}")
    print(f"Decompressions: {stats['decompressions']}")
    print(f"Bytes in: {stats['bytes_in']:,}")
    print(f"Bytes out: {stats['bytes_out']:,}")
    print(f"Overall ratio: {stats['overall_ratio']:.2f}×")
    print(f"Overall reduction: {stats['overall_reduction_pct']:.1f}%")
    print(f"Errors: {stats['errors']}")

    print("\n✅ FOLD26 PRODUCTION TEST COMPLETE")


if __name__ == "__main__":
    test_fold26()
