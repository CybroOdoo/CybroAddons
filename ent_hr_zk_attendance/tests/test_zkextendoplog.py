# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkextendoplog
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkExtendOpLog(TestCase):
    def test_zkextendoplog_updates_counter_and_returns_payload(self):
        data_recv = bytes.fromhex("0000010203040506")
        state = fake_device_state([reply_packet(payload=b"LOG")], data_recv=data_recv)
        result = zkextendoplog.zkextendoplog(state, index=1)
        self.assertEqual(result, b"LOG")
        self.assertEqual(state.counter, 2)
