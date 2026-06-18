# -*- coding: utf-8 -*-

from struct import pack
from types import SimpleNamespace
from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkconst, zkuser
from odoo.addons.ent_hr_zk_attendance.tests.common import fake_device_state, reply_packet


class TestZkUser(TestCase):
    def test_get_size_user(self):
        data = pack("HHHHI", zkconst.CMD_PREPARE_DATA, 0, 0, 0, 256)
        self.assertEqual(zkuser.getSizeUser(SimpleNamespace(data_recv=data)), 256)

    def test_set_user(self):
        state = fake_device_state([reply_packet(payload=b"OK")])
        self.assertEqual(zkuser.zksetuser(state, 1, "10", "User", "pass", 0), b"OK")

    def test_get_user_empty_response(self):
        state = fake_device_state([reply_packet(payload=b"")])
        self.assertEqual(zkuser.zkgetuser(state), {})

    def test_clear_user(self):
        state = fake_device_state([reply_packet(payload=b"CLEAR")])
        self.assertEqual(zkuser.zkclearuser(state), b"CLEAR")

    def test_clear_admin(self):
        state = fake_device_state([reply_packet(payload=b"ADMIN")])
        self.assertEqual(zkuser.zkclearadmin(state), b"ADMIN")
