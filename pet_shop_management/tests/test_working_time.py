# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import date, timedelta
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestWorkingTime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sitter = cls.env['hr.employee'].create({
            'name': 'Taylor Walker',
            'is_walker_sitters': True,
        })

    def test_01_working_time_and_hours(self):
        """ Test working.time and related working.hours lines """
        today = date.today()
        shift = self.env['working.time'].create({
            'name': 'Morning Shift',
            'working_time': 8.0,
            'avg_working_hours': '8 Hours',
            'working_hours': [Command.create({
                'name': self.sitter.id,
                'day': 'Monday',
                'start_date': today,
                'end_date': today + timedelta(days=7),
            })],
        })

        self.assertTrue(shift.exists())
        self.assertEqual(shift.name, 'Morning Shift')
        self.assertEqual(shift.working_time, 8.0)
        self.assertEqual(len(shift.working_hours), 1)

        hour_line = shift.working_hours[0]
        self.assertEqual(hour_line.name, self.sitter)
        self.assertEqual(hour_line.day, 'Monday')
        self.assertEqual(hour_line.start_date, today)
        self.assertEqual(hour_line.end_date, today + timedelta(days=7))
