/*
 * fold26_wuwei.c
 * Wu-Wei compression - let data determine its own optimal path
 * "The best compression follows the nature of the data"
 *
 * Philosophy:
 * - Analyze data characteristics (entropy, correlation, repetition)
 * - Let data guide compression strategy selection
 * - Apply only transformations that naturally reduce size
 * - Flow like water - adapt to data's structure
 *
 * Compile: gcc -O3 -Wall -o fold26ww fold26_wuwei.c -lcrypto -lz -lm
 * Usage: ./fold26ww compress <input> <output>
 *        ./fold26ww decompress <input> <output>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <openssl/sha.h>
#include <zlib.h>

#define FOLD26_VERSION "3.0.0-wuwei"
#define FOLD26_MAGIC "FWW\x01"  /* Fold26 Wu-Wei */
#define FOLD26_MAGIC_SIZE 4
#define FOLD26_HEADER_SIZE 50  /* magic(4) + size(4) + hash(32) + passes(1) + pass_seq(9) */
#define RLE_ESCAPE 0xFF
#define MAX_RUN_LENGTH 255
#define MAX_PASSES 9

/* Pass types - each represents a natural transformation */
typedef enum {
    PASS_NONE = 0,
    PASS_DELTA = 1,      /* Temporal correlation */
    PASS_RLE = 2,        /* Repetition */
    PASS_GZIP = 3,       /* General compression */
    PASS_XOR = 4,        /* XOR with previous */
    PASS_ROTATE = 5,     /* Bit rotation */
} PassType;

typedef struct {
    uint8_t *data;
    size_t size;
    size_t capacity;
} Buffer;

typedef struct {
    float entropy;           /* Shannon entropy (0-8 bits/byte) */
    float correlation;       /* Temporal correlation (0-1) */
    float repetition;        /* Repetition factor (0-1) */
    float compressibility;   /* Overall compression potential (0-1) */
    int has_structure;       /* Binary/text distinction */
} DataCharacteristics;

typedef struct {
    PassType passes[MAX_PASSES];
    int num_passes;
    float expected_ratio;
    const char *strategy_name;
} CompressionStrategy;

typedef struct {
    size_t original_size;
    size_t compressed_size;
    float ratio;
    float reduction_pct;
    uint8_t hash[SHA256_DIGEST_LENGTH];
    uint8_t num_passes;
    PassType pass_sequence[MAX_PASSES];
    int validated;
} CompressionMetadata;

/* ============================================================================
 * BUFFER MANAGEMENT
 * ============================================================================ */

Buffer* buffer_create(size_t initial_capacity) {
    Buffer *buf = (Buffer*)malloc(sizeof(Buffer));
    if (!buf) return NULL;

    buf->data = (uint8_t*)malloc(initial_capacity);
    if (!buf->data) {
        free(buf);
        return NULL;
    }

    buf->size = 0;
    buf->capacity = initial_capacity;
    return buf;
}

void buffer_free(Buffer *buf) {
    if (buf) {
        free(buf->data);
        free(buf);
    }
}

int buffer_append(Buffer *buf, uint8_t byte) {
    if (buf->size >= buf->capacity) {
        size_t new_capacity = buf->capacity * 2;
        uint8_t *new_data = (uint8_t*)realloc(buf->data, new_capacity);
        if (!new_data) return -1;
        buf->data = new_data;
        buf->capacity = new_capacity;
    }

    buf->data[buf->size++] = byte;
    return 0;
}

int buffer_append_bytes(Buffer *buf, const uint8_t *bytes, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (buffer_append(buf, bytes[i]) != 0) return -1;
    }
    return 0;
}

/* ============================================================================
 * WU-WEI: DATA ANALYSIS - Listen to the data's nature
 * ============================================================================ */

