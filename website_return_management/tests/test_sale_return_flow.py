# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.sale_stock.tests.common import TestSaleStockCommon


@tagged('post_install', '-at_install')
class TestSaleReturnFlow(TestSaleStockCommon):
    """Cover return_confirm(), rebuilt on stock.picking._create_return()
    since stock.return.picking / .line no longer exist in Odoo 20."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # _so_deliver() (odoo-20.0/addons/sale_stock/tests/common.py) needs
        # self.warehouse; TestSaleStockCommon doesn't set it (only its own
        # warehouse_3_steps_pull), matching the pattern in
        # addons/sale_stock/tests/test_return_order.py.
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)

    def test_return_confirm_raises_for_non_done_picking(self):
        """The old stock.return.picking wizard refused to return from a
        transfer that wasn't validated yet; _create_return() itself has
        no such guard in v20, so return_confirm() must enforce it."""
        so = self._so_deliver(self.product, quantity=2, picking=False, partner=self.partner)
        sale_return = self.env['sale.return'].create({
            'product_id': self.product.id,
            'sale_order_id': so.id,
            'partner_id': so.partner_id.id,
            'quantity': 1,
        })
        with self.assertRaises(UserError):
            sale_return.return_confirm()

    def test_return_confirm_creates_scoped_return_picking(self):
        """Returning part of a validated delivery must create a draft
        return picking containing only the requested product, at the
        requested quantity - not a full copy of every move on the
        delivery, which is what _create_return() does by default."""
        so = self._so_deliver(self.product, quantity=5, partner=self.partner)
        sale_return = self.env['sale.return'].create({
            'product_id': self.product.id,
            'sale_order_id': so.id,
            'partner_id': so.partner_id.id,
            'quantity': 2,
            'to_refund': True,
        })
        sale_return.return_confirm()
        self.assertEqual(sale_return.state, 'confirm')
        return_picking = sale_return.return_picking_ids
        self.assertTrue(return_picking, "return_confirm() should link the new return picking")
        self.assertEqual(len(return_picking.move_ids), 1)
        self.assertEqual(return_picking.move_ids.product_id, self.product)
        self.assertEqual(return_picking.move_ids.product_uom_qty, 2)
        self.assertTrue(return_picking.move_ids.to_refund)
        self.assertEqual(return_picking.state, 'draft')
