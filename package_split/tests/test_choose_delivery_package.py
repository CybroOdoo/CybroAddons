# -*- coding: utf-8 -*-

from odoo.addons.stock.tests.common import TestStockCommon


class TestChooseDeliveryPackage(TestStockCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.package_type = cls.env['stock.package.type'].create({
            'name': 'Insulated Box',
            'sequence_code': 'IBOX',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Packed Product',
            'is_storable': True,
        })

    def test_wizard_sets_package_type_and_shipping_weight(self):
        picking = self.env['stock.picking'].create({
            'name': 'Package Wizard Picking',
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.picking_type_out.id,
        })
        move_line = self.env['stock.move.line'].create({
            'picking_id': picking.id,
            'product_id': self.product.id,
            'product_uom_id': self.product.uom_id.id,
            'quantity': 2,
            'picked': True,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        wizard = self.env['stock.put.in.pack'].create({
            'move_line_ids': [(6, 0, move_line.ids)],
            'package_type_id': self.package_type.id,
            'shipping_weight': 7.5,
        })

        wizard.action_put_in_pack()

        package = move_line.result_package_id
        self.assertTrue(package)
        self.assertEqual(package.package_type_id, self.package_type)
        self.assertEqual(package.shipping_weight, 7.5)

    def test_wizard_respects_context_selected_move_lines(self):
        picking = self.env['stock.picking'].create({
            'name': 'Selected Lines Picking',
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.picking_type_out.id,
        })
        selected_line = self.env['stock.move.line'].create({
            'picking_id': picking.id,
            'product_id': self.product.id,
            'product_uom_id': self.product.uom_id.id,
            'quantity': 1,
            'picked': True,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        other_line = selected_line.copy({
            'result_package_id': False,
        })
        wizard = self.env['stock.put.in.pack'].with_context(
            move_lines_to_pack_ids=selected_line.ids,
        ).create({
            'move_line_ids': [(6, 0, (selected_line | other_line).ids)],
            'package_type_id': self.package_type.id,
        })

        wizard.action_put_in_pack()

        self.assertTrue(selected_line.result_package_id)
        self.assertFalse(other_line.result_package_id)
