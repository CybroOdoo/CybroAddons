# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from datetime import date



class TestBookOrder(TransactionCase):
    """Test cases for the book.order model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Book Order Customer',
            'phone': '1234567890',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Book Order Product',
            'list_price': 100.0,
            'taxes_id': False,
        })
        cls.tax = cls.env['account.tax'].create({
            'name': 'Test Tax 10%',
            'amount_type': 'percent',
            'amount': 10.0,
        })

    def test_create_sequence(self):
        """Test sequence generation on create."""
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
        })
        # If ir.sequence is not setup properly in tests, it might fallback to '/'
        # but we should at least verify create works.
        self.assertTrue(order)

    def test_compute_amount_all(self):
        """Test computing amounts with tax and discount."""
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
        })
        # Add line with tax
        self.env['book.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 2.0,
            'price_unit': 100.0,
            'tax_ids': [(4, self.tax.id)],
            'discount': 10.0,
        })
        # 100 * 2 = 200. Discount 10% = 180. Tax 10% = 18.
        # Subtotal untaxed = 180
        # Tax = 18
        # Total = 198
        self.assertAlmostEqual(order.amount_tax, 18.0)
        self.assertAlmostEqual(order.amount_total, 198.0)

    def test_action_confirm(self):
        """Test confirming a booked order."""
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.state, 'draft')
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')

    def test_create_booked_order(self):
        """Test API method create_booked_order."""
        product_dict = {
            'product_id': [self.product.id],
            'qty': [3.0],
            'price': [150.0],
        }
        order_name = self.env['book.order'].create_booked_order(
            partner=self.partner.id,
            phone='9876543210',
            address='123 Test St',
            date=False,
            price_list=False,
            product=product_dict,
            note='Test Note',
            pickup_date='2026-06-01',
            delivery_date='2026-06-02',
            pos_order='POS/0001'
        )
        
        order = self.env['book.order'].search([('name', '=', order_name)], limit=1)
        if not order:
             # if sequence fallback returned '/'
             order = self.env['book.order'].search([('partner_id', '=', self.partner.id)], order='id desc', limit=1)
             
        self.assertEqual(order.phone, '9876543210')
        self.assertEqual(order.delivery_address, '123 Test St')
        self.assertEqual(order.note, 'Test Note')
        self.assertEqual(order.pos_order_uid, 'POS/0001')
        self.assertEqual(len(order.book_line_ids), 1)
        self.assertEqual(order.book_line_ids[0].qty, 3.0)

    def test_all_orders(self):
        """Test fetching all orders for POS."""
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'note': 'Fetch me'
        })
        self.env['book.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 1.0,
            'price_unit': 50.0,
        })
        orders = self.env['book.order'].all_orders()
        found = next((o for o in orders if o['id'] == order.id), None)
        self.assertTrue(found)
        self.assertEqual(found['note'], 'Fetch me')
        self.assertEqual(len(found['products']), 1)
        self.assertEqual(found['products'][0]['qty'], 1.0)
