"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""
from dataclasses import dataclass
from typing import Tuple, Union

from .. import rlp
from ..base_types import (
    U64,
    U256,
    Bytes,
    Bytes0,
    Bytes32,
    Uint,
    slotted_freezable,
)
from ..exceptions import InvalidBlock
from .fork_types import Address, VersionedHash

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 16
TX_DATA_COST_PER_ZERO = 4
TX_CREATE_COST = 32000
TX_ACCESS_LIST_ADDRESS_COST = 2400
TX_ACCESS_LIST_STORAGE_KEY_COST = 1900


@slotted_freezable
@dataclass
class LegacyTransaction:
    """
    Atomic operation performed on the block chain.
    """

    nonce: U256
    gas_price: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    v: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class AccessListTransaction:
    """
    The transaction type added in EIP-2930 to support access lists.
    """

    chain_id: U64
    nonce: U256
    gas_price: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    y_parity: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class FeeMarketTransaction:
    """
    The transaction type added in EIP-1559.
    """

    chain_id: U64
    nonce: U256
    max_priority_fee_per_gas: Uint
    max_fee_per_gas: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    y_parity: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class BlobTransaction:
    """
    The transaction type added in EIP-4844.
    """

    chain_id: U64
    nonce: U256
    max_priority_fee_per_gas: Uint
    max_fee_per_gas: Uint
    gas: Uint
    to: Address
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    max_fee_per_blob_gas: U256
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    y_parity: U256
    r: U256
    s: U256

@slotted_freezable
@dataclass
class ArbitrumUnsignedTransaction:
    """
    Represents an L1 -> L2 message where the source is the bridge.
    Provides a mechanism for a user on L1 to message a contract on L2 using the bridge for authentication instead of the user's signature.
    The user's from address will be remapped on L2 to distinguish them from a normal L2 caller.
    """
    chain_id: U64
    from_: Address
    nonce: U256

    gas_fee_cap: U256
    gas: Uint
    to: Address
    value: U256
    data: Bytes

@slotted_freezable
@dataclass
class ArbitrumContractTransaction:
    """
    Represents a nonce-less L1 to L2 message where the source is a contract.
    Like `ArbitrumUnsignedTx` but is intended for smart contracts.
    Use the bridge's unique sequential nonce rather than requiring the caller to specify their own.
    """
    chain_id: U64
    request_id: Bytes
    from_: Address

    gas_fee_cap: U256
    gas: Uint
    to: Address
    value: U256
    data: Bytes

@slotted_freezable
@dataclass
class ArbitrumRetryTransaction:
    """
    Represents a special message type for retrying a transaction originates from L2.
    It is scheduled by calls to the redeem method of the ArbRetryableTx precompile.
    The submission_fee_refund goes to refund_to.
    The max_refund is the maximum refund sent to refund_to (the rest goes to from_).
    """
    chain_id: U64
    nonce: U256
    from_: Address

    gas_fee_cap: U256
    gas: Uint
    to: Address
    value: U256
    data: Bytes
    ticket_id: U256
    refund_to: Address
    max_refund: U256
    submission_fee_refund: U256

@slotted_freezable
@dataclass
class ArbitrumSubmitRetryTransaction:
    """
    Represents a special message type for submitting a retryable transaction from L1 bridge.
    It is like ArbitrumRetryTransaction but from the L1 bridge hence nonce is not needed, and request_id is used instead.
    The refund policy is the same as ArbitrumRetryTransaction.
    """
    chain_id: U64
    request_id: Bytes
    from_: Address
    l1_base_fee: U256

    deposit_value: U256
    gas_fee_cap: U256
    gas: Uint
    retry_to: Address
    retry_value: U256
    beneficiary: Address
    max_submission_fee: U256
    fee_refund_address: Address
    retry_data: Bytes

@slotted_freezable
@dataclass
class ArbitrumDepositTransaction:
    """
    Represents a special message type for depositing ether from L1 bridge onto the L2.
    This increases the to's balance by the amount deposited on L1.
    """
    chain_id: U64
    l1_request_id: Bytes
    from_: Address
    to: Address
    value: U256

@slotted_freezable
@dataclass
class ArbitrumInternalTransaction:
    """
    Represents a special message type for internal transaction for ArbOS state upgrade.
    """
    chain_id: U64
    data: Bytes

Transaction = Union[
    LegacyTransaction,
    AccessListTransaction,
    FeeMarketTransaction,
    BlobTransaction,
    ArbitrumUnsignedTransaction,
    ArbitrumContractTransaction,
    ArbitrumRetryTransaction,
    ArbitrumSubmitRetryTransaction,
    ArbitrumDepositTransaction,
    ArbitrumInternalTransaction,
]


def encode_transaction(tx: Transaction) -> Union[LegacyTransaction, Bytes]:
    """
    Encode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, LegacyTransaction):
        return tx
    elif isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(tx)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(tx)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(tx)
    elif isinstance(tx, ArbitrumDepositTransaction):
        return b"\x64" + rlp.encode(tx)
    elif isinstance(tx, ArbitrumUnsignedTransaction):
        return b"\x65" + rlp.encode(tx)
    elif isinstance(tx, ArbitrumContractTransaction):
        return b"\x66" + rlp.encode(tx)
    elif isinstance(tx, ArbitrumRetryTransaction):
        return b"\x68" + rlp.encode(tx)
    elif isinstance(tx, ArbitrumSubmitRetryTransaction):
        return b"\x69" + rlp.encode(tx)
    elif isinstance(tx, ArbitrumInternalTransaction):
        return b"\x6A" + rlp.encode(tx)

    else:
        raise Exception(f"Unable to encode transaction of type {type(tx)}")


def decode_transaction(tx: Union[LegacyTransaction, Bytes]) -> Transaction:
    """
    Decode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, Bytes):
        if tx[0] == 1:
            return rlp.decode_to(AccessListTransaction, tx[1:])
        elif tx[0] == 2:
            return rlp.decode_to(FeeMarketTransaction, tx[1:])
        elif tx[0] == 3:
            return rlp.decode_to(BlobTransaction, tx[1:])
        elif tx[0] == 0x64:
            return rlp.decode_to(ArbitrumDepositTransaction, tx[1:])
        elif tx[0] == 0x65:
            return rlp.decode_to(ArbitrumUnsignedTransaction, tx[1:])
        elif tx[0] == 0x66:
            return rlp.decode_to(ArbitrumContractTransaction, tx[1:])
        elif tx[0] == 0x68:
            return rlp.decode_to(ArbitrumRetryTransaction, tx[1:])
        elif tx[0] == 0x69:
            return rlp.decode_to(ArbitrumSubmitRetryTransaction, tx[1:])
        elif tx[0] == 0x6A:
            return rlp.decode_to(ArbitrumInternalTransaction, tx[1:])
        else:
            raise InvalidBlock
    else:
        return tx
