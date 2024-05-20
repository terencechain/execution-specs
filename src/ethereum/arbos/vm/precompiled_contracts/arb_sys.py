"""
ArbOS Sys PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `ArbSys` precompiled contract.
"""

from ethereum.base_types import (
    Uint,
    U256,
)

from ...vm import Evm


# Returns the current L2 block number
def arb_block_number(evm: Evm) -> Uint:
    return evm.env.number


# Returns the L2 block hash if sufficiently enough.
def arb_block_hash(evm: Evm, block_number: int) -> bytes:
    current_block_number = evm.env.number
    if block_number >= current_block_number or block_number < current_block_number - 256:
        raise ValueError("Invalid block number")

    return evm.env.block_hash(block_number)


# Returns the chain ID.
def arb_chain_id(evm: Evm) -> U256:
    return evm.env.chain_id

# Returns the ArbOS version.
def arb_version(evm: Evm) -> U256:
    return evm.env.arb_version