float calculate_entropy(const uint8_t *data, size_t size) {
    if (size == 0) return 0.0f;

    /* Count byte frequencies */
    uint32_t freq[256] = {0};
    for (size_t i = 0; i < size; i++) {
        freq[data[i]]++;
    }

    /* Calculate Shannon entropy */
    float entropy = 0.0f;
    for (int i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            float prob = (float)freq[i] / size;
            entropy -= prob * log2f(prob);
        }
    }

    return entropy;
}

float calculate_correlation(const uint8_t *data, size_t size) {
    if (size < 2) return 0.0f;

    /* Measure temporal correlation via delta patterns */
    uint32_t small_deltas = 0;
    for (size_t i = 1; i < size; i++) {
        int delta = abs((int)data[i] - (int)data[i-1]);
        if (delta <= 16) small_deltas++;
    }

    return (float)small_deltas / (size - 1);
}

float calculate_repetition(const uint8_t *data, size_t size) {
    if (size < 2) return 0.0f;

    /* Find longest runs and repeated patterns */
    size_t max_run = 1;
    size_t current_run = 1;

    for (size_t i = 1; i < size; i++) {
        if (data[i] == data[i-1]) {
            current_run++;
            if (current_run > max_run) max_run = current_run;
        } else {
            current_run = 1;
        }
    }

    /* Normalize: runs of 3+ indicate high repetition */
    return fminf(1.0f, (float)max_run / 10.0f);
}

DataCharacteristics analyze_data(const uint8_t *data, size_t size) {
    DataCharacteristics chars;

    chars.entropy = calculate_entropy(data, size);
    chars.correlation = calculate_correlation(data, size);
    chars.repetition = calculate_repetition(data, size);

    /* Compressibility score: inverse of entropy, boosted by patterns */
    chars.compressibility = (8.0f - chars.entropy) / 8.0f;
    chars.compressibility += chars.correlation * 0.3f;
    chars.compressibility += chars.repetition * 0.3f;
    chars.compressibility = fminf(1.0f, chars.compressibility);

    /* Structure detection: low entropy + high correlation = structured */
    chars.has_structure = (chars.entropy < 6.0f && chars.correlation > 0.5f);

    return chars;
}

/* ============================================================================
 * WU-WEI: STRATEGY SELECTION - Flow with the data's nature
 * ============================================================================ */

CompressionStrategy select_strategy(DataCharacteristics chars) {
    CompressionStrategy strategy = {0};

    printf("\n[Wu-Wei Analysis]\n");
    printf("  Entropy: %.3f bits/byte\n", chars.entropy);
    printf("  Correlation: %.3f\n", chars.correlation);
    printf("  Repetition: %.3f\n", chars.repetition);
    printf("  Compressibility: %.3f\n", chars.compressibility);

    /* High entropy (random) - wu-wei says: let it be */
    if (chars.entropy >= 7.5f) {
        strategy.strategy_name = "Wu-Wei: Non-Action (High Entropy)";
        strategy.num_passes = 1;
        strategy.passes[0] = PASS_GZIP;  /* Only GZIP has a chance */
        strategy.expected_ratio = 1.0f;
        printf("  Strategy: %s\n", strategy.strategy_name);
        return strategy;
    }

    /* High correlation - flow with temporal patterns */
    if (chars.correlation >= 0.7f) {
        strategy.strategy_name = "Wu-Wei: Flowing River (High Correlation)";
        strategy.num_passes = 4;
        strategy.passes[0] = PASS_DELTA;
        strategy.passes[1] = PASS_RLE;
        strategy.passes[2] = PASS_DELTA;
        strategy.passes[3] = PASS_RLE;
        strategy.expected_ratio = 4.0f;
        printf("  Strategy: %s\n", strategy.strategy_name);
        return strategy;
    }

    /* High repetition - embrace the pattern */
    if (chars.repetition >= 0.6f) {
        strategy.strategy_name = "Wu-Wei: Repeated Waves (High Repetition)";
        strategy.num_passes = 3;
        strategy.passes[0] = PASS_RLE;
        strategy.passes[1] = PASS_DELTA;
        strategy.passes[2] = PASS_RLE;
        strategy.expected_ratio = 5.0f;
        printf("  Strategy: %s\n", strategy.strategy_name);
        return strategy;
    }

    /* Structured data - gentle transformation */
    if (chars.has_structure) {
        strategy.strategy_name = "Wu-Wei: Gentle Stream (Structured)";
        strategy.num_passes = 3;
        strategy.passes[0] = PASS_DELTA;
        strategy.passes[1] = PASS_RLE;
        strategy.passes[2] = PASS_GZIP;
        strategy.expected_ratio = 3.0f;
        printf("  Strategy: %s\n", strategy.strategy_name);
        return strategy;
    }

    /* Default: balanced approach */
    strategy.strategy_name = "Wu-Wei: Balanced Path";
    strategy.num_passes = 2;
    strategy.passes[0] = PASS_DELTA;
    strategy.passes[1] = PASS_GZIP;
    strategy.expected_ratio = 2.0f;
    printf("  Strategy: %s\n", strategy.strategy_name);
    return strategy;
}

