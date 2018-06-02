# -*- coding: utf-8 -*-
from unittest import TestCase, skip
import iota
from iotapy import snapshot as ss


def test_dict_diff():
    a = dict(a=1, b=2, c=5)
    b = dict(b=2, c=4, d=3)
    result = ss.dict_diff(a, b)
    assert dict(a=1, c=1) == result


class SnapshotTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snap = ss.Snapshot(verify=False)

    def test_snapshot_init(self):
        assert self.snap.is_consistent()

    def test_snapshot_diff(self):
        snapshot = ss.Snapshot(self.snap.state, 0)
        diff = snapshot.diff(_get_modified_state(snapshot))
        assert 2 == len(diff.keys())

    def test_snapshot_patch(self):
        snapshot = ss.Snapshot(self.snap.state, 0)
        diff = snapshot.diff(_get_modified_state(snapshot))

        new_state = snapshot.patch(diff, 0)
        diff = snapshot.diff(new_state.state)
        self.assertNotEqual(len(diff), 0)
        assert new_state.is_consistent()

    @skip('Take too long time to verify a snapshot')
    def test_snapshot_init_verify(self):
        ss.Snapshot(verify=True)


def _get_modified_state(snapshot):
    h = iota.Hash(
        'PSRQPWWIECDGDDZXHGJNMEVJNSVOSMECPPVRPEVRZFVIZYNNXZ'
        'NTOTJOZNGCZNQVSPXBXTYUJUOXYASLS'
    )
    m = dict(snapshot.state)

    if m:
        k = next(iter(m))
        m[h] = m[k]
        m[k] = 0

    return m
