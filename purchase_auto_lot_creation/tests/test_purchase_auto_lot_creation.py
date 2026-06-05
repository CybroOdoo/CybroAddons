# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(odoo@cybrosys.com)
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
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPurchaseAutoLotCreation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Lot Vendor"})
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.lot_product = cls.env["product.product"].create({
            "name": "Tracked Purchase Product",
            "type": "consu",
            "tracking": "lot",
            "uom_id": cls.uom_unit.id,
            "uom_po_id": cls.uom_unit.id,
            "seller_ids": [(0, 0, {
                "partner_id": cls.vendor.id,
                "price": 10.0,
            })],
        })

    def test_onchange_product_id_sets_lot_flag(self):
        line = self.env["purchase.order.line"].new({
            "product_id": self.lot_product.id,
        })

        line._onchange_product_id()

        self.assertTrue(line.is_lot_product)

    def test_confirm_purchase_creates_move_line_with_lot_name(self):
        purchase = self.env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "order_line": [(0, 0, {
                "name": self.lot_product.display_name,
                "product_id": self.lot_product.id,
                "product_qty": 3.0,
                "product_uom": self.uom_unit.id,
                "price_unit": 10.0,
                "date_planned": "2099-01-01 00:00:00",
            })],
        })
        lot = self.env["custom.stock.lot"].create({
            "name": "LOT-PO-0001",
            "line_id": purchase.order_line.id,
        })
        purchase.order_line.lot_id = lot.id

        purchase.button_confirm()

        move = purchase.picking_ids.move_ids.filtered(
            lambda record: record.product_id == self.lot_product
        )
        self.assertTrue(move)
        move_line = self.env["stock.move.line"].search([
            ("move_id", "=", move.id),
            ("lot_name", "=", lot.name),
        ], limit=1)
        self.assertTrue(move_line)
        self.assertEqual(move_line.quantity, purchase.order_line.product_qty)
