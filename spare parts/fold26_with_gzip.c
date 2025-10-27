/*
 * fold26_with_gzip.c
 * Enhanced fold26 with optional GZIP compression stage
 * Delta + RLE + GZIP for maximum compression
 *
 * Compile: gcc -O3 -Wall -o fold26gz fold26_with_gzip.c -lcrypto -lz
 * Usage: ./fold26gz compress <input> <output> [--gzip]
 *        ./fold26gz decompress <input> <output>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <openssl/sha.h>
#include <zlib.h>

#define FOLD26_VERSION "2.0.0"
#define FOLD26_MAGIC "F2G\x01"  /* F26 + Gzip */
#define FOLD26_MAGIC_SIZE 4
#define FOLD26_HEADER_SIZE 41  /* magic(4) + size(4) + hash(32) + flags(1) */
#define RLE_ESCAPE 0xFF
#define MAX_RUN_LENGTH 255

/* Compression flags */
#define FLAG_DELTA     0x01
#define FLAG_RLE       0x02
#define FLAG_GZIP      0x04

typedef struct {
    uint8_t *data;
    size_t size;
    size_t capacity;
} Buffer;

typedef struct {
    size_t original_size;
    size_t compressed_size;
    float ratio;
    float reduction_pct;
    uint8_t hash[SHA256_DIGEST_LENGTH];
    uint8_t flags;
    int validated;
} CompressionMetadata;

/* Buffer management */
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

/* Delta encoding */
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

/* RLE encoding */
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
                fprintf(stderr, "Error: Truncated RLE escape at position %zu\n", i);
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

/* GZIP compression */
Buffer* gzip_compress(const uint8_t *data, size_t size) {
    if (size == 0) return buffer_create(0);

    /* Allocate output buffer (zlib recommends source_size + 0.1% + 12) */
    uLongf compressed_size = compressBound(size);
    Buffer *out = buffer_create(compressed_size + 8);  /* +8 for size header */
    if (!out) return NULL;

    /* Store original size (for decompression buffer allocation) */
    uint32_t size_le = (uint32_t)size;
    buffer_append_bytes(out, (uint8_t*)&size_le, sizeof(uint32_t));

    /* Compress with zlib */
    uint8_t *compressed_data = (uint8_t*)malloc(compressed_size);
    if (!compressed_data) {
        buffer_free(out);
        return NULL;
    }

    int result = compress2(compressed_data, &compressed_size, data, size, Z_BEST_COMPRESSION);

    if (result != Z_OK) {
        fprintf(stderr, "Error: GZIP compression failed (code %d)\n", result);
        free(compressed_data);
        buffer_free(out);
        return NULL;
    }

    /* Append compressed data */
    buffer_append_bytes(out, compressed_data, compressed_size);
    free(compressed_data);

    return out;
}

Buffer* gzip_decompress(const uint8_t *data, size_t size) {
    if (size < 4) {
        fprintf(stderr, "Error: GZIP data too short\n");
        return NULL;
    }

    /* Read original size */
    uint32_t original_size;
    memcpy(&original_size, data, sizeof(uint32_t));

    /* Decompress */
    Buffer *out = buffer_create(original_size);
    if (!out) return NULL;

    uLongf decompressed_size = original_size;
    uint8_t *decompressed_data = (uint8_t*)malloc(decompressed_size);
    if (!decompressed_data) {
        buffer_free(out);
        return NULL;
    }

    int result = uncompress(decompressed_data, &decompressed_size,
                           data + 4, size - 4);

    if (result != Z_OK) {
        fprintf(stderr, "Error: GZIP decompression failed (code %d)\n", result);
        free(decompressed_data);
        buffer_free(out);
        return NULL;
    }

    buffer_append_bytes(out, decompressed_data, decompressed_size);
    free(decompressed_data);

    return out;
}

