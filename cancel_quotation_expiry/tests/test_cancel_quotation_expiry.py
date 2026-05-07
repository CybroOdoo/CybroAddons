# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from datetime import date, timedelta
from odoo.tests import common


class TestCancelQuotationExpiry(common.TransactionCase):
    """Test cases for checking the automatic cancellation of expired
    quotations."""

    @classmethod
    def setUpClass(cls):
        super(TestCancelQuotationExpiry, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product'
        })

    def test_cancel_expired_quotation_logic(self):
        """Test the cancel_expired_quotation method for all possible states and scenarios."""
        
        # 1. Expired Quotation in 'draft' state
        expired_draft_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
            'validity_date': date.today() - timedelta(days=1),
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
            })],
        })

        # 2. Expired Quotation in 'sent' state
        expired_sent_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sent',
            'validity_date': date.today() - timedelta(days=1),
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
            })],
        })

        # 3. Valid Quotation (validity date is tomorrow)
        valid_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
            'validity_date': date.today() + timedelta(days=1),
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
            })],
        })

        # 4. No Validity Date
        no_date_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
            })],
        })

        # 5. Expired Order already in 'sale' state (should NOT be cancelled)
        expired_sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'sale',
            'validity_date': date.today() - timedelta(days=1),
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
            })],
        })

        # Trigger the cancellation logic
        self.env['sale.order'].cancel_expired_quotation()

        # Assertions
        self.assertEqual(expired_draft_order.state, 'cancel',
                         "Expired 'draft' quotation should be cancelled.")
        self.assertEqual(expired_sent_order.state, 'cancel',
                         "Expired 'sent' quotation should be cancelled.")
        self.assertEqual(valid_order.state, 'draft',
                         "Valid quotation should still be in 'draft' state.")
        self.assertEqual(no_date_order.state, 'draft',
                         "Quotation without validity date should still be in 'draft' state.")
        self.assertEqual(expired_sale_order.state, 'sale',
                         "Confirmed sale orders should not be cancelled even if expired.")