/* ============================================================================
 * COMPRESSION PASSES
 * ============================================================================ */

Buffer* delta_encode(const uint8_t *data, size_t size) {
    if (size == 0) return buffer_create(0);

    Buffer *out = buffer_create(size);
    if (!out) return NULL;

    buffer_append(out, data[0]);

    for (size_t i = 1; i < size; i++) {
        uint8_t delta = (data[i] - data[i-1]) & 0xFF;
        buffer_append(out, delta);
    }

    return out;
}

Buffer* delta_decode(const uint8_t *data, size_t size) {
    if (size == 0) return buffer_create(0);

    Buffer *out = buffer_create(size);
    if (!out) return NULL;

    buffer_append(out, data[0]);

    for (size_t i = 1; i < size; i++) {
        uint8_t value = (out->data[i-1] + data[i]) & 0xFF;
        buffer_append(out, value);
    }

    return out;
}

Buffer* rle_encode(const uint8_t *data, size_t size) {
    if (size == 0) return buffer_create(0);

    Buffer *out = buffer_create(size);
    if (!out) return NULL;

    size_t i = 0;
    while (i < size) {
        uint8_t value = data[i];
        size_t count = 1;

        while (i + count < size && data[i + count] == value && count < MAX_RUN_LENGTH) {
            count++;
        }

        if (count >= 3) {
            buffer_append(out, RLE_ESCAPE);
            buffer_append(out, value);
            buffer_append(out, (uint8_t)count);
        } else if (count == 2) {
            buffer_append(out, value);
            buffer_append(out, value);
        } else {
            if (value == RLE_ESCAPE) {
                buffer_append(out, RLE_ESCAPE);
                buffer_append(out, RLE_ESCAPE);
                buffer_append(out, 0x01);
            } else {
                buffer_append(out, value);
            }
        }

        i += count;
    }

    return out;
}

Buffer* rle_decode(const uint8_t *data, size_t size) {
    if (size == 0) return buffer_create(0);

    Buffer *out = buffer_create(size * 2);
    if (!out) return NULL;

    size_t i = 0;
    while (i < size) {
        if (data[i] == RLE_ESCAPE) {
            if (i + 2 >= size) {
                buffer_free(out);
                return NULL;
            }

            uint8_t value = data[i + 1];
            uint8_t count = data[i + 2];

            for (uint8_t j = 0; j < count; j++) {
                buffer_append(out, value);
            }

            i += 3;
        } else {
            buffer_append(out, data[i]);
            i++;
        }
    }

    return out;
}

