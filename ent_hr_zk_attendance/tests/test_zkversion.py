# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkversion
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkVersion(TestCase):
    def test_zkversion(self):
        state = fake_device_state([reply_packet(session_id=10, payload=b"VALUE")])
        result = zkversion.zkversion(state)
        state.createHeader.assert_called_once()
        self.assertEqual(result, b"VALUE")

    def test_zkversion_returns_false_on_recv_error(self):
        state = fake_device_state([RuntimeError("timeout")])
        self.assertFalse(zkversion.zkversion(state))
