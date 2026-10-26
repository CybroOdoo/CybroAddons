# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(https://www.cybrosys.com)
#    Author: Cybrosys Techno Solutions(https://www.cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestOrderLineNote(TransactionCase):
    """Test cases for checking the propagation of notes from order lines to
    stock moves and invoices, and the presence of the note fields.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info('Setting up TestOrderLineNote class')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

    def test_01_sale_order_line_note_propagates_to_invoice(self):
        """Sale order line note should be copied to the generated invoice line."""
        _logger.info('Running test_01_sale_order_line_note_propagates_to_invoice')
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
                'note': 'Test Sale Note',
            })],
        })
        sale_order.action_confirm()
        invoice = sale_order._create_invoices()
        self.assertTrue(invoice)
        self.assertEqual(invoice.invoice_line_ids[0].note, 'Test Sale Note')

    def test_02_purchase_order_line_note_propagates_to_invoice(self):
        """Purchase order line note should be copied to the generated invoice line."""
        _logger.info('Running test_02_purchase_order_line_note_propagates_to_invoice')
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 1.0,
                'price_unit': 100.0,
                'note': 'Test Purchase Note',
            })],
        })
        purchase_order.button_confirm()
        invoice_action = purchase_order.action_create_invoice()
        invoice = self.env['account.move'].browse(invoice_action['res_id'])
        self.assertTrue(invoice)
        self.assertEqual(invoice.invoice_line_ids[0].note, 'Test Purchase Note')

    def test_03_sale_order_line_note_propagates_to_stock_move(self):
        """Sale order line note should be copied to the related stock move."""
        _logger.info('Running test_03_sale_order_line_note_propagates_to_stock_move')
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 2.0,
                'note': 'Sale Stock Note',
            })],
        })
        sale_order.action_confirm()
        stock_move = self.env['stock.move'].search([('sale_line_id', '=', sale_order.order_line[0].id)])
        self.assertTrue(stock_move)
        self.assertEqual(stock_move.note, 'Sale Stock Note')

    def test_04_purchase_order_line_note_propagates_to_stock_move(self):
        """Purchase order line note should be copied to the related stock move."""
        _logger.info('Running test_04_purchase_order_line_note_propagates_to_stock_move')
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 3.0,
                'price_unit': 50.0,
                'note': 'Purchase Stock Note',
            })],
        })
        purchase_order.button_confirm()
        stock_move = self.env['stock.move'].search([('purchase_line_id', '=', purchase_order.order_line[0].id)])
        self.assertTrue(stock_move)
        self.assertEqual(stock_move.note, 'Purchase Stock Note')

    def test_05_note_field_presence(self):
        """Ensure the `note` field exists on sale, purchase and stock models."""
        _logger.info('Running test_05_note_field_presence')
        self.assertIn('note', self.env['sale.order.line']._fields)
        self.assertIn('note', self.env['purchase.order.line']._fields)
        self.assertIn('note', self.env['stock.move']._fields)

    def test_06_sale_order_report_contains_note(self):
        """Sale order PDF report should contain the order line note."""
        _logger.info('Running test_06_sale_order_report_contains_note')
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
                'note': 'Special Sale Report Note',
            })],
        })
        html = self.env['ir.actions.report']._render_qweb_html(
            'sale.action_report_saleorder', [sale_order.id]
        )[0]
        html_str = html.decode() if isinstance(html, bytes) else str(html)
        self.assertIn('Special Sale Report Note', html_str)

    def test_07_purchase_order_reports_contain_note(self):
        """Purchase order and RFQ PDF reports should contain the order line note."""
        _logger.info('Running test_07_purchase_order_reports_contain_note')
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 1.0,
                'price_unit': 100.0,
                'note': 'Special Purchase Report Note',
            })],
        })
        po_html = self.env['ir.actions.report']._render_qweb_html(
            'purchase.action_report_purchase_order', [purchase_order.id]
        )[0]
        po_html_str = po_html.decode() if isinstance(po_html, bytes) else str(po_html)
        self.assertIn('Special Purchase Report Note', po_html_str)

        rfq_html = self.env['ir.actions.report']._render_qweb_html(
            'purchase.report_purchase_quotation', [purchase_order.id]
        )[0]
        rfq_html_str = rfq_html.decode() if isinstance(rfq_html, bytes) else str(rfq_html)
        self.assertIn('Special Purchase Report Note', rfq_html_str)

