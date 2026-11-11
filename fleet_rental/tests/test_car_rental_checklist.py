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
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCarRentalChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.car_tool = cls.env['car.tools'].create({
            'name': 'Jack',
            'price': 50.0,
        })

    def test_onchange_name(self):
        """ Test onchange name for car rental checklist """
        checklist = self.env['car.rental.checklist'].new({
            'name': self.car_tool.id,
        })
        checklist.onchange_name()
        self.assertEqual(checklist.price, 50.0)
