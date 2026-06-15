# -*- coding: utf-8 -*-

from odoo.addons.stock.tests.common import TestStockCommon


class TestStockMove(TestStockCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env["ir.config_parameter"].sudo()
        cls.product = cls.env["product.product"].create({
            "name": "Auto Lot Move Product",
            "is_storable": True,
            "tracking": "lot",
            "prefix": "PRD",
            "digits": 4,
        })
        cls.location_dest = cls.env["stock.location"].create({
            "name": "Auto Lot Destination",
            "usage": "internal",
            "location_id": cls.stock_location,
        })

    def setUp(self):
        super().setUp()
        self.params.set_param(
            "auto_generate_lot_number.is_auto_generate", True
        )
        self.params.set_param(
            "auto_generate_lot_number.serial_number_type", "product"
        )
        self.params.set_param("auto_generate_lot_number.prefix", "GLB")
        self.params.set_param("auto_generate_lot_number.digits", 4)

    def _create_move(self):
        return self.env["stock.move"].create({
            "name": "Auto Lot Move",
            "product_id": self.product.id,
            "product_uom": self.product.uom_id.id,
            "product_uom_qty": 1,
            "location_id": self.stock_location,
            "location_dest_id": self.location_dest.id,
        })

    def test_prepare_move_line_vals_uses_product_lot_sequence(self):
        move = self._create_move()
        self.product.product_tmpl_id.write({
            "prefix": "PRD",
            "digits": 4,
            "number_next": 0,
        })

        vals = move._prepare_move_line_vals(quantity=1)

        self.assertEqual(vals["lot_name"], "PRD0001")
        self.assertEqual(vals["quantity"], 1)
        self.assertEqual(vals["product_id"], self.product.id)
        self.assertEqual(self.product.product_tmpl_id.number_next, 1)

    def test_prepare_move_line_vals_uses_global_lot_sequence(self):
        self.params.set_param(
            "auto_generate_lot_number.serial_number_type", "global"
        )
        self.params.set_param("auto_generate_lot_number.prefix", "GLB")
        self.params.set_param("auto_generate_lot_number.digits", 5)
        move = self._create_move()

        vals = move._prepare_move_line_vals(quantity=1)

        self.assertTrue(vals["lot_name"].startswith("GLB"))
        self.assertEqual(len(vals["lot_name"]), 8)

    def test_prepare_move_line_vals_keeps_reserved_quant_values(self):
        lot = self.env["stock.lot"].create({
            "name": "Reserved Lot",
            "product_id": self.product.id,
        })
        package = self.env["stock.quant.package"].create({
            "name": "Reserved Package",
        })
        owner = self.env["res.partner"].create({
            "name": "Reserved Owner",
        })
        quant = self.env["stock.quant"].create({
            "product_id": self.product.id,
            "location_id": self.location_dest.id,
            "quantity": 2,
            "lot_id": lot.id,
            "package_id": package.id,
            "owner_id": owner.id,
        })
        move = self._create_move()

        vals = move._prepare_move_line_vals(quantity=1, reserved_quant=quant)

        self.assertEqual(vals["location_id"], self.location_dest.id)
        self.assertEqual(vals["lot_id"], lot.id)
        self.assertEqual(vals["package_id"], package.id)
        self.assertEqual(vals["owner_id"], owner.id)

    def test_action_show_details_uses_module_view_when_enabled(self):
        move = self._create_move()
        expected_view = self.env.ref(
            "auto_generate_lot_number.view_stock_move_operations"
        )

        action = move.action_show_details()

        self.assertEqual(action["view_id"], expected_view.id)
        self.assertEqual(action["views"], [(expected_view.id, "form")])

    def test_action_show_details_uses_stock_view_when_disabled(self):
        self.params.set_param(
            "auto_generate_lot_number.is_auto_generate", False
        )
        move = self._create_move()
        expected_view = self.env.ref("stock.view_stock_move_operations")

        action = move.action_show_details()

        self.assertEqual(action["view_id"], expected_view.id)
        self.assertEqual(action["views"], [(expected_view.id, "form")])