Buffer* gzip_compress(const uint8_t *data, size_t size) {
    if (size == 0) return buffer_create(0);

    uLongf compressed_size = compressBound(size);
    Buffer *out = buffer_create(compressed_size + 4);
    if (!out) return NULL;

    uint32_t size_le = (uint32_t)size;
    buffer_append_bytes(out, (uint8_t*)&size_le, sizeof(uint32_t));

    uint8_t *compressed_data = (uint8_t*)malloc(compressed_size);
    if (!compressed_data) {
        buffer_free(out);
        return NULL;
    }

    int result = compress2(compressed_data, &compressed_size, data, size, Z_BEST_COMPRESSION);

    if (result != Z_OK) {
        free(compressed_data);
        buffer_free(out);
        return NULL;
    }

    buffer_append_bytes(out, compressed_data, compressed_size);
    free(compressed_data);

    return out;
}

Buffer* gzip_decompress(const uint8_t *data, size_t size) {
    if (size < 4) return NULL;

    uint32_t original_size;
    memcpy(&original_size, data, sizeof(uint32_t));

    Buffer *out = buffer_create(original_size);
    if (!out) return NULL;

    uLongf decompressed_size = original_size;
    uint8_t *decompressed_data = (uint8_t*)malloc(decompressed_size);
    if (!decompressed_data) {
        buffer_free(out);
        return NULL;
    }

    int result = uncompress(decompressed_data, &decompressed_size, data + 4, size - 4);

    if (result != Z_OK) {
        free(decompressed_data);
        buffer_free(out);
        return NULL;
    }

    buffer_append_bytes(out, decompressed_data, decompressed_size);
    free(decompressed_data);

    return out;
}

Buffer* apply_pass(const uint8_t *data, size_t size, PassType pass) {
    switch (pass) {
        case PASS_DELTA: return delta_encode(data, size);
        case PASS_RLE: return rle_encode(data, size);
        case PASS_GZIP: return gzip_compress(data, size);
        default: return NULL;
    }
}

Buffer* reverse_pass(const uint8_t *data, size_t size, PassType pass) {
    switch (pass) {
        case PASS_DELTA: return delta_decode(data, size);
        case PASS_RLE: return rle_decode(data, size);
        case PASS_GZIP: return gzip_decompress(data, size);
        default: return NULL;
    }
}

/* ============================================================================
 * WU-WEI COMPRESSION - Effortless action guided by data's nature
 * ============================================================================ */

Buffer* fold26_compress_wuwei(const uint8_t *data, size_t size, CompressionMetadata *meta) {
    if (size == 0) {
        fprintf(stderr, "Error: Empty input\n");
        return NULL;
    }

    /* Calculate hash */
    SHA256(data, size, meta->hash);

    /* Wu-Wei: Listen to the data */
    DataCharacteristics chars = analyze_data(data, size);
    CompressionStrategy strategy = select_strategy(chars);

    /* Apply passes intelligently - only keep what helps */
    Buffer *current = buffer_create(size);
    buffer_append_bytes(current, data, size);

    meta->num_passes = 0;

    printf("\n[Compression Passes]\n");

    for (int i = 0; i < strategy.num_passes; i++) {
        PassType pass = strategy.passes[i];
        size_t before_size = current->size;

        Buffer *transformed = apply_pass(current->data, current->size, pass);
        if (!transformed) {
            printf("  Pass %d (%d): FAILED\n", i + 1, pass);
            continue;
        }

        size_t after_size = transformed->size;
        float pass_ratio = (float)before_size / after_size;

        /* Wu-Wei: Only keep transformations that flow naturally (compress) */
        /* OR keep intermediate passes that enable later compression */
        int keep_pass = (after_size <= before_size) || (i < strategy.num_passes - 1);

        if (keep_pass) {
            printf("  Pass %d (%d): %zu → %zu bytes (%.2fx)\n",
                   i + 1, pass, before_size, after_size, pass_ratio);
            buffer_free(current);
            current = transformed;
            meta->pass_sequence[meta->num_passes++] = pass;
        } else {
            printf("  Pass %d (%d): %zu → %zu bytes (%.2fx) [SKIPPED - no improvement]\n",
                   i + 1, pass, before_size, after_size, pass_ratio);
            buffer_free(transformed);
        }
    }

    /* Wu-Wei: If final result is larger, return to origin */
    if (current->size >= size) {
        printf("\n[Wu-Wei Wisdom: Original form is best]\n");
        buffer_free(current);
        current = buffer_create(size);
        buffer_append_bytes(current, data, size);
        meta->num_passes = 0;
    }

    /* Build output with header */
    Buffer *output = buffer_create(FOLD26_HEADER_SIZE + current->size);
    if (!output) {
        buffer_free(current);
        return NULL;
    }

    /* Write header */
    buffer_append_bytes(output, (uint8_t*)FOLD26_MAGIC, FOLD26_MAGIC_SIZE);

    uint32_t size_le = (uint32_t)size;
    buffer_append_bytes(output, (uint8_t*)&size_le, sizeof(uint32_t));

    buffer_append_bytes(output, meta->hash, SHA256_DIGEST_LENGTH);

    buffer_append(output, meta->num_passes);

    /* Write pass sequence */
    for (int i = 0; i < MAX_PASSES; i++) {
        uint8_t pass = (i < meta->num_passes) ? meta->pass_sequence[i] : 0;
        buffer_append(output, pass);
    }

    /* Write payload */
    buffer_append_bytes(output, current->data, current->size);

    buffer_free(current);

    /* Fill metadata */
    meta->original_size = size;
    meta->compressed_size = output->size;
    meta->ratio = (float)size / output->size;
    meta->reduction_pct = (1.0f - (float)output->size / size) * 100.0f;

    return output;
}

