#!/usr/bin/env python3
from bin_addr import BinaryAddress
from reference import ReferenceCacheStatus
from word_addr import WordAddress


class Cache(dict):

    # Initializes the reference cache with a fixed number of sets
    def __init__(self, cache=None, num_sets=None, num_index_bits=0, is_l2=False):

        # A list of recently ordered addresses, ordered from least-recently
        # used to most
        self.recently_used_addrs = []
        self.is_l2 = is_l2

        if cache is not None:
            self.update(cache)
        else:
            for i in range(num_sets):
                index = BinaryAddress(
                    word_addr=WordAddress(i), num_addr_bits=num_index_bits
                )
                self[index] = []

    # Every time we see an address, place it at the top of the
    # list of recently-seen addresses
    def mark_ref_as_last_seen(self, ref):

        # The index and tag (not the offset) uniquely identify each address
        addr_id = (ref.index, ref.tag)
        if addr_id in self.recently_used_addrs:
            self.recently_used_addrs.remove(addr_id)
        self.recently_used_addrs.append(addr_id)

    # Returns True if a block at the given index and tag exists in the cache,
    # indicating a hit; returns False otherwise, indicating a miss
    def is_hit(self, addr_index, addr_tag):

        # Ensure that indexless fully associative caches are accessed correctly
        if addr_index is None:
            blocks = self["0"]
        elif addr_index in self:
            blocks = self[addr_index]
        else:
            return False

        for block in blocks:
            if block["tag"] == addr_tag:
                return True

        return False

    # Iterate through the recently-used entries in reverse order for MRU
    def replace_block(self, blocks, replacement_policy, addr_index, new_entry):
        if replacement_policy == "mru":
            recently_used_addrs = reversed(self.recently_used_addrs)
        else:
            recently_used_addrs = self.recently_used_addrs
        # Replace the first matching entry with the entry to add
        for recent_index, recent_tag in recently_used_addrs:
            for i, block in enumerate(blocks):
                if recent_index == addr_index and block["tag"] == recent_tag:
                    blocks[i] = new_entry
                    return

    # Adds the given entry to the cache at the given index
    def set_block(self, replacement_policy, num_blocks_per_set, addr_index, new_entry, l2_cache=None):
        # Place all cache entries in a single set if cache is fully associative
        if addr_index is None:
            blocks = self["0"]
        else:
            blocks = self[addr_index]
        # Replace MRU or LRU entry if number of blocks in set exceeds the limit
        if len(blocks) == num_blocks_per_set:
            evicted_entry = blocks.pop(0)
            # L1 캐시에서 퇴출된 블록을 L2 캐시에 추가
            if l2_cache and not self.is_l2:
                l2_cache.set_block(
                    replacement_policy=replacement_policy,
                    num_blocks_per_set=num_blocks_per_set,
                    addr_index=evicted_entry["index"],
                    new_entry=evicted_entry
                )
        blocks.append(new_entry)

    # Simulate the cache by reading the given address references into it
    def read_refs(
        self, num_blocks_per_set, num_words_per_block, replacement_policy, refs, l2_cache=None
    ):
        for ref in refs:
            self.mark_ref_as_last_seen(ref)
            if self.is_hit(ref.index, ref.tag):
                ref.cache_status = ReferenceCacheStatus.hit
            else:
                ref.cache_status = ReferenceCacheStatus.miss
                self.set_block(
                    replacement_policy=replacement_policy,
                    num_blocks_per_set=num_blocks_per_set,
                    addr_index=ref.index,
                    new_entry=ref.get_cache_entry(num_words_per_block),
                    l2_cache=l2_cache,
                )
                if l2_cache and not l2_cache.is_hit(ref.index, ref.tag):
                    l2_cache.set_block(
                        replacement_policy=replacement_policy,
                        num_blocks_per_set=num_blocks_per_set,
                        addr_index=ref.index,
                        new_entry=ref.get_cache_entry(num_words_per_block),
                    )

    # Add a method to retrieve a block from the cache
    def get_block(self, addr_index, addr_tag):
        if addr_index in self:
            blocks = self[addr_index]
            for block in blocks:
                if block["tag"] == addr_tag:
                    return block
        return None


