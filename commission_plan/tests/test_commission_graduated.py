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


class TestCommissionGraduated(TransactionCase):

    def setUp(self):
        super(TestCommissionGraduated, self).setUp()
        self.commission = self.env['crm.commission'].create({
            'name': 'Graduated Plan',
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=10),
            'type': 'revenue',
            'revenue_type': 'graduated',
        })
        self.Graduated = self.env['commission.graduated']

    def test_amount_constraints(self):
        """Test amount_to must be greater than amount_from"""
        with self.assertRaises(ValidationError):
            self.Graduated.create({
                'commission_id': self.commission.id,
                'amount_from': 100,
                'amount_to': 50,
            })

    def test_compute_sequence(self):
        """Test sequence computation"""
        rule1 = self.Graduated.create({
            'commission_id': self.commission.id,
            'amount_from': 0,
            'amount_to': 100,
        })
        rule2 = self.Graduated.create({
            'commission_id': self.commission.id,
            'amount_from': 101,
            'amount_to': 200,
        })
        # Sequence should be computed automatically
        self.assertEqual(rule1.sequence, 1)
        self.assertEqual(rule2.sequence, 2)