Buffer* fold26_decompress_wuwei(const uint8_t *data, size_t size, CompressionMetadata *meta) {
    if (size < FOLD26_HEADER_SIZE) {
        fprintf(stderr, "Error: Data too short\n");
        return NULL;
    }

    /* Validate magic */
    if (memcmp(data, FOLD26_MAGIC, FOLD26_MAGIC_SIZE) != 0) {
        fprintf(stderr, "Error: Invalid magic header\n");
        return NULL;
    }

    /* Parse header */
    uint32_t original_size;
    memcpy(&original_size, data + FOLD26_MAGIC_SIZE, sizeof(uint32_t));

    const uint8_t *stored_hash = data + FOLD26_MAGIC_SIZE + sizeof(uint32_t);

    uint8_t num_passes = data[40];

    /* Read pass sequence */
    PassType pass_sequence[MAX_PASSES];
    for (int i = 0; i < MAX_PASSES; i++) {
        pass_sequence[i] = data[41 + i];
    }

    const uint8_t *payload = data + FOLD26_HEADER_SIZE;
    size_t payload_size = size - FOLD26_HEADER_SIZE;

    /* Reverse passes in reverse order */
    Buffer *current = buffer_create(payload_size);
    buffer_append_bytes(current, payload, payload_size);

    for (int i = num_passes - 1; i >= 0; i--) {
        Buffer *decoded = reverse_pass(current->data, current->size, pass_sequence[i]);
        buffer_free(current);
        if (!decoded) {
            fprintf(stderr, "Error: Pass %d decoding failed\n", i);
            return NULL;
        }
        current = decoded;
    }

    /* Validate hash */
    uint8_t computed_hash[SHA256_DIGEST_LENGTH];
    SHA256(current->data, current->size, computed_hash);

    if (memcmp(computed_hash, stored_hash, SHA256_DIGEST_LENGTH) != 0) {
        fprintf(stderr, "Error: Hash mismatch\n");
        buffer_free(current);
        return NULL;
    }

    /* Fill metadata */
    meta->original_size = original_size;
    meta->compressed_size = size;
    meta->num_passes = num_passes;
    meta->validated = 1;
    memcpy(meta->hash, stored_hash, SHA256_DIGEST_LENGTH);

    return current;
}

