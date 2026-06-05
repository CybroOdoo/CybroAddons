# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPosOrder, cls).setUpClass()
        cls.program = cls.env['loyalty.program'].create({
            'name': 'Test E-Wallet Program',
            'program_type': 'ewallet',
            'applies_on': 'future',
            'trigger': 'auto',
        })
        cls.card = cls.env['loyalty.card'].create({
            'program_id': cls.program.id,
            'points': 100.0,
            'limit': 100.0,
            'set_limit': True,
        })

    def test_set_remaining_balance(self):
        """Test that set_remaining_balance correctly deducts the point cost from the coupon"""
        self.assertEqual(self.card.balance_limit_amount, 100.0)

        # Simulate data structure passed from POS Frontend
        data = [{
            'coupon_id': self.card.id,
            'point_cost': 35.0,
        }]

        result = self.env['pos.order'].set_remaining_balance(data)
        self.assertTrue(result)
        self.assertEqual(self.card.balance_limit_amount, 65.0)
