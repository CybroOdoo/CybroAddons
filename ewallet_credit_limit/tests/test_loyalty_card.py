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
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestLoyaltyCard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestLoyaltyCard, cls).setUpClass()
        cls.program = cls.env['loyalty.program'].create({
            'name': 'Test E-Wallet Program',
            'program_type': 'ewallet',
            'applies_on': 'future',
            'trigger': 'auto',
        })
        cls.card = cls.env['loyalty.card'].create({
            'program_id': cls.program.id,
            'points': 100.0,
            'limit': 50.0,
            'set_limit': True,
        })

    def test_compute_balance_limit(self):
        """Test that balance_limit_amount is correctly computed to match limit"""
        self.assertEqual(self.card.balance_limit_amount, 50.0)
        self.card.write({'limit': 80.0})
        self.assertEqual(self.card.balance_limit_amount, 80.0)

    def test_check_balance_points_validation(self):
        """Test check_balance_points raises ValidationError if points_display < limit"""
        # Case 1: points_display is less than limit -> ValidationError
        self.card.points_display = "30.00"
        self.card.limit = 50.0
        with self.assertRaises(ValidationError):
            self.card.check_balance_points()

        # Case 2: points_display is greater or equal to limit -> No error
        self.card.points_display = "60.00"
        self.card.limit = 50.0
        # Should execute without raising ValidationError
        self.card.check_balance_points()

    def test_load_pos_data_fields(self):
        """Test _load_pos_data_fields returns the custom ewallet fields"""
        fields = self.env['loyalty.card']._load_pos_data_fields(1)
        self.assertIn('balance_limit_amount', fields)
        self.assertIn('set_limit', fields)
