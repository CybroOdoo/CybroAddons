# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkconnect
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkConnect(TestCase):
    def test_connect_success(self):
        state = fake_device_state([reply_packet(session_id=9)])
        self.assertTrue(zkconnect.zkconnect(state))
        self.assertEqual(state.session_id, 9)

    def test_connect_failure(self):
        state = fake_device_state([RuntimeError("timeout")])
        self.assertFalse(zkconnect.zkconnect(state))

    def test_disconnect_returns_validity(self):
        state = fake_device_state([reply_packet()])
        self.assertTrue(zkconnect.zkdisconnect(state))
        state.checkValid.assert_called_once()
