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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestCrmCommission(TransactionCase):

    def setUp(self):
        super(TestCrmCommission, self).setUp()
        self.CommissionPlan = self.env['crm.commission']

    def test_date_constraints(self):
        """Test that date_to cannot be earlier than date_from"""
        with self.assertRaises(ValidationError):
            self.CommissionPlan.create({
                'name': 'Test Plan',
                'date_from': date.today(),
                'date_to': date.today() - timedelta(days=1),
                'type': 'product',
            })

    def test_onchange_type(self):
        """Test onchange clears respective fields based on plan type"""
        plan = self.CommissionPlan.create({
            'name': 'Test Plan 2',
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=5),
            'type': 'product',
            'revenue_type': 'graduated',
            'straight_commission_rate': 10.0,
        })
        
        # Change to revenue, should clear product lines
        plan.type = 'revenue'
        plan._onchange_type()
        self.assertEqual(len(plan.product_comm_ids), 0)
        
        # Change to product, should clear revenue fields
        plan.type = 'product'
        plan._onchange_type()
        self.assertFalse(plan.revenue_type)
        self.assertFalse(plan.straight_commission_rate)
        self.assertEqual(len(plan.revenue_grd_comm_ids), 0)
