/*
 * fold26_bridge.c
 * Digital Compression Fallback for Hybrid Mainnet
 *
 * When to use:
 * - Analog encoding fails (non-continuous data)
 * - Event-heavy logs (many topology changes)
 * - Fallback to proven fold26 wu-wei compression
 *
 * Compile: gcc -O3 -Wall -o fold26_bridge fold26_bridge.c -lcrypto -lz -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <zlib.h>
#include <openssl/sha.h>

#define VERSION "26.0-bridge"
#define MAGIC "F26B"

/* Wu-wei strategies */
typedef enum {
    STRATEGY_NONACTION = 0,     /* High entropy: skip compression */
    STRATEGY_FLOWING_RIVER,     /* High correlation: delta→rle→delta→rle */
    STRATEGY_REPEATED_WAVES,    /* High repetition: rle→delta→rle */
    STRATEGY_GENTLE_STREAM,     /* Structured: delta→rle→gzip */
    STRATEGY_BALANCED_PATH      /* Default: delta→gzip */
} CompressionStrategy;

typedef struct {
    float entropy;
    float correlation;
    float repetition;
    float compressibility;
} DataCharacteristics;

/* Compressed output */
typedef struct {
    char magic[4];
    uint32_t version;
    uint64_t original_size;
    CompressionStrategy strategy;
    uint32_t num_passes;
    uint8_t hash[32];
    uint32_t compressed_size;
    uint8_t data[];
} CompressedData;

/* ============================================================================
 * DATA ANALYSIS (Wu-wei: understand before acting)
 * ============================================================================ */

float calculate_entropy(const uint8_t *data, size_t size) {
    if (size == 0) return 0.0f;

    uint32_t freq[256] = {0};
    for (size_t i = 0; i < size; i++) {
        freq[data[i]]++;
    }

    float entropy = 0.0f;
    for (int i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            float p = (float)freq[i] / size;
            entropy -= p * log2f(p);
        }
    }

    return entropy;
}

float calculate_correlation(const uint8_t *data, size_t size) {
    if (size < 2) return 0.0f;

    float mean = 0.0f;
    for (size_t i = 0; i < size; i++) {
        mean += data[i];
    }
    mean /= size;

    float autocorr = 0.0f, variance = 0.0f;
    for (size_t i = 0; i < size - 1; i++) {
        float dev1 = data[i] - mean;
        float dev2 = data[i+1] - mean;
        autocorr += dev1 * dev2;
        variance += dev1 * dev1;
    }

    return (variance > 0) ? (autocorr / variance) : 0.0f;
}

float calculate_repetition(const uint8_t *data, size_t size) {
    if (size < 2) return 0.0f;

    size_t runs = 0;
    for (size_t i = 0; i < size - 1; i++) {
        if (data[i] == data[i+1]) runs++;
    }

    return (float)runs / (size - 1);
}

DataCharacteristics analyze_data(const uint8_t *data, size_t size) {
    DataCharacteristics chars = {0};

    chars.entropy = calculate_entropy(data, size);
    chars.correlation = calculate_correlation(data, size);
    chars.repetition = calculate_repetition(data, size);
    chars.compressibility = 1.0f - (chars.entropy / 8.0f);

    return chars;
}

CompressionStrategy select_strategy(DataCharacteristics chars) {
    /* Wu-wei: Let the data guide the strategy */

    if (chars.entropy >= 7.5f) {
        printf("  Strategy: Non-Action (entropy %.2f, skip compression)\n", chars.entropy);
        return STRATEGY_NONACTION;
    }

    if (chars.correlation >= 0.7f) {
        printf("  Strategy: Flowing River (correlation %.2f)\n", chars.correlation);
        return STRATEGY_FLOWING_RIVER;
    }

    if (chars.repetition >= 0.6f) {
        printf("  Strategy: Repeated Waves (repetition %.2f)\n", chars.repetition);
        return STRATEGY_REPEATED_WAVES;
    }

    if (chars.compressibility >= 0.3f) {
        printf("  Strategy: Gentle Stream (compressibility %.2f)\n", chars.compressibility);
        return STRATEGY_GENTLE_STREAM;
    }

    printf("  Strategy: Balanced Path (default)\n");
    return STRATEGY_BALANCED_PATH;
}

/* ============================================================================
 * COMPRESSION PRIMITIVES
 * ============================================================================ */

size_t delta_encode(const uint8_t *input, size_t size, uint8_t *output) {
    if (size == 0) return 0;

    output[0] = input[0];
    for (size_t i = 1; i < size; i++) {
        output[i] = (input[i] - input[i-1]) & 0xFF;
    }
    return size;
}

