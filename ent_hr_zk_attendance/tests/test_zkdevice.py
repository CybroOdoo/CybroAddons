# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkdevice
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkDevice(TestCase):
    def _assert_wrapper(self, func):
        state = fake_device_state([reply_packet(session_id=10, payload=b"VALUE")])
        result = func(state)
        state.createHeader.assert_called_once()
        self.assertEqual(result, b"VALUE")
        self.assertEqual(state.session_id, 10)
        self.assertEqual(state.zkclient.sent[0][1], state.address)

    def test_zkdevicename(self):
        self._assert_wrapper(zkdevice.zkdevicename)

    def test_zkenabledevice(self):
        self._assert_wrapper(zkdevice.zkenabledevice)

    def test_zkdisabledevice(self):
        self._assert_wrapper(zkdevice.zkdisabledevice)
