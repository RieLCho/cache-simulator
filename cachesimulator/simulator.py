#!/usr/bin/env python3

import math
import shutil

from bin_addr import BinaryAddress
from cache import Cache
from reference import Reference
from table import Table

# The names of all reference table columns
REF_COL_NAMES = ("WordAddr", "BinAddr", "Tag", "Index", "Offset", "Hit/Miss")
# The minimum number of bits required per group in a prettified binary string
MIN_BITS_PER_GROUP = 3
# The default column width of the displayed results table
DEFAULT_TABLE_WIDTH = 80


class Simulator(object):

    # Retrieves a list of address references for use by simulator
    def get_addr_refs(
        self, word_addrs, num_addr_bits, num_offset_bits, num_index_bits, num_tag_bits
    ):

        return [
            Reference(
                word_addr, num_addr_bits, num_offset_bits, num_index_bits, num_tag_bits
            )
            for word_addr in word_addrs
        ]

    # Displays details for each address reference, including its hit/miss
    # status
    def display_addr_refs(self, refs, table_width):

        table = Table(num_cols=len(REF_COL_NAMES), width=table_width, alignment="right")
        table.header[:] = REF_COL_NAMES

        for ref in refs:

            if ref.tag is not None:
                ref_tag = ref.tag
            else:
                ref_tag = "n/a"

            if ref.index is not None:
                ref_index = ref.index
            else:
                ref_index = "n/a"

            if ref.offset is not None:
                ref_offset = ref.offset
            else:
                ref_offset = "n/a"

            # Display data for each address as a row in the table
            table.rows.append(
                (
                    ref.word_addr,
                    BinaryAddress.prettify(ref.bin_addr, MIN_BITS_PER_GROUP),
                    BinaryAddress.prettify(ref_tag, MIN_BITS_PER_GROUP),
                    BinaryAddress.prettify(ref_index, MIN_BITS_PER_GROUP),
                    BinaryAddress.prettify(ref_offset, MIN_BITS_PER_GROUP),
                    ref.cache_status,
                )
            )

        print(table)

    # Displays the contents of the given cache as nicely-formatted table
    def display_cache(self, cache, table_width):
        cache_set_names = sorted(cache.keys())
        num_sets = len(cache_set_names)
        num_cols = num_sets if num_sets > 1 else 1

        table = Table(num_cols=num_cols, width=table_width, alignment="center")
        table.title = "L2 Cache" if cache.is_l2 else "L1 Cache"

        # Display set names in table header if cache is not fully associative
        if num_sets > 1:
            table.header[:] = cache_set_names
        else:
            table.header[:] = ["Set"]

        # Find the maximum number of blocks in any set
        max_blocks = max(len(cache[index]) for index in cache_set_names)
        # Add rows for each block position
        for i in range(max_blocks):
            row = []
            for index in cache_set_names:
                blocks = cache[index]
                if i < len(blocks):
                    block_data = ",".join(map(str, blocks[i]["data"]))
                    row.append(block_data)
                else:
                    row.append("")
            table.rows.append(row)

        print(table)

    # Run the entire cache simulation
    def run_simulation(
        self,
        num_blocks_per_set,
        num_words_per_block,
        cache_size,
        replacement_policy,
        num_addr_bits,
        word_addrs,
    ):
        num_blocks = cache_size // num_words_per_block
        num_sets = num_blocks // num_blocks_per_set

        # Ensure that the number of bits used to represent each address is
        # always large enough to represent the largest address
        num_addr_bits = max(num_addr_bits, int(math.log2(max(word_addrs))) + 1)

        num_offset_bits = int(math.log2(num_words_per_block))
        num_index_bits = int(math.log2(num_sets))
        num_tag_bits = num_addr_bits - num_index_bits - num_offset_bits

        refs = self.get_addr_refs(
            word_addrs, num_addr_bits, num_offset_bits, num_index_bits, num_tag_bits
        )

        l1_cache = Cache(num_sets=num_sets, num_index_bits=num_index_bits)
        l2_cache = Cache(num_sets=num_sets, num_index_bits=num_index_bits, is_l2=True)

        total_cycles_with_l2 = l1_cache.read_refs(
            num_blocks_per_set, num_words_per_block, replacement_policy, refs, l2_cache
        )

        # The character-width of all displayed tables
        # Attempt to fit table to terminal width, otherwise use default of 80
        table_width = max(
            (
                shutil.get_terminal_size((DEFAULT_TABLE_WIDTH, None)).columns,
                DEFAULT_TABLE_WIDTH,
            )
        )

        print("Running simulation with L1 and L2 caches...")
        self.display_addr_refs(refs, table_width)
        print()
        self.display_cache(l1_cache, table_width)
        print()
        self.display_cache(l2_cache, table_width)
        print()
        print(f"Total Cycles with L2: {total_cycles_with_l2}")

        # Run the simulation with L1 cache only
        l1_cache_only = Cache(num_sets=num_sets, num_index_bits=num_index_bits)
        total_cycles_with_l1_only = l1_cache_only.read_refs(
            num_blocks_per_set, num_words_per_block, replacement_policy, refs
        )

        print("\nRunning simulation with L1 cache only...")
        self.display_addr_refs(refs, table_width)
        print()
        self.display_cache(l1_cache_only, table_width)
        print()
        print(f"Total Cycles with L1 only: {total_cycles_with_l1_only}")

        print("\nComparison of total cycles:")
        print(f"Total Cycles with L2: {total_cycles_with_l2}")
        print(f"Total Cycles with L1 only: {total_cycles_with_l1_only}")
