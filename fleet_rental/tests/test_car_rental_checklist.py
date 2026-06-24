# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase

class TestCarRentalChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCarRentalChecklist, cls).setUpClass()
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
