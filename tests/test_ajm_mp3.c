/* Decode a generated stereo MP3 through the production AJM batch API.
 * Usage: ajm-mp3-test input.mp3 output.f32 (compare against FFmpeg's float PCM).
 * Link with LibAtrac9, libavcodec, libavutil and pthreads; no game files needed. */
#include "../src/runtime_ajm.c"
#include <assert.h>

uintptr_t runtime_lookup(const RuntimeExport *table, size_t count, const char *name) {
    for (size_t i = 0; i < count; ++i)
        if (!strcmp(table[i].name, name)) return (uintptr_t)table[i].function;
    return 0;
}

int main(int argc, char **argv) {
    assert(argc == 3);
    // Header-like tag/padding bytes for Layer I/II must never reach the MP3 decoder.
    for (unsigned layer = 0; layer < 4; ++layer) {
        unsigned char header[] = {0xff, (unsigned char)(0xf9 | (layer << 1)), 0x90, 0x00};
        Mp3Frame frame = {0};
        int32_t result = mp3_parse_frame(header, sizeof(header), 0, &frame);
        assert(layer == 1 ? result == 0 : result == ERR_INVALID_PARAMETER);
    }
    FILE *input = fopen(argv[1], "rb");
    assert(input && fseek(input, 0, SEEK_END) == 0);
    long length = ftell(input);
    assert(length > 0 && fseek(input, 0, SEEK_SET) == 0);
    unsigned char *encoded = calloc((size_t)length + AV_INPUT_BUFFER_PADDING_SIZE, 1);
    assert(encoded && fread(encoded, 1, (size_t)length, input) == (size_t)length);
    fclose(input);
    FILE *output = fopen(argv[2], "wb");
    assert(output);

    uint32_t ctx, instance;
    assert(ajm_initialize(0, &ctx) == 0);
    assert(ajm_module_register(ctx, 0, 0) == 0);
    assert(ajm_instance_create(ctx, 0, 1 | (2 << 3) | (FORMAT_FLOAT << 7), &instance) == 0);
    size_t consumed = 0, decoded = 0, jobs = 0;
    while (consumed < (size_t)length) {
        unsigned char command[256] = {0}, sideband[64] = {0};
        float pcm[4096 * 2];
        const uint64_t flags = 1 | (UINT64_C(1) << 12) | (UINT64_C(1) << 46) |
                               (UINT64_C(1) << 47);
        unsigned char *end = job_run(command, instance, flags, encoded + consumed,
                                     (uint64_t)length - consumed, pcm, sizeof(pcm),
                                     sideband, sizeof(sideband), NULL);
        uint32_t batch;
        BatchError error = {0};
        assert(ajm_batch_start(ctx, command, (uint32_t)(end - command), 0, &error, &batch) == 0);
        assert(ajm_batch_wait(ctx, batch, 0, &error) == 0);
        SidebandResult result;
        SidebandStream stream;
        SidebandFormat format;
        memcpy(&result, sideband, sizeof(result));
        memcpy(&stream, sideband + 8, sizeof(stream));
        memcpy(&format, sideband + 24, sizeof(format));
        assert(result.result == 0 && result.internal_result == 0);
        assert(stream.input_consumed > 0 && stream.output_written >= 0);
        assert((uint64_t)stream.input_consumed <= (uint64_t)length - consumed);
        assert((size_t)stream.output_written <= sizeof(pcm));
        assert(format.channels == 2 && format.sample_rate == 48000);
        assert(format.encoding == FORMAT_FLOAT);
        assert(fwrite(pcm, 1, (size_t)stream.output_written, output) ==
               (size_t)stream.output_written);
        consumed += (size_t)stream.input_consumed;
        decoded += (size_t)stream.output_written;
        assert(++jobs < 1000);
    }
    assert(decoded > 0 && jobs > 1);
    assert(ajm_instance_destroy(ctx, instance) == 0);
    assert(ajm_finalize(ctx) == 0);
    fclose(output);
    free(encoded);
    printf("AJM MP3: %zu bytes consumed, %zu PCM bytes in %zu batch jobs\n",
           consumed, decoded, jobs);
    return 0;
}
