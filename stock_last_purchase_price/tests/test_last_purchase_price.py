# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestLastPurchasePrice(AccountTestInvoicingCommon):
    """ Tests for the 'Last Purchase Price' costing method """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.partner_a
        cls.category_last = cls.env['product.category'].create({
            'name': 'Last Price Category',
            'property_cost_method': 'last',
        })
        cls.product = cls._make_last_product('Last Price Product',
                                          cls.category_last)

    @classmethod
    def _make_last_product(cls, name, category):
        template = cls.env['product.template'].create({
            'name': name,
            'type': 'consu',
            'is_storable': True,
            'categ_id': category.id,
            'standard_price': 5.0,
        })
        return template.product_variant_id

    def _create_purchase(self, price, date_order=None, qty=5.0):
        order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'date_order': date_order or fields.Datetime.now(),
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_qty': qty,
                'price_unit': price,
            })],
        })
        order.button_confirm()
        return order

    def _receive(self, order):
        picking = order.picking_ids
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.button_validate()
        return picking

    def test_selection_is_added(self):
        """ The 'last' option is available on every costing field """
        for model in ('product.category', 'product.template',
                      'res.company', 'stock.quant'):
            field_name = ('property_cost_method'
                          if model == 'product.category' else 'cost_method')
            selection = dict(
                self.env[model]._fields[field_name]._description_selection(
                    self.env))
            self.assertIn('last', selection, f"Missing on {model}")
            self.assertEqual(selection['last'], 'Last Purchase Price')

    def test_product_uses_last_cost_method(self):
        """ A product follows the costing method of its category """
        self.assertEqual(self.product.cost_method, 'last')

    def test_cost_from_purchase_order_line(self):
        """ Cost is taken from the last confirmed purchase order line """
        self._create_purchase(10.0)
        self.product._update_standard_price()
        self.assertAlmostEqual(self.product.standard_price, 10.0)

    def test_latest_purchase_order_wins(self):
        """ The most recent purchase order sets the cost """
        self._create_purchase(
            10.0, fields.Datetime.subtract(fields.Datetime.now(), days=5))
        self._create_purchase(12.0, fields.Datetime.now())
        self.product._update_standard_price()
        self.assertAlmostEqual(self.product.standard_price, 12.0)

    def test_posted_vendor_bill_price_preferred(self):
        """ A posted vendor bill price overrides the purchase order price """
        order = self._create_purchase(10.0)
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.vendor.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 5.0,
                'price_unit': 11.0,
                'purchase_line_id': order.order_line.id,
                'account_id': self.company_data[
                    'default_account_expense'].id,
            })],
        })
        bill.action_post()
        self.assertEqual(order.invoice_ids, bill)
        self.product._update_standard_price()
        self.assertAlmostEqual(self.product.standard_price, 11.0)

    def test_draft_purchase_order_is_ignored(self):
        """ Only confirmed purchase orders change the cost """
        self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_qty': 5.0,
                'price_unit': 99.0,
            })],
        })
        self.product._update_standard_price()
        self.assertAlmostEqual(self.product.standard_price, 5.0)

    def test_no_purchase_keeps_cost(self):
        """ Without any purchase the cost is left unchanged """
        self.product._update_standard_price()
        self.assertAlmostEqual(self.product.standard_price, 5.0)

    def test_standard_cost_is_untouched(self):
        """ Products using the standard method keep their cost """
        category = self.env['product.category'].create({
            'name': 'Standard Category',
            'property_cost_method': 'standard',
        })
        product = self._make_last_product('Standard Product', category)
        product._update_standard_price()
        self.assertAlmostEqual(product.standard_price, 5.0)

    def test_fifo_without_stock(self):
        """ The FIFO branch still works and gives a zero cost without stock """
        category = self.env['product.category'].create({
            'name': 'FIFO Category',
            'property_cost_method': 'fifo',
        })
        product = self._make_last_product('FIFO Product', category)
        product._update_standard_price()
        self.assertAlmostEqual(product.standard_price, 0.0)

    def test_remaining_value_of_received_move(self):
        """ The remaining value of a receipt follows the remaining quantity """
        order = self._create_purchase(10.0)
        picking = self._receive(order)
        self.assertEqual(picking.state, 'done')
        move = picking.move_ids
        self.assertTrue(move.is_in)
        expected = move.value * move.remaining_qty / move.quantity
        self.assertAlmostEqual(move.remaining_value, expected)

    def test_avco_report_view_exists(self):
        """ The inventory valuation report view is rebuilt on install """
        self.env.cr.execute("SELECT to_regclass('stock_avco_report')")
        self.assertTrue(self.env.cr.fetchone()[0])
        self.env['stock.avco.report'].init()