size_t rle_encode(const uint8_t *input, size_t size, uint8_t *output) {
    if (size == 0) return 0;

    size_t out_idx = 0;
    size_t i = 0;

    while (i < size) {
        uint8_t value = input[i];
        size_t count = 1;

        while (i + count < size && input[i + count] == value && count < 255) {
            count++;
        }

        output[out_idx++] = value;
        output[out_idx++] = (uint8_t)count;
        i += count;
    }

    return out_idx;
}

size_t gzip_compress(const uint8_t *input, size_t input_size,
                     uint8_t *output, size_t output_size) {
    z_stream zs = {0};

    if (deflateInit2(&zs, Z_BEST_COMPRESSION, Z_DEFLATED, 15 + 16, 8, Z_DEFAULT_STRATEGY) != Z_OK) {
        return 0;
    }

    zs.next_in = (Bytef*)input;
    zs.avail_in = input_size;
    zs.next_out = output;
    zs.avail_out = output_size;

    int ret = deflate(&zs, Z_FINISH);
    deflateEnd(&zs);

    return (ret == Z_STREAM_END) ? zs.total_out : 0;
}

/* ============================================================================
 * HYBRID BRIDGE COMPRESS
 * ============================================================================ */

CompressedData* compress_bridge(const uint8_t *data, size_t size) {
    printf("\n[fold26 Digital Bridge]\n");
    printf("  Input size: %zu bytes\n", size);

    DataCharacteristics chars = analyze_data(data, size);
    CompressionStrategy strategy = select_strategy(chars);

    if (strategy == STRATEGY_NONACTION) {
        /* Wu-wei: Don't force compression on random data */
        CompressedData *result = malloc(sizeof(CompressedData) + size);
        memcpy(result->magic, MAGIC, 4);
        result->version = 1;
        result->original_size = size;
        result->strategy = strategy;
        result->num_passes = 0;
        result->compressed_size = size;
        memcpy(result->data, data, size);

        SHA256(data, size, result->hash);

        printf("  Output: %zu bytes (1.00x, uncompressed)\n", size);
        return result;
    }

    /* Apply compression passes */
    uint8_t *work1 = malloc(size * 2);
    uint8_t *work2 = malloc(size * 2);
    uint8_t *current_in = (uint8_t*)data;
    uint8_t *current_out = work1;
    size_t current_size = size;
    uint32_t passes = 0;

    switch (strategy) {
        case STRATEGY_FLOWING_RIVER:
            current_size = delta_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = rle_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = delta_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = rle_encode(current_in, current_size, current_out);
            current_in = current_out;
            passes++;
            break;

        case STRATEGY_REPEATED_WAVES:
            current_size = rle_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = delta_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = rle_encode(current_in, current_size, current_out);
            current_in = current_out;
            passes++;
            break;

        case STRATEGY_GENTLE_STREAM:
            current_size = delta_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = rle_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = gzip_compress(current_in, current_size, current_out, size * 2);
            current_in = current_out;
            passes++;
            break;

        case STRATEGY_BALANCED_PATH:
        default:
            current_size = delta_encode(current_in, current_size, current_out);
            current_in = current_out; current_out = (current_out == work1) ? work2 : work1;
            passes++;

            current_size = gzip_compress(current_in, current_size, current_out, size * 2);
            current_in = current_out;
            passes++;
            break;
    }

    /* Create result */
    CompressedData *result = malloc(sizeof(CompressedData) + current_size);
    memcpy(result->magic, MAGIC, 4);
    result->version = 1;
    result->original_size = size;
    result->strategy = strategy;
    result->num_passes = passes;
    result->compressed_size = current_size;
    memcpy(result->data, current_in, current_size);

    SHA256(data, size, result->hash);

    float ratio = (float)size / current_size;
    printf("  Passes: %u\n", passes);
    printf("  Output: %u bytes (%.2fx)\n", result->compressed_size, ratio);

    free(work1);
    free(work2);

    return result;
}

/* ============================================================================
 * MAIN
 * ============================================================================ */

int main(int argc, char *argv[]) {
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  fold26 Digital Bridge v%s\n", VERSION);
    printf("  Wu-wei fallback for hybrid mainnet\n");
    printf("═══════════════════════════════════════════════════════════════\n");

    if (argc < 2) {
        printf("\nUsage:\n");
        printf("  Test:   %s test\n", argv[0]);
        printf("  File:   %s compress <input> <output>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "test") == 0) {
        /* Test case 1: Repetitive data */
        uint8_t rep_data[1000];
        for (int i = 0; i < 1000; i++) rep_data[i] = 0xAA;

        CompressedData *result = compress_bridge(rep_data, 1000);
        free(result);

        /* Test case 2: Random data (should skip) */
        uint8_t rand_data[1000];
        for (int i = 0; i < 1000; i++) rand_data[i] = rand() % 256;

        result = compress_bridge(rand_data, 1000);
        free(result);

        printf("\n✓ All tests complete\n");
    }

    return 0;
}
