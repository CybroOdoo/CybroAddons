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

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import timedelta


class TestCrmCommission(TransactionCase):
    """Test cases for crm_kit commission logic."""

    @classmethod
    def setUpClass(cls):
        super(TestCrmCommission, cls).setUpClass()
        cls.team = cls.env['crm.team'].create({'name': 'Sales Team 1'})
        cls.user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_crm_kit',
            'email': 'test@example.com',
        })
        cls.category = cls.env['product.category'].create({'name': 'Test Category'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'categ_id': cls.category.id,
        })
        cls.commission_revenue = cls.env['crm.commission'].create({
            'name': 'Revenue Commission',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today() + timedelta(days=30),
            'type': 'revenue',
            'team_id': cls.team.id,
            'user_id': cls.user.id,
        })
        cls.commission_product = cls.env['crm.commission'].create({
            'name': 'Product Commission',
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today() + timedelta(days=30),
            'type': 'product',
            'team_id': cls.team.id,
            'user_id': cls.user.id,
        })

    def test_check_date_constraint(self):
        """Test validation error for invalid dates."""
        with self.assertRaises(ValidationError):
            self.env['crm.commission'].create({
                'name': 'Invalid Date Commission',
                'date_from': fields.Date.today(),
                'date_to': fields.Date.today() - timedelta(days=30),
                'type': 'product',
            })

    def test_onchange_type(self):
        """Test onchange method for commission type."""
        commission = self.env['crm.commission'].new({
            'name': 'Test',
            'type': 'product',
            'straight_commission_rate': 10.0,
            'revenue_type': 'straight',
        })
        commission._onchange_type()
        self.assertFalse(commission.revenue_type)
        self.assertFalse(commission.straight_commission_rate)

    def test_commission_graduated_amounts(self):
        """Test validation error for invalid amounts in graduated commission."""
        with self.assertRaises(ValidationError):
            self.env['commission.graduated'].create({
                'commission_id': self.commission_revenue.id,
                'amount_from': 100,
                'amount_to': 50,
            })

    def test_commission_graduated_sequence(self):
        """Test sequence computation for graduated commission rules."""
        grad1 = self.env['commission.graduated'].create({
            'commission_id': self.commission_revenue.id,
            'amount_from': 0,
            'amount_to': 100,
            'graduated_commission_rate': 5,
        })
        grad2 = self.env['commission.graduated'].create({
            'commission_id': self.commission_revenue.id,
            'amount_from': 100,
            'amount_to': 200,
            'graduated_commission_rate': 10,
        })
        self.assertEqual(grad1.sequence, 1)
        self.assertEqual(grad2.sequence, 2)
