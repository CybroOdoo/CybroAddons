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

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields


class TestPurchaseRecurringOrders(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Odoo 19 specific partner constraints (autopost_bills)
        cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')
        try:
            cls.env['ir.default'].set('res.partner', 'group_rfq', 'default')
            cls.env['ir.default'].set('res.partner', 'group_on', 'default')
        except Exception:
            pass

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Supplier Partner',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Agreement Product',
            'type': 'consu',
            'list_price': 10.0,
        })

    def test_01_recurring_agreement_creation_defaults(self):
        """Test default values on purchase.recurring.agreement creation."""
        agreement = self.env['purchase.recurring.agreement'].create({
            'name': 'Test Default Agreement',
            'partner_id': self.partner.id,
        })
        self.assertTrue(agreement.number, "Sequence number should be generated automatically.")
        self.assertEqual(agreement.start_date, fields.Date.today(), "Start date should default to today.")
        self.assertEqual(agreement.prolong, 'unlimited', "Prolongation default should be unlimited.")
        self.assertEqual(agreement.state, 'empty', "Initial state should be empty (Without Orders).")

    def test_02_agreement_date_validation(self):
        """Test that ValidationError/Warning is raised if end date is prior to start date."""
        with self.assertRaises(Exception, msg="Should raise exception if end date is before start date"):
            self.env['purchase.recurring.agreement'].create({
                'name': 'Invalid Date Agreement',
                'partner_id': self.partner.id,
                'start_date': fields.Date.today(),
                'end_date': fields.Date.today() - timedelta(days=5),
            })

    def test_03_expiration_date_computes(self):
        """Test the computation of next_expiration_date based on prolongation values."""
        start_date = fields.Date.today()
        # 1. Fixed term
        agreement_fixed = self.env['purchase.recurring.agreement'].create({
            'name': 'Fixed Term',
            'partner_id': self.partner.id,
            'prolong': 'fixed',
            'start_date': start_date,
            'end_date': start_date + timedelta(days=10),
        })
        agreement_fixed._compute_next_expiration_date()
        self.assertEqual(agreement_fixed.next_expiration_date.date(), start_date + timedelta(days=10))

        # 2. Unlimited Term (Days interval)
        agreement_unlimited = self.env['purchase.recurring.agreement'].create({
            'name': 'Unlimited Term',
            'partner_id': self.partner.id,
            'prolong': 'unlimited',
            'start_date': start_date,
            'prolong_interval': 2,
            'prolong_unit': 'months',
        })
        agreement_unlimited._compute_next_expiration_date()
        expected_next = start_date + relativedelta(months=2)
        self.assertEqual(agreement_unlimited.next_expiration_date.date(), expected_next)

    def test_04_action_generate_agreement_from_purchase_order(self):
        """Test generating a recurring agreement directly from a Purchase Order."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 5.0,
                'price_unit': 10.0,
                'name': self.product.name,
                'date_planned': fields.Datetime.now(),
            })]
        })

        action = purchase_order.action_button_generate_agreement()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'purchase.recurring.agreement')

        # Check generated agreement
        agreement = self.env['purchase.recurring.agreement'].search([
            ('partner_id', '=', self.partner.id),
            ('name', '=', purchase_order.name)
        ])
        self.assertTrue(agreement)
        self.assertEqual(len(agreement.agreement_line_ids), 1)
        self.assertEqual(agreement.agreement_line_ids.product_id, self.product)
        self.assertEqual(agreement.agreement_line_ids.quantity, 5.0)

    def test_05_generate_agreement_orders_and_unlink(self):
        """Test generating next planned orders and unlinking draft orders."""
        start_date = fields.Datetime.now()
        agreement = self.env['purchase.recurring.agreement'].create({
            'name': 'Generate Order Test',
            'partner_id': self.partner.id,
            'start_date': start_date,
            'prolong': 'unlimited',
            'agreement_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 10.0,
                'ordering_interval': 1,
                'ordering_unit': 'months',
            })]
        })

        # Generate orders for next year
        agreement.generate_next_orders(years=1, start_date=start_date)

        # Confirm count and state
        self.assertTrue(agreement.order_count > 0, "Orders should be generated.")
        self.assertEqual(agreement.state, 'orders', "State should change to 'orders'.")

        # Verify draft order values
        first_order = agreement.order_ids.sorted('date_order')[0]
        self.assertEqual(first_order.state, 'draft')
        self.assertEqual(first_order.origin, agreement.number)
        self.assertEqual(first_order.from_agreement, True)

        # Test unlinking pending draft/sent orders
        agreement.unlink_orders(start_date)
        self.assertEqual(agreement.order_count, 0, "Draft orders should be unlinked.")

    def test_06_renewal_wizard(self):
        """Test manual renewal wizard functionality."""
        agreement = self.env['purchase.recurring.agreement'].create({
            'name': 'Renewal Agreement',
            'partner_id': self.partner.id,
            'prolong': 'recurrent',
            'start_date': fields.Date.today(),
            'prolong_interval': 1,
            'prolong_unit': 'years',
        })

        renewal_date = fields.Date.today() + relativedelta(years=1)
        
        # Open and trigger Wizard
        wizard = self.env['agreement.renewal'].with_context(active_ids=[agreement.id]).create({
            'date': renewal_date,
            'comments': 'Renewing for another year.'
        })
        wizard.create_renewal()

        # Check updates on agreement
        agreement.read()
        self.assertEqual(agreement.renewal_state, 'renewed')
        self.assertEqual(agreement.last_renovation_date.date(), renewal_date)
        self.assertEqual(len(agreement.renewal_ids), 1)
        self.assertEqual(agreement.renewal_ids.comments, 'Renewing for another year.')
