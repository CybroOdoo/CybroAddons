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
from odoo import fields

class TestPropertySale(TransactionCase):

    def setUp(self):
        super(TestPropertySale, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Buyer'})
        self.broker = self.env['res.partner'].create({'name': 'Test Broker'})
        self.commission_plan = self.env['property.commission'].create({
            'name': 'Fixed 1000',
            'commission_type': 'fixed',
            'commission': 1000,
        })
        self.property = self.env['property.property'].create({
            'name': 'Test Sale Property',
            'property_type': 'residential',
            'street': 'Test Street',
            'country_id': self.env.ref('base.in').id,
            'sale_rent': 'for_sale',
            'unit_price': 50000,
            'state': 'available',
        })
        # Ensure accounting setup
        self.income_account = self.env['account.account'].create({
            'name': 'Income Account',
            'code': 'INC001',
            'account_type': 'income',
            'company_ids': [fields.Command.set(self.env.company.ids)],
        })
        self.expense_account = self.env['account.account'].create({
            'name': 'Expense Account',
            'code': 'EXP001',
            'account_type': 'expense',
            'company_ids': [fields.Command.set(self.env.company.ids)],
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'code': 'SALE',
            'type': 'sale',
            'company_id': self.env.company.id,
        })
        self.purchase_journal = self.env['account.journal'].create({
            'name': 'Purchase Journal',
            'code': 'PURC',
            'type': 'purchase',
            'company_id': self.env.company.id,
        })
        self.sale = self.env['property.sale'].create({
            'property_id': self.property.id,
            'partner_id': self.partner.id,
            'any_broker': True,
            'broker_id': self.broker.id,
            'commission_plan_id': self.commission_plan.id,
        })

    def test_sale_creation(self):
        """Test sequence generation on creation"""
        self.assertNotEqual(self.sale.name, 'New')

    def test_compute_commission(self):
        """Test commission calculation"""
        self.sale._compute_commission_and_commission_type()
        self.assertEqual(self.sale.commission, 1000)
        
        # Test percentage
        self.commission_plan.commission_type = 'percentage'
        self.commission_plan.commission = 10
        self.sale._compute_commission_and_commission_type()
        self.assertEqual(self.sale.commission, 5000) # 10% of 50000

    def test_action_confirm(self):
        """Test sale confirmation and blacklisted check"""
        # Test success
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'confirm')
        self.assertEqual(self.property.state, 'sold')
        self.assertEqual(self.property.sale_id.id, self.sale.id)

        # Test blacklisted
        self.partner.blacklisted = True
        sale2 = self.env['property.sale'].create({
            'property_id': self.property.id,
            'partner_id': self.partner.id,
        })
        with self.assertRaises(ValidationError):
            sale2.action_confirm()

    def test_create_invoice_action(self):
        """Test create_invoice action structure"""
        action = self.sale.create_invoice()
        self.assertTrue(self.sale.invoiced)
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['context']['default_move_type'], 'out_invoice')

    def test_commission_bill_action(self):
        """Test commission_bill action structure"""
        action = self.sale.commission_bill()
        self.assertTrue(self.sale.billed)
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['context']['default_move_type'], 'in_invoice')
