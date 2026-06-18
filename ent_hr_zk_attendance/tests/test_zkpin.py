# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkpin
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkPin(TestCase):
    def test_zkpinwidth(self):
        state = fake_device_state([reply_packet(session_id=10, payload=b"VALUE")])
        result = zkpin.zkpinwidth(state)
        state.createHeader.assert_called_once()
        self.assertEqual(result, b"VALUE")
