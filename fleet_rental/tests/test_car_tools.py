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
class TestCarTools(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.car_tool = cls.env['car.tools'].create({
            'name': 'Jack',
            'price': 50.0,
        })

    def test_car_tool_creation(self):
        """ Test car tool creation """
        self.assertEqual(self.car_tool.name, 'Jack')
        self.assertEqual(self.car_tool.price, 50.0)
