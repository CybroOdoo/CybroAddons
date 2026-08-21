# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: K Sai Saran Varma (odoo@cybrosys.com)
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
from odoo.fields import Command

class TestPosBookOrder(TransactionCase):

    def setUp(self):
        super(TestPosBookOrder, self).setUp()
        self.partner = self.env['res.partner'].search([], limit=1)
        self.product = self.env['product.product'].search([('sale_ok', '=', True)], limit=1)
        self.tax = self.env['account.tax'].create({
            'name': 'Test Tax',
            'amount': 10,
            'amount_type': 'percent',
        })

    def test_01_book_order_creation_defaults(self):
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.state, 'draft')

    def test_02_book_order_sequence_generation(self):
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertNotEqual(order.name, '/')

    def test_03_book_order_action_confirm(self):
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'pos_order_uid': 'POS/123'
        })
        res = order.action_confirm()
        self.assertEqual(order.state, 'confirmed')
        self.assertEqual(res, 'POS/123')

    def test_04_book_order_create_booked_order(self):
        product_data = {
            'product_id': [self.product.id],
            'qty': [2],
            'price': [100.0],
            'tax_ids': [[self.tax.id]]
        }
        order_name = self.env['book.order'].create_booked_order(
            self.partner.id, '1234567890', 'Test Address', False, False,
            product_data, 'Test Note', '2026-01-01', '2026-01-02', 'POS_123'
        )
        order = self.env['book.order'].search([('name', '=', order_name)])
        self.assertTrue(order)
        self.assertEqual(len(order.book_line_ids), 1)

    def test_05_book_order_all_orders(self):
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'book_line_ids': [Command.create({
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 100.0,
            })]
        })
        orders = self.env['book.order'].all_orders()
        order_ids = [o['id'] for o in orders]
        self.assertIn(order.id, order_ids)

    def test_06_book_order_compute_amount_all(self):
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'book_line_ids': [Command.create({
                'product_id': self.product.id,
                'qty': 2,
                'price_unit': 100.0,
                'tax_ids': [Command.set(self.tax.ids)]
            })]
        })
        self.assertEqual(order.amount_total, 220.0)

    def test_07_book_order_line_compute(self):
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['book.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 2,
            'price_unit': 100.0,
            'discount': 10.0,
        })
        self.assertEqual(line.price_subtotal, 180.0)

    def test_08_book_order_dates_and_phone(self):
        product_data = {
            'product_id': [self.product.id],
            'qty': [1],
            'price': [100.0],
            'tax_ids': [[]]
        }
        order_name = self.env['book.order'].create_booked_order(
            self.partner.id, '1234567890', 'Test', False, False,
            product_data, 'Test Note', '2026-01-01', '2026-01-02', 'POS_123'
        )
        order = self.env['book.order'].search([('name', '=', order_name)])
        self.assertEqual(str(order.pickup_date), '2026-01-01 00:00:00')
        self.assertEqual(str(order.deliver_date), '2026-01-02 00:00:00')
