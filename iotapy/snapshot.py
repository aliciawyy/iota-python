# -*- coding: utf-8 -*-
import iota
from typing import List
from pkg_resources import resource_string


def dict_diff(dict1, dict2):
    return {
        k: v - dict2.get(k, 0) for k, v in dict1.items()
        if v - dict2.get(k, 0) != 0
    }


HASH_LENGTH = 243
CURL_HASH_LENGTH = HASH_LENGTH * 3


class ISS:
    # Initial Snapshot Signature
    NUMBER_OF_FRAGMENT_CHUNKS = 27
    MIN_TRYTE_VALUE = -13


    @classmethod
    def address(self, sponge_type, digests: List[int]):
        if not digests or len(digests) % HASH_LENGTH != 0:
            raise ValueError('Invalid digests length: %d' % len(digests))

        trits = []
        hash = sponge_type()
        hash.absorb(digests)
        hash.squeeze(trits)

        return trits

    @classmethod
    def digest(self, sponge_type, normalized_bundle_fragment: List[int], signature_fragment: iota.TryteString):
        hash = sponge_type()
        trits = signature_fragment.as_trits()
        d = []

        for j in range(self.NUMBER_OF_FRAGMENT_CHUNKS):
            for k in range(normalized_bundle_fragment[j] - self.MIN_TRYTE_VALUE):
                hash.reset()
                hash.absorb(trits, j * HASH_LENGTH, (j + 1) * HASH_LENGTH)
                hash.squeeze(trits, j * HASH_LENGTH)

        hash.reset()
        hash.absorb(trits)
        hash.squeeze(d)

        return d

    @classmethod
    def get_merkle_root(self, sponge_type, hash: List[int], trits: List[int],
                        offset: int, index: int, length: int):
        curl = sponge_type()
        for i in range(length):
            curl.reset()
            if index & 1 == 0:
                curl.absorb(hash)
                curl.absorb(trits, offset + i * HASH_LENGTH, offset + (i + 1) * HASH_LENGTH)
            else:
                curl.absorb(trits, offset + i * HASH_LENGTH, offset + (i + 1) * HASH_LENGTH)
                curl.absorb(hash)
            curl.squeeze(hash)
            index >>= 1

        if index:
            return [0] * HASH_LENGTH
        return hash


class Snapshot:
    SNAPSHOT_PUBKEY = (
        'TTXJUGKTNPOOEXSTQVVACENJOQUROXYKDRCVK9LHUXILCLA'
        'BLGJTIPNF9REWHOIMEUKWQLUOKD9CZUYAC'
    )
    SNAPSHOT_PUBKEY_DEPTH = 6
    SNAPSHOT_INDEX = 1
    MAX_SUPPLY = (3 ** 33 - 1) // 2

    def __init__(self, state=None, index=0, verify=False):
        self.state = state or self.get_state_from_snapshot(verify)
        self.index = index

    def get_state_from_snapshot(self, verify):
        pkg = "iotapy.resources"
        snapshot_data = resource_string(pkg, 'Snapshot.txt').splitlines()
        snapshot_sig = resource_string(pkg, 'Snapshot.sig').splitlines()
        state = {}

        # Init snapshot
        curl = iota.crypto.kerl.Kerl()
        for line in snapshot_data:
            trits = iota.TryteString.from_bytes(line).as_trits()

            if verify:
                curl.absorb(trits)

            key, value = line.split(b';')
            state[iota.Hash(key)] = int(value)

        if not self.is_consistent(state):
            raise ValueError('Snapshot total supply or address value is bad')

        if not verify:
            return state

        trits = []
        curl.squeeze(trits)

        mode = iota.crypto.Curl
        bundle_hash = iota.BundleHash.from_trits(trits)
        bundles = iota.crypto.signing.normalize(bundle_hash)

        digests = []
        for i, bundle in enumerate(bundles):
            digests.extend(ISS.digest(mode, bundle, iota.TryteString(snapshot_sig[i])))

        root = ISS.get_merkle_root(mode, ISS.address(mode, digests),
                                   iota.TryteString(snapshot_sig[-1]).as_trits(),
                                   0, self.SNAPSHOT_INDEX, self.SNAPSHOT_PUBKEY_DEPTH)

        if root != iota.TryteString(self.SNAPSHOT_PUBKEY).as_trits():
            raise ValueError('Snapshot signature failed')
        return state

    def is_consistent(self, state=None):
        state = state or self.state
        state_values = state.values()
        return not (sum(state_values) != self.MAX_SUPPLY or
                    any(i < 0 for i in state_values))

    def diff(self, other_state):
        return dict_diff(other_state, self.state)

    def patch(self, other_state, index):
        state = {
            k: self.state.get(k, 0) + other_state.get(k, 0)
            for k in set(self.state).union(other_state)
            if self.state.get(k, 0) + other_state.get(k, 0) > 0
        }
        return Snapshot(state, index)
