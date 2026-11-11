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
from odoo.tests import tagged

from .common import SalonCommon


@tagged('post_install', '-at_install')
class TestResConfigSettings(SalonCommon):

    def test_defaults_reflect_current_flags(self):
        self.chair.active_booking_chairs = True
        sunday = self.holiday_sunday
        settings = self.env['res.config.settings'].create({})
        self.assertIn(self.chair, settings.salon_booking_chair_ids)
        self.assertNotIn(self.chair2, settings.salon_booking_chair_ids)
        self.assertIn(sunday, settings.salon_holiday_ids)

    def test_helper_methods(self):
        self.chair.active_booking_chairs = True
        settings = self.env['res.config.settings']
        self.assertIn(self.chair, settings.booking_chairs())
        self.assertNotIn(self.chair2, settings.booking_chairs())
        holidays = settings.return_holidays()
        self.assertTrue(all(holidays.mapped('holiday')))

    def test_execute_updates_flags(self):
        monday = self.holiday_monday
        sunday = self.holiday_sunday
        settings = self.env['res.config.settings'].create({
            'salon_booking_chair_ids': [(6, 0, [self.chair.id])],
            'salon_holiday_ids': [(6, 0, [monday.id])],
        })
        settings.execute()
        self.assertTrue(self.chair.active_booking_chairs)
        self.assertFalse(self.chair2.active_booking_chairs)
        self.assertTrue(monday.holiday)
        self.assertFalse(sunday.holiday)

    def test_execute_can_deactivate_chairs(self):
        self.chair.active_booking_chairs = True
        settings = self.env['res.config.settings'].create({
            'salon_booking_chair_ids': [(5, 0, 0)],
            'salon_holiday_ids': [(5, 0, 0)],
        })
        settings.execute()
        self.assertFalse(self.chair.active_booking_chairs)
        self.assertFalse(self.env['salon.holiday'].search(
            [('holiday', '=', True)]))