/* ============================================================================
 * FILE I/O
 * ============================================================================ */

int fold26_compress_file(const char *input_path, const char *output_path) {
    FILE *fp = fopen(input_path, "rb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open input file: %s\n", input_path);
        return -1;
    }

    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    uint8_t *data = (uint8_t*)malloc(size);
    if (!data) {
        fclose(fp);
        return -1;
    }

    fread(data, 1, size, fp);
    fclose(fp);

    /* Wu-Wei Compression */
    CompressionMetadata meta = {0};
    Buffer *compressed = fold26_compress_wuwei(data, size, &meta);
    free(data);

    if (!compressed) {
        return -1;
    }

    /* Write output */
    fp = fopen(output_path, "wb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open output file: %s\n", output_path);
        buffer_free(compressed);
        return -1;
    }

    fwrite(compressed->data, 1, compressed->size, fp);
    fclose(fp);

    /* Print stats */
    printf("\n[Compression Complete]\n");
    printf("  Input: %s (%zu bytes)\n", input_path, meta.original_size);
    printf("  Output: %s (%zu bytes)\n", output_path, meta.compressed_size);
    printf("  Ratio: %.2fx\n", meta.ratio);
    printf("  Reduction: %.1f%%\n", meta.reduction_pct);
    printf("  Passes applied: %d\n", meta.num_passes);

    buffer_free(compressed);
    return 0;
}

int fold26_decompress_file(const char *input_path, const char *output_path) {
    FILE *fp = fopen(input_path, "rb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open input file: %s\n", input_path);
        return -1;
    }

    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    uint8_t *data = (uint8_t*)malloc(size);
    if (!data) {
        fclose(fp);
        return -1;
    }

    fread(data, 1, size, fp);
    fclose(fp);

    /* Wu-Wei Decompression */
    CompressionMetadata meta = {0};
    Buffer *decompressed = fold26_decompress_wuwei(data, size, &meta);
    free(data);

    if (!decompressed) {
        return -1;
    }

    /* Write output */
    fp = fopen(output_path, "wb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open output file: %s\n", output_path);
        buffer_free(decompressed);
        return -1;
    }

    fwrite(decompressed->data, 1, decompressed->size, fp);
    fclose(fp);

    printf("\n[Decompression Complete]\n");
    printf("  Input: %s (%zu bytes)\n", input_path, size);
    printf("  Output: %s (%zu bytes)\n", output_path, meta.original_size);
    printf("  Passes reversed: %d\n", meta.num_passes);
    printf("  Validated: %s\n", meta.validated ? "✓" : "✗");

    buffer_free(decompressed);
    return 0;
}

/* ============================================================================
 * MAIN
 * ============================================================================ */

int main(int argc, char *argv[]) {
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  fold26 Wu-Wei Compressor v%s\n", FOLD26_VERSION);
    printf("  無為 - Effortless compression guided by data's nature\n");
    printf("═══════════════════════════════════════════════════════════════\n");

    if (argc != 4) {
        printf("\nUsage:\n");
        printf("  Compress:   %s compress <input> <output>\n", argv[0]);
        printf("  Decompress: %s decompress <input> <output>\n", argv[0]);
        printf("\nPhilosophy:\n");
        printf("  The compressor analyzes data characteristics and selects\n");
        printf("  the optimal compression path. Each transformation is applied\n");
        printf("  only if it naturally reduces size. Wu-wei: act without forcing.\n");
        return 1;
    }

    const char *mode = argv[1];
    const char *input = argv[2];
    const char *output = argv[3];

    if (strcmp(mode, "compress") == 0) {
        return fold26_compress_file(input, output);
    } else if (strcmp(mode, "decompress") == 0) {
        return fold26_decompress_file(input, output);
    } else {
        fprintf(stderr, "Error: Unknown mode '%s'\n", mode);
        return 1;
    }
}
