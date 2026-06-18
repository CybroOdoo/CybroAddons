# -*- coding: utf-8 -*-

from struct import pack
from unittest import TestCase
from unittest.mock import patch

from odoo.addons.ent_hr_zk_attendance.models import zklib
from odoo.addons.ent_hr_zk_attendance.models.zkconst import CMD_ACK_OK


class TestZkLib(TestCase):
    def test_create_checksum_returns_two_bytes(self):
        lib = zklib.ZKLib("127.0.0.1", 4370)
        checksum = lib.createChkSum((1, 2, 3, 4))
        self.assertEqual(len(checksum), 2)

    def test_create_header_accepts_text_and_bytes_payloads(self):
        lib = zklib.ZKLib("127.0.0.1", 4370)
        header_text = lib.createHeader(1, 0, 2, 3, "ping")
        header_bytes = lib.createHeader(1, 0, 2, 3, b"pong")

        self.assertTrue(header_text.endswith(b"ping"))
        self.assertTrue(header_bytes.endswith(b"pong"))

    def test_check_valid_recognizes_ack_ok(self):
        lib = zklib.ZKLib("127.0.0.1", 4370)
        reply = pack("HHHH", CMD_ACK_OK, 0, 0, 0)
        self.assertTrue(lib.checkValid(reply))
        self.assertFalse(lib.checkValid(pack("HHHH", 999, 0, 0, 0)))

    def test_delegated_methods_call_helper_functions(self):
        lib = zklib.ZKLib("127.0.0.1", 4370)
        delegates = [
            ("connect", "zkconnect"),
            ("disconnect", "zkdisconnect"),
            ("version", "zkversion"),
            ("osversion", "zkos"),
            ("extendFormat", "zkextendfmt"),
            ("platform", "zkplatform"),
            ("fmVersion", "zkplatformVersion"),
            ("workCode", "zkworkcode"),
            ("ssr", "zkssr"),
            ("pinWidth", "zkpinwidth"),
            ("faceFunctionOn", "zkfaceon"),
            ("serialNumber", "zkserialnumber"),
            ("deviceName", "zkdevicename"),
            ("disableDevice", "zkdisabledevice"),
            ("enableDevice", "zkenabledevice"),
            ("getUser", "zkgetuser"),
            ("clearUser", "zkclearuser"),
            ("clearAdmin", "zkclearadmin"),
            ("getAttendance", "zkgetattendance"),
            ("clearAttendance", "zkclearattendance"),
            ("getTime", "zkgettime"),
        ]
        for method_name, helper_name in delegates:
            with self.subTest(method=method_name), patch.object(zklib, helper_name, return_value=method_name) as helper:
                self.assertEqual(getattr(lib, method_name)(), method_name)
                helper.assert_called_once_with(lib)

    def test_methods_with_arguments_delegate_arguments(self):
        lib = zklib.ZKLib("127.0.0.1", 4370)
        with patch.object(zklib, "zkextendoplog", return_value="ok") as helper:
            self.assertEqual(lib.extendOPLog(2), "ok")
            helper.assert_called_once_with(lib, 2)

        with patch.object(zklib, "zksetuser", return_value="ok") as helper:
            self.assertEqual(lib.setUser(1, "u1", "Name", "pwd", 0), "ok")
            helper.assert_called_once_with(lib, 1, "u1", "Name", "pwd", 0)

        with patch.object(zklib, "zksettime", return_value="ok") as helper:
            self.assertEqual(lib.setTime("time"), "ok")
            helper.assert_called_once_with(lib, "time")
