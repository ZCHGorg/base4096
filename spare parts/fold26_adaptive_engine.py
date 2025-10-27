#!/usr/bin/env python3
"""
Adaptive Compression Engine - Test 9
Self-optimizing multi-pass compression combining all algorithms
Analyzes data characteristics and selects optimal compression strategy
"""

import struct
import hashlib
import math
from collections import Counter
from typing import Tuple, List, Dict, Optional
import time

class DataAnalyzer:
    """Analyzes data to determine optimal compression strategy"""

    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        """Shannon entropy in bits per byte"""
        if len(data) == 0:
            return 0.0
        freq = Counter(data)
        total = len(data)
        entropy = 0.0
        for count in freq.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def analyze_temporal_correlation(data: bytes, sample_size: int = 1000) -> float:
        """Measure temporal correlation (0=none, 1=perfect)"""
        if len(data) < 2:
            return 0.0

        # Sample if data is large
        if len(data) > sample_size:
            step = len(data) // sample_size
            samples = [data[i] for i in range(0, len(data), step)][:sample_size]
        else:
            samples = list(data)

        # Calculate correlation with deltas
        deltas = [abs(samples[i] - samples[i-1]) for i in range(1, len(samples))]
        avg_delta = sum(deltas) / len(deltas) if deltas else 0

        # Normalized correlation score (lower delta = higher correlation)
        correlation = 1.0 - min(avg_delta / 128.0, 1.0)
        return correlation

    @staticmethod
    def analyze_repetition(data: bytes, sample_size: int = 1000) -> float:
        """Measure repetition factor (0=none, 1=all same)"""
        if len(data) == 0:
            return 0.0

        # Sample if data is large
        if len(data) > sample_size:
            step = len(data) // sample_size
            samples = bytes([data[i] for i in range(0, len(data), step)][:sample_size])
        else:
            samples = data

        # Find longest runs
        max_run = 1
        current_run = 1
        for i in range(1, len(samples)):
            if samples[i] == samples[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1

        # Normalized repetition score
        repetition = min(max_run / 10.0, 1.0)
        return repetition

    @staticmethod
    def analyze_structure(data: bytes) -> Dict[str, float]:
        """Complete data structure analysis"""
        return {
            'entropy': DataAnalyzer.calculate_entropy(data),
            'correlation': DataAnalyzer.analyze_temporal_correlation(data),
            'repetition': DataAnalyzer.analyze_repetition(data),
            'size': len(data),
            'unique_bytes': len(set(data)),
            'compressibility': 1.0 - (DataAnalyzer.calculate_entropy(data) / 8.0)
        }


class CompressionStrategy:
    """Determines optimal compression strategy based on data analysis"""

    STRATEGIES = {
        'high_entropy': {
            'name': 'High Entropy (Random)',
            'passes': [],  # No compression recommended
            'expected_ratio': 1.0,
            'threshold': {'entropy': 7.0}
        },
        'high_correlation': {
            'name': 'High Temporal Correlation',
            'passes': ['delta', 'rle', 'delta', 'rle'],  # 2-pass recursive
            'expected_ratio': 4.0,
            'threshold': {'correlation': 0.7}
        },
        'high_repetition': {
            'name': 'High Repetition',
            'passes': ['rle', 'delta', 'rle'],  # RLE-focused
            'expected_ratio': 5.0,
            'threshold': {'repetition': 0.6}
        },
        'structured': {
            'name': 'Structured Data',
            'passes': ['delta', 'rle', 'delta'],  # Standard fold26+
            'expected_ratio': 3.0,
            'threshold': {'compressibility': 0.4}
        },
        'mixed': {
            'name': 'Mixed Characteristics',
            'passes': ['delta', 'rle'],  # Standard fold26
            'expected_ratio': 2.0,
            'threshold': {}
        }
    }

    @staticmethod
    def select_strategy(analysis: Dict[str, float]) -> Dict:
        """Select best compression strategy based on analysis"""

        # High entropy = don't compress
        if analysis['entropy'] >= 7.0:
            return CompressionStrategy.STRATEGIES['high_entropy']

        # High correlation = multi-pass delta+RLE
        if analysis['correlation'] >= 0.7:
            return CompressionStrategy.STRATEGIES['high_correlation']

        # High repetition = RLE-focused
        if analysis['repetition'] >= 0.6:
            return CompressionStrategy.STRATEGIES['high_repetition']

        # Decent compressibility = structured approach
        if analysis['compressibility'] >= 0.4:
            return CompressionStrategy.STRATEGIES['structured']

        # Default = standard fold26
        return CompressionStrategy.STRATEGIES['mixed']


class AdaptiveCompressionEngine:
    """
    Self-optimizing compression engine
    Combines delta, RLE, and recursive folding with intelligent pass selection
    """

    VERSION = "2.0.0"
    MAGIC_HEADER = b'ACE\x02'  # Adaptive Compression Engine v2

    def __init__(self):
        self.stats = {
            'total_compressions': 0,
            'total_decompressions': 0,
            'bytes_in': 0,
            'bytes_out': 0,
            'analysis_time': 0.0,
            'compression_time': 0.0,
            'decompression_time': 0.0
        }

    def delta_encode(self, data: bytes) -> bytes:
        """Delta encoding pass"""
        if len(data) == 0:
            return b''
        out = bytearray([data[0]])
        for i in range(1, len(data)):
            delta = (data[i] - data[i-1]) % 256
            out.append(delta)
        return bytes(out)

    def delta_decode(self, data: bytes) -> bytes:
        """Delta decoding pass"""
        if len(data) == 0:
            return b''
        out = bytearray([data[0]])
        for i in range(1, len(data)):
            value = (out[-1] + data[i]) % 256
            out.append(value)
        return bytes(out)

    def rle_encode(self, data: bytes) -> bytes:
        """RLE encoding pass"""
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
                # RLE encoding: [0xFF] [value] [count]
                out.append(0xFF)
                out.append(value)
                out.append(count)
            elif count == 2:
                # Write pairs directly
                out.append(value)
                out.append(value)
            else:
                # Single byte (escape 0xFF)
                if value == 0xFF:
                    out.append(0xFF)
                    out.append(0xFF)
                    out.append(0x01)
                else:
                    out.append(value)

            i += count

        return bytes(out)

    def rle_decode(self, data: bytes) -> bytes:
        """RLE decoding pass"""
        if len(data) == 0:
            return b''

        out = bytearray()
        i = 0

        while i < len(data):
            if data[i] == 0xFF:
                if i + 2 >= len(data):
                    raise ValueError(f"Truncated RLE escape at position {i}")
                value = data[i + 1]
                count = data[i + 2]
                out.extend([value] * count)
                i += 3
            else:
                out.append(data[i])
                i += 1

        return bytes(out)

    def apply_pass(self, data: bytes, pass_name: str) -> bytes:
        """Apply a single compression pass"""
        if pass_name == 'delta':
            return self.delta_encode(data)
        elif pass_name == 'rle':
            return self.rle_encode(data)
        else:
            raise ValueError(f"Unknown pass: {pass_name}")

    def reverse_pass(self, data: bytes, pass_name: str) -> bytes:
        """Reverse a single compression pass"""
        if pass_name == 'delta':
            return self.delta_decode(data)
        elif pass_name == 'rle':
            return self.rle_decode(data)
        else:
            raise ValueError(f"Unknown pass: {pass_name}")

    def compress_with_strategy(self, data: bytes, strategy: Dict) -> Tuple[bytes, List[str]]:
        """Apply compression strategy passes with optimization"""
        passes = strategy['passes']

        if not passes:
            # No compression recommended
            return data, []

        current = data
        applied_passes = []
        sizes = [len(data)]  # Track sizes through pipeline

        for pass_name in passes:
            before_size = len(current)
            try:
                transformed = self.apply_pass(current, pass_name)
                after_size = len(transformed)

                # Keep pass if it compressed OR if we're building a pipeline
                # (later passes might compress this pass's output)
                if after_size <= before_size or len(applied_passes) < len(passes) - 1:
                    current = transformed
                    applied_passes.append(pass_name)
                    sizes.append(after_size)
                else:
                    # Last pass didn't help, skip it
                    sizes.append(before_size)
            except Exception as e:
                # Pass failed, continue without it
                sizes.append(before_size)
                continue

        # If final size is larger, use original data
        if len(current) >= len(data):
            return data, []

        return current, applied_passes

    def compress(self, data: bytes, adaptive: bool = True) -> Tuple[bytes, Dict]:
        """
        Adaptive compression with intelligent pass selection
        """
        if len(data) == 0:
            return b'', {'error': 'Empty input'}

        start_time = time.perf_counter()
        original_size = len(data)
        original_hash = hashlib.sha256(data).digest()

        try:
            # Step 1: Analyze data
            analysis_start = time.perf_counter()
            analysis = DataAnalyzer.analyze_structure(data)
            analysis_time = time.perf_counter() - analysis_start

            # Step 2: Select strategy
            if adaptive:
                strategy = CompressionStrategy.select_strategy(analysis)
            else:
                # Default to standard fold26
                strategy = CompressionStrategy.STRATEGIES['mixed']

            # Step 3: Apply compression
            compress_start = time.perf_counter()
            compressed, applied_passes = self.compress_with_strategy(data, strategy)
            compression_time = time.perf_counter() - compress_start

            # Step 4: Build header
            header = self.MAGIC_HEADER
            header += struct.pack('<I', original_size)  # Original size
            header += original_hash  # SHA-256 hash
            header += struct.pack('<B', len(applied_passes))  # Number of passes

            # Encode pass sequence
            pass_encoding = {'delta': 0x01, 'rle': 0x02}
            for pass_name in applied_passes:
                header += struct.pack('<B', pass_encoding.get(pass_name, 0x00))

            output = header + compressed

            total_time = time.perf_counter() - start_time

            # Update stats
            self.stats['total_compressions'] += 1
            self.stats['bytes_in'] += original_size
            self.stats['bytes_out'] += len(output)
            self.stats['analysis_time'] += analysis_time
            self.stats['compression_time'] += compression_time

            # Metadata
            metadata = {
                'original_size': original_size,
                'compressed_size': len(output),
                'ratio': original_size / len(output) if len(output) > 0 else 0,
                'reduction_pct': (1 - len(output)/original_size) * 100 if original_size > 0 else 0,
                'strategy': strategy['name'],
                'passes_attempted': len(strategy['passes']),
                'passes_applied': len(applied_passes),
                'pass_sequence': applied_passes,
                'analysis': analysis,
                'analysis_time_ms': analysis_time * 1000,
                'compression_time_ms': compression_time * 1000,
                'total_time_ms': total_time * 1000,
                'throughput_mbps': (original_size / (1024*1024)) / compression_time if compression_time > 0 else 0,
                'algorithm': 'ACE',
                'version': self.VERSION
            }

            return output, metadata

        except Exception as e:
            return b'', {'error': str(e)}

    def decompress(self, data: bytes) -> Tuple[bytes, Dict]:
        """Decompress ACE format with pass recovery"""
        if len(data) < 41:  # Minimum header size
            return b'', {'error': 'Data too short for valid ACE format'}

        start_time = time.perf_counter()

        try:
            # Parse header
            magic = data[:4]
            if magic != self.MAGIC_HEADER:
                return b'', {'error': f'Invalid magic header: {magic.hex()}'}

            original_size = struct.unpack('<I', data[4:8])[0]
            original_hash = data[8:40]
            num_passes = struct.unpack('<B', data[40:41])[0]

            # Decode pass sequence
            pass_decoding = {0x01: 'delta', 0x02: 'rle'}
            passes = []
            offset = 41
            for i in range(num_passes):
                if offset >= len(data):
                    return b'', {'error': 'Truncated pass sequence'}
                pass_code = struct.unpack('<B', data[offset:offset+1])[0]
                passes.append(pass_decoding.get(pass_code, 'unknown'))
                offset += 1

            # Extract compressed payload
            compressed_payload = data[offset:]

            # Apply decompression in reverse order
            current = compressed_payload
            for pass_name in reversed(passes):
                current = self.reverse_pass(current, pass_name)

            # Validate
            computed_hash = hashlib.sha256(current).digest()
            if computed_hash != original_hash:
                return b'', {'error': 'Hash mismatch: data corrupted'}

            if len(current) != original_size:
                return b'', {'error': f'Size mismatch: expected {original_size}, got {len(current)}'}

            total_time = time.perf_counter() - start_time

            # Update stats
            self.stats['total_decompressions'] += 1
            self.stats['decompression_time'] += total_time

            metadata = {
                'original_size': original_size,
                'compressed_size': len(data),
                'decompressed_size': len(current),
                'passes_applied': passes,
                'decompression_time_ms': total_time * 1000,
                'throughput_mbps': (len(current) / (1024*1024)) / total_time if total_time > 0 else 0,
                'validated': True,
                'algorithm': 'ACE',
                'version': self.VERSION
            }

            return current, metadata

        except Exception as e:
            return b'', {'error': str(e)}

    def get_stats(self) -> Dict:
        """Get compression statistics"""
        stats = self.stats.copy()

        if stats['bytes_in'] > 0:
            stats['overall_ratio'] = stats['bytes_in'] / stats['bytes_out'] if stats['bytes_out'] > 0 else 0
            stats['overall_reduction_pct'] = (1 - stats['bytes_out']/stats['bytes_in']) * 100
        else:
            stats['overall_ratio'] = 0
            stats['overall_reduction_pct'] = 0

        if stats['total_compressions'] > 0:
            stats['avg_analysis_time_ms'] = (stats['analysis_time'] / stats['total_compressions']) * 1000
            stats['avg_compression_time_ms'] = (stats['compression_time'] / stats['total_compressions']) * 1000

        return stats


def test_adaptive_engine():
    """Test 9: Comprehensive adaptive compression engine test"""
    print("="*80)
    print("TEST 9: ADAPTIVE COMPRESSION ENGINE")
    print("Self-optimizing multi-pass compression with intelligent strategy selection")
    print("="*80)

    engine = AdaptiveCompressionEngine()

    test_cases = [
        ("Empty data", b''),
        ("Single byte", b'\x42'),
        ("Repeated bytes (100×0xAA)", b'\xAA' * 100),
        ("Sequential (0-255)", bytes(range(256))),
        ("Random (1000 bytes)", bytes([hash(i) % 256 for i in range(1000)])),
        ("Time-series (smooth)", bytes([(128 + int(math.sin(i/10)*50)) % 256 for i in range(1000)])),
        ("High correlation", bytes([100 + (i % 10) for i in range(1000)])),
        ("Mixed pattern", b'\xAA' * 50 + bytes(range(256)) + b'\xFF' * 50),
    ]

    results = []

    for name, data in test_cases:
        print(f"\n{'─'*80}")
        print(f"📋 Test Case: {name}")
        print(f"{'─'*80}")

        if len(data) == 0:
            print("   Size: 0 bytes")
            print("   Result: ✓ SKIP (empty data)")
            continue

        # Compress
        compressed, meta = engine.compress(data, adaptive=True)

        if 'error' in meta:
            print(f"   Result: ✗ FAIL - {meta['error']}")
            continue

        # Decompress and validate
        decompressed, decomp_meta = engine.decompress(compressed)

        if 'error' in decomp_meta:
            print(f"   Result: ✗ FAIL - {decomp_meta['error']}")
            continue

        # Validate
        is_valid = decompressed == data

        # Print results
        print(f"   Original size:    {meta['original_size']:,} bytes")
        print(f"   Compressed size:  {meta['compressed_size']:,} bytes")
        print(f"   Compression ratio: {meta['ratio']:.2f}×")
        print(f"   Reduction:        {meta['reduction_pct']:.1f}%")
        print(f"   Strategy:         {meta['strategy']}")
        print(f"   Passes attempted: {meta['passes_attempted']}")
        print(f"   Passes applied:   {meta['passes_applied']}")
        print(f"   Pass sequence:    {' → '.join(meta['pass_sequence']) if meta['pass_sequence'] else 'none'}")
        print(f"\n   📊 Data Analysis:")
        print(f"      Entropy:          {meta['analysis']['entropy']:.3f} bits/byte")
        print(f"      Correlation:      {meta['analysis']['correlation']:.3f}")
        print(f"      Repetition:       {meta['analysis']['repetition']:.3f}")
        print(f"      Compressibility:  {meta['analysis']['compressibility']:.3f}")
        print(f"\n   ⚡ Performance:")
        print(f"      Analysis time:    {meta['analysis_time_ms']:.2f} ms")
        print(f"      Compression time: {meta['compression_time_ms']:.2f} ms")
        print(f"      Total time:       {meta['total_time_ms']:.2f} ms")
        print(f"      Throughput:       {meta['throughput_mbps']:.2f} MB/s")

        result_str = '✓ PASS' if is_valid else '✗ FAIL'
        print(f"\n   Result: {result_str}")

        results.append({
            'name': name,
            'original': len(data),
            'compressed': meta['compressed_size'],
            'ratio': meta['ratio'],
            'strategy': meta['strategy'],
            'passes': meta['pass_sequence'],
            'valid': is_valid
        })

    # Large data test
    print(f"\n{'─'*80}")
    print(f"📋 Test Case: Large time-series (10 MB)")
    print(f"{'─'*80}")

    large_data = bytes([(128 + int(math.sin(i/100)*100)) % 256 for i in range(10 * 1024 * 1024)])

    compressed, meta = engine.compress(large_data, adaptive=True)

    if 'error' not in meta:
        print(f"   Original size:    {meta['original_size']:,} bytes")
        print(f"   Compressed size:  {meta['compressed_size']:,} bytes")
        print(f"   Compression ratio: {meta['ratio']:.2f}×")
        print(f"   Reduction:        {meta['reduction_pct']:.1f}%")
        print(f"   Strategy:         {meta['strategy']}")
        print(f"   Passes applied:   {' → '.join(meta['pass_sequence'])}")
        print(f"   Compression time: {meta['compression_time_ms']/1000:.3f}s ({meta['throughput_mbps']:.2f} MB/s)")

        # Decompress
        decompressed, decomp_meta = engine.decompress(compressed)
        if 'error' not in decomp_meta:
            is_valid = decompressed == large_data
            print(f"   Decompression time: {decomp_meta['decompression_time_ms']/1000:.3f}s ({decomp_meta['throughput_mbps']:.2f} MB/s)")
            print(f"   Result: {'✓ PASS' if is_valid else '✗ FAIL'}")

    # Summary
    print(f"\n{'='*80}")
    print("ADAPTIVE ENGINE STATISTICS")
    print(f"{'='*80}")

    stats = engine.get_stats()
    print(f"Total compressions:   {stats['total_compressions']}")
    print(f"Total decompressions: {stats['total_decompressions']}")
    print(f"Bytes in:             {stats['bytes_in']:,}")
    print(f"Bytes out:            {stats['bytes_out']:,}")
    print(f"Overall ratio:        {stats['overall_ratio']:.2f}×")
    print(f"Overall reduction:    {stats['overall_reduction_pct']:.1f}%")
    print(f"Avg analysis time:    {stats['avg_analysis_time_ms']:.2f} ms")
    print(f"Avg compression time: {stats['avg_compression_time_ms']:.2f} ms")

    # Strategy effectiveness
    print(f"\n{'='*80}")
    print("STRATEGY SELECTION SUMMARY")
    print(f"{'='*80}")

    strategy_counts = {}
    for result in results:
        strategy = result['strategy']
        if strategy not in strategy_counts:
            strategy_counts[strategy] = {'count': 0, 'ratios': []}
        strategy_counts[strategy]['count'] += 1
        strategy_counts[strategy]['ratios'].append(result['ratio'])

    for strategy, data in sorted(strategy_counts.items(), key=lambda x: x[1]['count'], reverse=True):
        avg_ratio = sum(data['ratios']) / len(data['ratios'])
        print(f"{strategy:30} | Count: {data['count']} | Avg Ratio: {avg_ratio:.2f}×")

    print(f"\n{'='*80}")
    print("✅ ADAPTIVE COMPRESSION ENGINE TEST COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_adaptive_engine()