/* Multi-stage compression */
Buffer* fold26_compress_multi(const uint8_t *data, size_t size, int use_gzip, CompressionMetadata *meta) {
    if (size == 0) {
        fprintf(stderr, "Error: Empty input\n");
        return NULL;
    }

    /* Calculate SHA-256 hash */
    SHA256(data, size, meta->hash);

    Buffer *current = NULL;
    meta->flags = 0;

    /* Stage 1: Delta encoding */
    Buffer *delta_buf = delta_encode(data, size);
    if (!delta_buf) {
        fprintf(stderr, "Error: Delta encoding failed\n");
        return NULL;
    }
    meta->flags |= FLAG_DELTA;
    current = delta_buf;

    /* Stage 2: RLE */
    Buffer *rle_buf = rle_encode(current->data, current->size);
    buffer_free(current);
    if (!rle_buf) {
        fprintf(stderr, "Error: RLE encoding failed\n");
        return NULL;
    }
    meta->flags |= FLAG_RLE;
    current = rle_buf;

    /* Stage 3: GZIP (optional) */
    if (use_gzip) {
        Buffer *gzip_buf = gzip_compress(current->data, current->size);
        buffer_free(current);
        if (!gzip_buf) {
            fprintf(stderr, "Error: GZIP compression failed\n");
            return NULL;
        }
        meta->flags |= FLAG_GZIP;
        current = gzip_buf;
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

    buffer_append(output, meta->flags);

    /* Write compressed payload */
    buffer_append_bytes(output, current->data, current->size);

    buffer_free(current);

    /* Fill metadata */
    meta->original_size = size;
    meta->compressed_size = output->size;
    meta->ratio = (float)size / output->size;
    meta->reduction_pct = (1.0f - (float)output->size / size) * 100.0f;

    return output;
}

Buffer* fold26_decompress_multi(const uint8_t *data, size_t size, CompressionMetadata *meta) {
    if (size < FOLD26_HEADER_SIZE) {
        fprintf(stderr, "Error: Data too short for valid fold26 format\n");
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
    uint8_t flags = data[40];

    const uint8_t *payload = data + FOLD26_HEADER_SIZE;
    size_t payload_size = size - FOLD26_HEADER_SIZE;

    Buffer *current = buffer_create(payload_size);
    buffer_append_bytes(current, payload, payload_size);

    /* Stage 3 (reverse): GZIP decompress */
    if (flags & FLAG_GZIP) {
        Buffer *gzip_decoded = gzip_decompress(current->data, current->size);
        buffer_free(current);
        if (!gzip_decoded) {
            fprintf(stderr, "Error: GZIP decompression failed\n");
            return NULL;
        }
        current = gzip_decoded;
    }

    /* Stage 2 (reverse): RLE decode */
    if (flags & FLAG_RLE) {
        Buffer *rle_decoded = rle_decode(current->data, current->size);
        buffer_free(current);
        if (!rle_decoded) {
            fprintf(stderr, "Error: RLE decoding failed\n");
            return NULL;
        }
        current = rle_decoded;
    }

    /* Stage 1 (reverse): Delta decode */
    if (flags & FLAG_DELTA) {
        Buffer *delta_decoded = delta_decode(current->data, current->size);
        buffer_free(current);
        if (!delta_decoded) {
            fprintf(stderr, "Error: Delta decoding failed\n");
            return NULL;
        }
        current = delta_decoded;
    }

    /* Validate hash */
    uint8_t computed_hash[SHA256_DIGEST_LENGTH];
    SHA256(current->data, current->size, computed_hash);

    if (memcmp(computed_hash, stored_hash, SHA256_DIGEST_LENGTH) != 0) {
        fprintf(stderr, "Error: Hash mismatch - data corrupted\n");
        buffer_free(current);
        return NULL;
    }

    /* Validate size */
    if (current->size != original_size) {
        fprintf(stderr, "Error: Size mismatch - expected %u, got %zu\n",
                original_size, current->size);
        buffer_free(current);
        return NULL;
    }

    /* Fill metadata */
    meta->original_size = original_size;
    meta->compressed_size = size;
    meta->flags = flags;
    meta->validated = 1;
    memcpy(meta->hash, stored_hash, SHA256_DIGEST_LENGTH);

    return current;
}

/* File I/O */
int fold26_compress_file(const char *input_path, const char *output_path, int use_gzip) {
    /* Read input file */
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
        fprintf(stderr, "Error: Memory allocation failed\n");
        fclose(fp);
        return -1;
    }

    fread(data, 1, size, fp);
    fclose(fp);

    /* Compress */
    CompressionMetadata meta = {0};
    Buffer *compressed = fold26_compress_multi(data, size, use_gzip, &meta);
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
    printf("Compression successful:\n");
    printf("  Input: %s (%zu bytes)\n", input_path, meta.original_size);
    printf("  Output: %s (%zu bytes)\n", output_path, meta.compressed_size);
    printf("  Ratio: %.2fx\n", meta.ratio);
    printf("  Reduction: %.1f%%\n", meta.reduction_pct);
    printf("  Stages: Delta%s%s\n",
           (meta.flags & FLAG_RLE) ? " + RLE" : "",
           (meta.flags & FLAG_GZIP) ? " + GZIP" : "");

    buffer_free(compressed);
    return 0;
}

int fold26_decompress_file(const char *input_path, const char *output_path) {
    /* Read input file */
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
        fprintf(stderr, "Error: Memory allocation failed\n");
        fclose(fp);
        return -1;
    }

    fread(data, 1, size, fp);
    fclose(fp);

    /* Decompress */
    CompressionMetadata meta = {0};
    Buffer *decompressed = fold26_decompress_multi(data, size, &meta);
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

    /* Print stats */
    printf("Decompression successful:\n");
    printf("  Input: %s (%zu bytes)\n", input_path, size);
    printf("  Output: %s (%zu bytes)\n", output_path, meta.original_size);
    printf("  Stages: Delta%s%s\n",
           (meta.flags & FLAG_RLE) ? " + RLE" : "",
           (meta.flags & FLAG_GZIP) ? " + GZIP" : "");
    printf("  Hash: ");
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        printf("%02x", meta.hash[i]);
    }
    printf("\n");

    buffer_free(decompressed);
    return 0;
}

/* Main */
int main(int argc, char *argv[]) {
    printf("fold26 Compressor v%s (with GZIP support)\n", FOLD26_VERSION);
    printf("Delta + RLE + GZIP compression for consensus checkpoints\n\n");

    if (argc < 4) {
        printf("Usage:\n");
        printf("  Compress:   %s compress <input> <output> [--gzip]\n", argv[0]);
        printf("  Decompress: %s decompress <input> <output>\n", argv[0]);
        printf("\nOptions:\n");
        printf("  --gzip    Apply GZIP compression after Delta+RLE (recommended for text logs)\n");
        return 1;
    }

    const char *mode = argv[1];
    const char *input = argv[2];
    const char *output = argv[3];

    /* Check for --gzip flag */
    int use_gzip = 0;
    if (argc >= 5 && strcmp(argv[4], "--gzip") == 0) {
        use_gzip = 1;
    }

    if (strcmp(mode, "compress") == 0) {
        return fold26_compress_file(input, output, use_gzip);
    } else if (strcmp(mode, "decompress") == 0) {
        return fold26_decompress_file(input, output);
    } else {
        fprintf(stderr, "Error: Unknown mode '%s'\n", mode);
        return 1;
    }
}
