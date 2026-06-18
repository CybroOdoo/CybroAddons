# -*- coding: utf-8 -*-

from unittest import TestCase

from odoo.addons.ent_hr_zk_attendance.models import zkconst
from odoo.addons.ent_hr_zk_attendance.tests.common import sample_datetime


class TestZkConst(TestCase):
    def test_encode_and_decode_time_round_trip(self):
        moment = sample_datetime()
        encoded = zkconst.encode_time(moment)
        self.assertEqual(zkconst.decode_time(encoded), moment)
