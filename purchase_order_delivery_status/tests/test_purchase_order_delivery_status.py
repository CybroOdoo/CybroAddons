# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPurchaseOrderDeliveryStatus(TransactionCase):
    """ Test the computation of the delivery status on purchase orders. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.storable = cls.env['product.product'].create({
            'name': 'Test Storable Product',
            'type': 'consu',
            'is_storable': True,
        })
        cls.service = cls.env['product.product'].create({
            'name': 'Test Service Product',
            'type': 'service',
        })

    def _create_order(self, products, qty=10.0):
        """ Create a purchase order with one line for each given product. """
        return self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_qty': qty,
                'price_unit': 10.0,
            }) for product in products],
        })

    def _receive(self, order, qty=None):
        """ Validate the open receipt of the order, optionally with a
        partial quantity (a backorder is created in that case). """
        picking = order.picking_ids.filtered(
            lambda p: p.state not in ('done', 'cancel'))[:1]
        if qty is not None:
            picking.move_ids.quantity = qty
        else:
            picking.move_ids.quantity = picking.move_ids.product_uom_qty
        picking.with_context(skip_backorder=True).button_validate()
        return picking

    def test_field_definition(self):
        """ The field is stored and has the four expected values. """
        field = self.env['purchase.order']._fields['delivery_status']
        self.assertTrue(field.store)
        self.assertEqual(
            [key for key, _label in field.selection],
            ['nothing', 'to_receive', 'partial', 'received'])

    def test_nothing_to_receive_for_draft_order(self):
        """ A quotation has no receipt yet, so there is nothing to receive. """
        order = self._create_order(self.storable)
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.delivery_status, 'nothing')

    def test_to_receive_after_confirmation(self):
        """ Once confirmed, the receipt exists and nothing is received. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self.assertTrue(order.picking_ids)
        self.assertEqual(order.delivery_status, 'to_receive')

    def test_partial_receipt(self):
        """ Receiving less than the ordered quantity gives 'partial'. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self._receive(order, qty=4.0)
        self.assertEqual(order.order_line.qty_received, 4.0)
        self.assertEqual(order.delivery_status, 'partial')

    def test_full_receipt(self):
        """ Receiving the full quantity gives 'received'. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self._receive(order)
        self.assertEqual(order.order_line.qty_received, 10.0)
        self.assertEqual(order.delivery_status, 'received')

    def test_partial_then_full_receipt(self):
        """ The status moves from 'partial' to 'received' on the backorder. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self._receive(order, qty=4.0)
        self.assertEqual(order.delivery_status, 'partial')
        self._receive(order)
        self.assertEqual(order.delivery_status, 'received')

    def test_over_receipt_is_received(self):
        """ Receiving more than ordered must still give a valid status. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self._receive(order, qty=12.0)
        self.assertEqual(order.delivery_status, 'received')

    def test_multiple_lines_partially_received(self):
        """ One fully received line and one untouched line is 'partial'. """
        second = self.storable.copy({'name': 'Second Storable Product'})
        order = self._create_order(self.storable + second)
        order.button_confirm()
        picking = order.picking_ids[:1]
        move = picking.move_ids.filtered(
            lambda m: m.product_id == self.storable)
        move.quantity = move.product_uom_qty
        (picking.move_ids - move).quantity = 0.0
        picking.with_context(skip_backorder=True).button_validate()
        self.assertEqual(order.delivery_status, 'partial')

    def test_service_only_order_is_to_receive(self):
        """ A confirmed service-only order has no receipt but is not
        flagged as 'nothing to receive'. """
        order = self._create_order(self.service)
        order.button_confirm()
        self.assertFalse(order.picking_ids)
        self.assertEqual(order.delivery_status, 'to_receive')

    def test_draft_rfq_with_service_line_is_nothing_to_receive(self):
        """ A draft RFQ with a service line must show 'nothing to receive'. """
        order = self._create_order(self.service)
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.delivery_status, 'nothing')

    def test_cancelled_order_with_receipts_is_nothing_to_receive(self):
        """ A cancelled order with receipts must show 'nothing to receive'. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self.assertEqual(order.delivery_status, 'to_receive')
        order.button_cancel()
        self.assertEqual(order.state, 'cancel')
        self.assertEqual(order.delivery_status, 'nothing')

    def test_cancelled_order_with_partial_receipt_is_nothing_to_receive(self):
        """ A cancelled order with partial receipt must show 'nothing'. """
        order = self._create_order(self.storable)
        order.button_confirm()
        self._receive(order, qty=4.0)
        self.assertEqual(order.delivery_status, 'partial')
        order.button_cancel()
        self.assertEqual(order.state, 'cancel')
        self.assertEqual(order.delivery_status, 'nothing')

    def test_views_show_delivery_status(self):
        """ The field is available in the form and list views. """
        for view_type in ('form', 'list'):
            arch = self.env['purchase.order'].get_view(
                view_type=view_type)['arch']
            self.assertIn('delivery_status', arch)
