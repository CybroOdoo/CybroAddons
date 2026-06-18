# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkplatform
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkPlatform(TestCase):
    def test_zkplatform(self):
        state = fake_device_state([reply_packet(session_id=10, payload=b"VALUE")])
        result = zkplatform.zkplatform(state)
        state.createHeader.assert_called_once()
        self.assertEqual(result, b"VALUE")

    def test_zkplatform_version(self):
        state = fake_device_state([reply_packet(session_id=10, payload=b"VALUE")])
        result = zkplatform.zkplatformVersion(state)
        state.createHeader.assert_called_once()
        self.assertEqual(result, b"VALUE")
