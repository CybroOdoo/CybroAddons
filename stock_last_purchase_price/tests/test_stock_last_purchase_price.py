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

from odoo.tests.common import TransactionCase, tagged
from odoo import fields, models


@tagged('post_install', '-at_install')
class TestStockLastPurchasePrice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create partner/vendor
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Supplier Last Price',
        })

        # Create product category with 'last' cost method
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category Last Price',
            'property_cost_method': 'last',
            'property_valuation': 'real_time',
        })

        # Create product with category
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product Last Price',
            'categ_id': cls.category.id,
            'type': 'consu',
            'is_storable': True,
        })

    def test_01_configuration_selection(self):
        """ Test selection options for cost method """
        # Verify 'last' is in product category property_cost_method selection list
        categ_selection = self.env['product.category']._fields['property_cost_method'].selection
        self.assertIn(('last', 'Last Purchase Price'), categ_selection)

        # Verify 'last' is in product template cost_method selection list
        tmpl_selection = self.env['product.template']._fields['cost_method'].selection
        self.assertIn(('last', 'Last Purchase Price'), tmpl_selection)

        # Verify 'last' is in company cost_method selection list
        company_selection = self.env['res.company']._fields['cost_method'].selection
        self.assertIn(('last', 'Last Purchase Price'), company_selection)

    def test_02_update_standard_price_no_po(self):
        """ Test standard price update when no purchase order exists """
        self.assertEqual(self.product.standard_price, 0.0)
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 0.0)

    def test_03_update_standard_price_po_only(self):
        """ Test standard price update when PO exists but no vendor bill """
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_qty': 10.0,
                    'price_unit': 100.0,
                    'date_planned': fields.Datetime.now(),
                })
            ]
        })
        # Verify price before confirmation is unchanged (PO is in 'draft' or 'sent')
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 0.0)

        # Confirm the purchase order (sets state to 'purchase')
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')

        # Update standard price and verify it uses the PO unit price
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 100.0)

    def test_04_update_standard_price_with_posted_bill(self):
        """ Test standard price update when PO and posted vendor bill exist """
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_qty': 10.0,
                    'price_unit': 100.0,
                    'date_planned': fields.Datetime.now(),
                })
            ]
        })
        po.button_confirm()

        # Create draft vendor bill
        action = po.action_create_invoice()
        bill = po.invoice_ids or self.env['account.move'].browse(action.get('res_id'))
        self.assertTrue(bill)

        # Verify the standard price uses PO price since vendor bill is draft (not posted)
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 100.0)

        # Update price on bill line to 110.0
        bill.invoice_line_ids.filtered(lambda l: l.product_id == self.product).write({
            'price_unit': 110.0
        })

        # Set invoice date and post the bill
        bill.invoice_date = fields.Date.today()
        bill.action_post()
        self.assertEqual(bill.state, 'posted')

        # Verify standard price uses the vendor bill price
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 110.0)

    def test_05_update_standard_price_multiple_pos(self):
        """ Test standard price updates to the latest confirmed PO price """
        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': fields.Datetime.now(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_qty': 5.0,
                    'price_unit': 80.0,
                    'date_planned': fields.Datetime.now(),
                })
            ]
        })
        po1.button_confirm()

        # Update price to verify it tracks po1
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 80.0)

        # Create a second PO with a later date_order
        po2 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': fields.Datetime.now(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_qty': 5.0,
                    'price_unit': 120.0,
                    'date_planned': fields.Datetime.now(),
                })
            ]
        })
        po2.button_confirm()

        # Update price and verify it tracks the newer PO price (po2)
        self.product._update_standard_price()
        self.assertEqual(self.product.standard_price, 120.0)

    def test_06_stock_move_remaining_value(self):
        """ Test remaining value calculation for moves of products with cost method 'last' """
        # Set standard price to $50
        self.product.standard_price = 50.0

        # Create an incoming picking and move
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
        })
        move = self.env['stock.move'].create({
            'name': 'Test Stock Move In',
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 10.0,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'picking_id': picking.id,
        })
        picking.action_confirm()
        picking.action_assign()
        for move_line in move.move_line_ids:
            move_line.quantity = 10.0
        picking.button_validate()

        self.assertEqual(move.state, 'done')
        self.assertEqual(move.value, 500.0)
        self.assertEqual(move.remaining_qty, 10.0)

        # Trigger compute remaining value
        move._compute_remaining_value()
        self.assertEqual(move.remaining_value, 500.0)

        # Process an outgoing picking of 4 units
        picking_out = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        move_out = self.env['stock.move'].create({
            'name': 'Test Stock Move Out',
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 4.0,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'picking_id': picking_out.id,
        })
        picking_out.action_confirm()
        picking_out.action_assign()
        for move_line in move_out.move_line_ids:
            move_line.quantity = 4.0
        picking_out.button_validate()

        self.assertEqual(move_out.state, 'done')

        # Verify remaining quantity is reduced to 6.0
        self.assertEqual(move.remaining_qty, 6.0)

        # Trigger compute remaining value and check Ratio logic
        move._compute_remaining_value()
        # Ratio = 6.0 / 10.0 = 0.6
        # remaining_value = 0.6 * 500 = 300.0
        self.assertEqual(move.remaining_value, 300.0)

    def test_07_audit_report_view(self):
        """ Test that query on stock_avco_report runs successfully with the added selection """
        # Read the stock_avco_report view to verify there are no SQL execution errors
        report_records = self.env['stock.avco.report'].search([], limit=1)
        # Even if empty, it shouldn't raise any database schema or selection error
        self.assertTrue(isinstance(report_records, models.Model))
