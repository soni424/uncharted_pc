// SPDX-License-Identifier: GPL-2.0-or-later
#include <algorithm>
#include <cassert>
#include <cstring>
#include <vector>
#include "video_core/renderer_vulkan/vk_scheduler.h"

int main() {
    Vulkan::RecordChunk chunk;
    // The reported U1 copy carried 6,121 regions, larger than a recording chunk.
    constexpr size_t bytes = 6121 * 24;
    static_assert(bytes > Vulkan::RecordChunk::Capacity);
    std::vector<unsigned char> source(bytes, 0x59);
    auto* data = static_cast<unsigned char*>(chunk.AllocateOverflow(bytes));
    std::memcpy(data, source.data(), bytes);
    int executed = 0;
    assert(chunk.Push([data, &executed](vk::CommandBuffer) {
        assert(std::all_of(data, data + bytes, [](auto byte) { return byte == 0x59; }));
        ++executed;
    }));
    // Data must outlive the producer, further allocations, and command execution.
    source.clear();
    source.shrink_to_fit();
    std::memset(chunk.AllocateOverflow(bytes * 2), 0x33, bytes * 2);
    assert(chunk.Push([&executed](vk::CommandBuffer) { assert(executed == 1); ++executed; }));
    assert(executed == 0);
    chunk.Execute(vk::CommandBuffer{});
    assert(executed == 2 && chunk.Empty() && chunk.Size() == 0);
    // Recycled chunks must accept both ordinary data and new oversized data.
    assert(chunk.Allocate(128, 16));
    auto* next = static_cast<unsigned char*>(chunk.AllocateOverflow(bytes));
    std::memset(next, 0x67, bytes);
    assert(chunk.Push([next](vk::CommandBuffer) {
        assert(next[0] == 0x67 && next[bytes - 1] == 0x67);
    }));
    chunk.Execute(vk::CommandBuffer{});
    assert(chunk.Empty() && chunk.Size() == 0);
}
