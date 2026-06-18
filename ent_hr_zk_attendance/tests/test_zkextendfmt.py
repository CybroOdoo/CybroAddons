# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkextendfmt
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkExtendFmt(TestCase):
    def test_zkextendfmt_updates_counter_and_returns_payload(self):
        data_recv = bytes.fromhex("0000010203040506")
        state = fake_device_state([reply_packet(payload=b"FMT")], data_recv=data_recv)
        result = zkextendfmt.zkextendfmt(state)
        self.assertEqual(result, b"FMT")
        self.assertEqual(state.counter, 2)
