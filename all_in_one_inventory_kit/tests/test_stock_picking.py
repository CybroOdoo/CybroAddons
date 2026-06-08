# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
from odoo.exceptions import UserError


class TestStockPicking(TransactionCase):
    def setUp(self):
        super(TestStockPicking, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu', 'is_storable': True,
            'barcode': '123456789',
            'lst_price': 100.0,
        })
        self.picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        self.picking_type_in = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        self.location_src = self.picking_type_out.default_location_src_id
        self.location_dest = self.picking_type_out.default_location_dest_id

        self.picking_out = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.move = self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 1.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'picking_id': self.picking_out.id,
        })

    def test_barcode_scanning(self):
        # Scan existing barcode
        self.picking_out.barcode = '123456789'
        self.picking_out.move_line_ids = [(0, 0, {
            'product_id': self.product.id,
            'quantity': 1.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })]
        self.picking_out._onchange_barcode()
        
        # Test warning for invalid barcode
        self.picking_out.barcode = 'invalid_barcode'
        res = self.picking_out._onchange_barcode()
        self.assertIn('warning', res)
        
        # Test barcode write overriding
        self.picking_out.with_context(barcode_processed=True).write({'barcode': '123456789'})

    def test_invoice_creation(self):
        # Configure journal
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        self.env['ir.config_parameter'].sudo().set_param('stock_move_invoice.customer_journal_id', journal.id)
        
        invoice = self.picking_out.action_create_invoice()
        self.assertTrue(invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.picking_id.id, self.picking_out.id)
        
        # Check compute count and action open
        self.picking_out._compute_invoice_count()
        self.assertEqual(self.picking_out.invoice_count, 1)
        res = self.picking_out.action_open_picking_invoice()
        self.assertEqual(res['res_model'], 'account.move')

    def test_bill_creation(self):
        picking_in = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.picking_type_in.default_location_src_id.id,
            'location_dest_id': self.picking_type_in.default_location_dest_id.id,
        })
        self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 1.0,
            'location_id': picking_in.location_id.id,
            'location_dest_id': picking_in.location_dest_id.id,
            'picking_id': picking_in.id,
        })
        
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        self.env['ir.config_parameter'].sudo().set_param('stock_move_invoice.vendor_journal_id', journal.id)
        
        bill = picking_in.action_create_bill()
        self.assertTrue(bill)
        self.assertEqual(bill.move_type, 'in_invoice')

    def test_get_dashboard_data(self):
        # Test get_operation_types
        operation_types = self.env['stock.picking'].get_operation_types()
        self.assertTrue(isinstance(operation_types, tuple))
        
        # Test get_product_category
        categories = self.env['stock.picking'].get_product_category()
        self.assertIn('name', categories)
        self.assertIn('count', categories)
        
        # Test get_locations
        locations = self.env['stock.picking'].get_locations()
        self.assertTrue(isinstance(locations, dict))
