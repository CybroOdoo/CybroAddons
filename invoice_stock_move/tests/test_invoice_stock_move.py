# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestInvoiceStockMove(AccountTestInvoicingCommon):
    """Test the creation of stock pickings from invoices."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.partner_a
        cls.product_one = cls._create_stock_product('Invoice Stock Product 1')
        cls.product_two = cls._create_stock_product('Invoice Stock Product 2')
        cls.service = cls.env['product.product'].create({
            'name': 'Invoice Stock Service',
            'type': 'service',
        })

    @classmethod
    def _create_stock_product(cls, name):
        """Create a storable product."""
        return cls.env['product.product'].create({
            'name': name,
            'type': 'consu',
            'is_storable': True,
        })

    def _create_invoice(self, move_type='out_invoice', products=None,
                        post=True):
        """Create (and post) an invoice with one line per given product."""
        products = products or [self.product_one]
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                Command.create({
                    'product_id': product.id,
                    'quantity': 3,
                    'price_unit': 10,
                }) for product in products
            ],
        })
        if post:
            invoice.action_post()
        return invoice

    def _get_picking_type(self, code):
        """Return the picking type of the company for the given code."""
        return self.env['stock.picking.type'].search(
            [('code', '=', code), ('company_id', '=', self.company.id)],
            limit=1)

    def test_picking_type_for_customer_documents(self):
        """Customer invoices and credit notes get the outgoing type."""
        for move_type in ('out_invoice', 'out_refund'):
            invoice = self._create_invoice(move_type, post=False)
            self.assertEqual(
                invoice.picking_type_id, self._get_picking_type('outgoing'))

    def test_picking_type_for_vendor_documents(self):
        """Vendor bills and refunds get the incoming type."""
        for move_type in ('in_invoice', 'in_refund'):
            invoice = self._create_invoice(move_type, post=False)
            self.assertEqual(
                invoice.picking_type_id, self._get_picking_type('incoming'))

    def test_no_picking_type_for_journal_entry(self):
        """A journal entry has no picking type."""
        entry = self.env['account.move'].create({'move_type': 'entry'})
        self.assertFalse(entry.picking_type_id)

    def test_customer_invoice_creates_outgoing_picking(self):
        """A customer invoice creates an outgoing picking with its moves."""
        invoice = self._create_invoice(
            products=[self.product_one, self.product_two])
        invoice.action_stock_move()
        picking = invoice.invoice_picking_id
        self.assertTrue(picking)
        self.assertEqual(invoice.picking_count, 1)
        self.assertEqual(picking.picking_type_id.code, 'outgoing')
        self.assertEqual(picking.partner_id, self.partner)
        self.assertEqual(picking.origin, invoice.name)
        self.assertEqual(
            picking.location_dest_id, self.partner.property_stock_customer)
        self.assertEqual(
            picking.location_id,
            picking.picking_type_id.default_location_src_id)
        self.assertEqual(len(picking.move_ids), 2)
        self.assertEqual(
            picking.move_ids.product_id,
            self.product_one + self.product_two)
        for stock_move in picking.move_ids:
            self.assertEqual(stock_move.product_uom_qty, 3)
            self.assertNotEqual(stock_move.state, 'draft')

    def test_vendor_bill_creates_incoming_picking(self):
        """A vendor bill creates an incoming picking."""
        invoice = self._create_invoice('in_invoice')
        invoice.action_stock_move()
        picking = invoice.invoice_picking_id
        self.assertEqual(picking.picking_type_id.code, 'incoming')
        self.assertEqual(
            picking.location_id, self.partner.property_stock_supplier)
        self.assertEqual(
            picking.location_dest_id,
            picking.picking_type_id.default_location_dest_id)
        self.assertEqual(picking.move_ids.product_id, self.product_one)
        self.assertEqual(picking.move_ids.product_uom_qty, 3)

    def test_credit_note_creates_outgoing_picking(self):
        """A customer credit note uses the outgoing picking type."""
        refund = self._create_invoice('out_refund')
        refund.action_stock_move()
        self.assertEqual(
            refund.invoice_picking_id.picking_type_id.code, 'outgoing')

    def test_non_storable_lines_are_ignored(self):
        """Service lines do not create stock moves."""
        invoice = self._create_invoice(
            products=[self.product_one, self.service])
        invoice.action_stock_move()
        self.assertEqual(
            invoice.invoice_picking_id.move_ids.product_id, self.product_one)

    def test_picking_is_created_only_once(self):
        """Calling the action twice does not create a second picking."""
        invoice = self._create_invoice()
        invoice.action_stock_move()
        picking = invoice.invoice_picking_id
        invoice.action_stock_move()
        self.assertEqual(invoice.invoice_picking_id, picking)
        self.assertEqual(
            self.env['stock.picking'].search_count(
                [('origin', '=', invoice.name)]), 1)

    def test_action_without_picking_type_raises(self):
        """A document without picking type cannot create a picking."""
        entry = self.env['account.move'].create({'move_type': 'entry'})
        with self.assertRaises(UserError):
            entry.action_stock_move()

    def test_action_view_picking(self):
        """The smart button opens the picking of the invoice."""
        invoice = self._create_invoice()
        invoice.action_stock_move()
        action = invoice.action_view_picking()
        self.assertEqual(action['res_model'], 'stock.picking')
        self.assertEqual(action['res_id'], invoice.invoice_picking_id.id)
        self.assertEqual(
            action['domain'], [('id', '=', invoice.invoice_picking_id.id)])

    def test_action_view_picking_without_picking(self):
        """Without a picking the action does not target a record."""
        invoice = self._create_invoice()
        action = invoice.action_view_picking()
        self.assertFalse(action.get('res_id'))

    def test_picking_is_not_copied(self):
        """Duplicating an invoice does not copy its picking."""
        invoice = self._create_invoice()
        invoice.action_stock_move()
        new_invoice = invoice.copy()
        self.assertFalse(new_invoice.invoice_picking_id)
        self.assertEqual(new_invoice.picking_count, 0)
