# -*- coding: utf-8 -*-

from struct import pack
from types import SimpleNamespace
from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkattendance, zkconst
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkAttendance(TestCase):
    def test_get_size_attendance_returns_prepared_size(self):
        data = pack("HHHHI", zkconst.CMD_PREPARE_DATA, 0, 0, 0, 512)
        self.assertEqual(zkattendance.getSizeAttendance(SimpleNamespace(data_recv=data)), 512)

    def test_reverse_hex(self):
        self.assertEqual(zkattendance.reverseHex("01020304"), "04030201")

    def test_get_attendance_returns_empty_list_without_prepare_data(self):
        state = fake_device_state([reply_packet(payload=b"")])
        self.assertEqual(zkattendance.zkgetattendance(state), [])

    def test_clear_attendance_returns_payload(self):
        state = fake_device_state([reply_packet(payload=b"CLEARED")])
        self.assertEqual(zkattendance.zkclearattendance(state), b"CLEARED")
