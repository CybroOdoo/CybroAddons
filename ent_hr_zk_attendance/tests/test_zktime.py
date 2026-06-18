# -*- coding: utf-8 -*-

from struct import pack
from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkconst, zktime
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet, sample_datetime


class TestZkTime(TestCase):
    def test_reverse_hex(self):
        self.assertEqual(zktime.reverseHex("01020304"), "04030201")

    def test_set_time(self):
        dt = sample_datetime()
        packed_time = pack("I", zkconst.encode_time(dt))
        state = fake_device_state([reply_packet(session_id=8, payload=packed_time)])
        self.assertEqual(zktime.zksettime(state, dt), packed_time)

    def test_get_time(self):
        dt = sample_datetime()
        packed_time = pack("I", zkconst.encode_time(dt))
        state = fake_device_state([reply_packet(session_id=8, payload=packed_time)])
        self.assertEqual(zktime.zkgettime(state), dt)
