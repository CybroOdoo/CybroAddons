# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests import common, tagged

DUMMY_IMAGE = (
    b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='
)


@tagged('post_install', '-at_install')
class TestReportTemplates(common.TransactionCase):

    def setUp(self):
        super(TestReportTemplates, self).setUp()
        self.doc_layout = self.env['doc.layout'].create({
            'name': 'Test Layout',
            'base_color': '#FFFFFF',
            'heading_text_color': '#000000',
            'text_color': '#333333',
            'customer_text_color': '#555555',
            'company_text_color': '#666666',
            'logo_position': 'left',
            'customer_position': 'left',
            'company_position': 'right',
        })
        self.env.company.write({
            'sale_document_layout_id': self.doc_layout.id,
            'purchase_document_layout_id': self.doc_layout.id,
            'account_document_layout_id': self.doc_layout.id,
            'stock_document_layout_id': self.doc_layout.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'image_1920': DUMMY_IMAGE,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'image_1920': DUMMY_IMAGE,
        })

    def test_doc_layout_all_fields(self):
        layout = self.env['doc.layout'].create({
            'name': 'Full Layout',
            'base_color': '#123456',
            'heading_text_color': '#abcdef',
            'text_color': '#111111',
            'customer_text_color': '#222222',
            'company_text_color': '#333333',
            'logo_position': 'right',
            'customer_position': 'right',
            'company_position': 'left',
        })
        self.assertEqual(layout.name, 'Full Layout')
        self.assertEqual(layout.base_color, '#123456')
        self.assertEqual(layout.heading_text_color, '#abcdef')
        self.assertEqual(layout.text_color, '#111111')
        self.assertEqual(layout.customer_text_color, '#222222')
        self.assertEqual(layout.company_text_color, '#333333')
        self.assertEqual(layout.logo_position, 'right')
        self.assertEqual(layout.customer_position, 'right')
        self.assertEqual(layout.company_position, 'left')

    def test_doc_layout_default_company(self):
        layout = self.env['doc.layout'].create({'name': 'Default Company Layout'})
        self.assertEqual(layout.company_id, self.env.company)

    def test_doc_layout_left_right_positions(self):
        left_layout = self.env['doc.layout'].create({
            'name': 'Left Layout',
            'logo_position': 'left',
            'customer_position': 'left',
            'company_position': 'left',
        })
        right_layout = self.env['doc.layout'].create({
            'name': 'Right Layout',
            'logo_position': 'right',
            'customer_position': 'right',
            'company_position': 'right',
        })
        self.assertEqual(left_layout.logo_position, 'left')
        self.assertEqual(right_layout.logo_position, 'right')
        self.assertEqual(left_layout.customer_position, 'left')
        self.assertEqual(right_layout.customer_position, 'right')
        self.assertEqual(left_layout.company_position, 'left')
        self.assertEqual(right_layout.company_position, 'right')

    def test_company_layout_fields_assigned(self):
        company = self.env.company
        self.assertEqual(company.sale_document_layout_id, self.doc_layout)
        self.assertEqual(company.purchase_document_layout_id, self.doc_layout)
        self.assertEqual(company.account_document_layout_id, self.doc_layout)
        self.assertEqual(company.stock_document_layout_id, self.doc_layout)

    def test_company_layout_unset(self):
        self.env.company.write({
            'sale_document_layout_id': False,
            'purchase_document_layout_id': False,
            'account_document_layout_id': False,
            'stock_document_layout_id': False,
        })
        sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.assertFalse(sale_order.theme_id)
        purchase_order = self.env['purchase.order'].create({'partner_id': self.partner.id})
        self.assertFalse(purchase_order.theme_id)
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.assertFalse(invoice.theme_id)

    def test_sale_order_layout(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
        })
        self.assertEqual(sale_order.theme_id, self.doc_layout)
        self.assertTrue(sale_order.order_line[0].order_line_image)

    def test_sale_order_customer_image(self):
        sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.assertTrue(sale_order.customer_image)
        self.assertEqual(sale_order.customer_image, self.partner.image_1920)

    def test_sale_order_multiple_lines_images(self):
        product2 = self.env['product.product'].create({
            'name': 'Test Product 2',
            'type': 'consu',
            'image_1920': DUMMY_IMAGE,
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product.id, 'product_uom_qty': 1}),
                (0, 0, {'product_id': product2.id, 'product_uom_qty': 2}),
            ],
        })
        self.assertEqual(len(sale_order.order_line), 2)
        for line in sale_order.order_line:
            self.assertTrue(line.order_line_image)

    def test_sale_order_theme_switch(self):
        new_layout = self.env['doc.layout'].create({
            'name': 'New Sale Layout',
            'base_color': '#FF0000',
            'logo_position': 'right',
        })
        sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.assertEqual(sale_order.theme_id, self.doc_layout)
        self.env.company.write({'sale_document_layout_id': new_layout.id})
        self.assertEqual(sale_order.theme_id, new_layout)

    def test_purchase_order_layout(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1,
                'name': self.product.name,
                'price_unit': 100,
            })],
        })
        self.assertEqual(purchase_order.theme_id, self.doc_layout)
        self.assertTrue(purchase_order.order_line[0].order_line_image)

    def test_purchase_order_multiple_lines_images(self):
        product2 = self.env['product.product'].create({
            'name': 'Purchase Product 2',
            'type': 'consu',
            'image_1920': DUMMY_IMAGE,
        })
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product.id, 'product_qty': 1,
                        'name': self.product.name, 'price_unit': 50}),
                (0, 0, {'product_id': product2.id, 'product_qty': 2,
                        'name': product2.name, 'price_unit': 75}),
            ],
        })
        self.assertEqual(len(purchase_order.order_line), 2)
        for line in purchase_order.order_line:
            self.assertTrue(line.order_line_image)

    def test_purchase_order_theme_switch(self):
        new_layout = self.env['doc.layout'].create({
            'name': 'New Purchase Layout',
            'base_color': '#00FF00',
        })
        purchase_order = self.env['purchase.order'].create({'partner_id': self.partner.id})
        self.assertEqual(purchase_order.theme_id, self.doc_layout)
        self.env.company.write({'purchase_document_layout_id': new_layout.id})
        self.assertEqual(purchase_order.theme_id, new_layout)

    def test_account_move_customer_invoice_layout(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })],
        })
        self.assertEqual(invoice.theme_id, self.doc_layout)
        self.assertTrue(invoice.invoice_line_ids[0].order_line_image)

    def test_account_move_vendor_bill_layout(self):
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 200,
            })],
        })
        self.assertEqual(invoice.theme_id, self.doc_layout)
        self.assertTrue(invoice.invoice_line_ids[0].order_line_image)

    def test_account_move_multiple_lines_images(self):
        product2 = self.env['product.product'].create({
            'name': 'Invoice Product 2',
            'type': 'consu',
            'image_1920': DUMMY_IMAGE,
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {'product_id': self.product.id, 'quantity': 1, 'price_unit': 100}),
                (0, 0, {'product_id': product2.id, 'quantity': 2, 'price_unit': 50}),
            ],
        })
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        for line in invoice.invoice_line_ids:
            self.assertTrue(line.order_line_image)

    def test_account_move_theme_switch(self):
        new_layout = self.env['doc.layout'].create({
            'name': 'New Account Layout',
            'base_color': '#0000FF',
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.assertEqual(invoice.theme_id, self.doc_layout)
        self.env.company.write({'account_document_layout_id': new_layout.id})
        self.assertEqual(invoice.theme_id, new_layout)

    def test_stock_picking_layout(self):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')], limit=1)
        location = self.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        dest_location = self.env['stock.location'].search(
            [('usage', '=', 'customer')], limit=1)
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': dest_location.id,
            'partner_id': self.partner.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'location_id': location.id,
                'location_dest_id': dest_location.id,
            })],
        })
        self.assertEqual(picking.theme_id, self.doc_layout)
        self.assertTrue(picking.move_ids[0].order_line_image)

    def test_stock_picking_multiple_moves_images(self):
        product2 = self.env['product.product'].create({
            'name': 'Stock Product 2',
            'type': 'consu',
            'image_1920': DUMMY_IMAGE,
        })
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')], limit=1)
        location = self.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        dest_location = self.env['stock.location'].search(
            [('usage', '=', 'customer')], limit=1)
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': dest_location.id,
            'partner_id': self.partner.id,
            'move_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'location_id': location.id,
                    'location_dest_id': dest_location.id,
                }),
                (0, 0, {
                    'product_id': product2.id,
                    'product_uom_qty': 2,
                    'location_id': location.id,
                    'location_dest_id': dest_location.id,
                }),
            ],
        })
        self.assertEqual(len(picking.move_ids), 2)
        for move in picking.move_ids:
            self.assertTrue(move.order_line_image)

    def test_stock_picking_theme_switch(self):
        new_layout = self.env['doc.layout'].create({
            'name': 'New Stock Layout',
            'base_color': '#FF00FF',
        })
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')], limit=1)
        location = self.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1)
        dest_location = self.env['stock.location'].search(
            [('usage', '=', 'customer')], limit=1)
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': dest_location.id,
        })
        self.assertEqual(picking.theme_id, self.doc_layout)
        self.env.company.write({'stock_document_layout_id': new_layout.id})
        self.assertEqual(picking.theme_id, new_layout)

    def test_independent_layouts_per_document_type(self):
        sale_layout = self.env['doc.layout'].create({'name': 'Sale Only', 'base_color': '#AAAAAA'})
        purchase_layout = self.env['doc.layout'].create({'name': 'Purchase Only', 'base_color': '#BBBBBB'})
        account_layout = self.env['doc.layout'].create({'name': 'Account Only', 'base_color': '#CCCCCC'})
        stock_layout = self.env['doc.layout'].create({'name': 'Stock Only', 'base_color': '#DDDDDD'})
        self.env.company.write({
            'sale_document_layout_id': sale_layout.id,
            'purchase_document_layout_id': purchase_layout.id,
            'account_document_layout_id': account_layout.id,
            'stock_document_layout_id': stock_layout.id,
        })
        sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        purchase_order = self.env['purchase.order'].create({'partner_id': self.partner.id})
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.assertEqual(sale_order.theme_id, sale_layout)
        self.assertEqual(purchase_order.theme_id, purchase_layout)
        self.assertEqual(invoice.theme_id, account_layout)
        self.assertNotEqual(sale_order.theme_id, purchase_order.theme_id)
        self.assertNotEqual(purchase_order.theme_id, invoice.theme_id)
