# -*- coding: utf-8 -*-

from odoo.addons.stock.tests.common import TestStockCommon


class TestStockMoveLinePackageSplit(TestStockCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category_fragile = cls.env['package.category'].create({
            'name': 'Fragile',
        })
        cls.category_chilled = cls.env['package.category'].create({
            'name': 'Chilled',
        })
        cls.product_fragile = cls.env['product.product'].create({
            'name': 'Glass Bottle',
            'is_storable': True,
            'package_category_id': cls.category_fragile.id,
        })
        cls.product_chilled = cls.env['product.product'].create({
            'name': 'Ice Cream',
            'is_storable': True,
            'package_category_id': cls.category_chilled.id,
        })
        cls.product_without_category = cls.env['product.product'].create({
            'name': 'Plain Product',
            'is_storable': True,
        })

    def _create_picking_with_move_lines(self, products):
        picking = self.env['stock.picking'].create({
            'name': 'Package Split Picking',
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.picking_type_out.id,
        })
        move_lines = self.env['stock.move.line']
        for product in products:
            move_lines |= self.env['stock.move.line'].create({
                'picking_id': picking.id,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'quantity': 1,
                'picked': True,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })
        return picking, move_lines

    def test_action_put_in_pack_splits_move_lines_by_package_category(self):
        picking, move_lines = self._create_picking_with_move_lines([
            self.product_fragile,
            self.product_chilled,
            self.product_without_category,
        ])

        package = move_lines.action_put_in_pack(package_name='PACK')

        self.assertTrue(package, 'The pack action should return a created package.')
        self.assertEqual(len(picking.move_line_ids.result_package_id), 3)
        self.assertEqual(
            move_lines.filtered(lambda ml: ml.product_id == self.product_fragile).result_package_id.name,
            'PACK-Fragile',
        )
        self.assertEqual(
            move_lines.filtered(lambda ml: ml.product_id == self.product_chilled).result_package_id.name,
            'PACK-Chilled',
        )
        self.assertEqual(
            move_lines.filtered(lambda ml: ml.product_id == self.product_without_category).result_package_id.name,
            'PACK',
        )

    def test_action_put_in_pack_groups_same_package_category_together(self):
        second_fragile_product = self.env['product.product'].create({
            'name': 'Ceramic Cup',
            'is_storable': True,
            'package_category_id': self.category_fragile.id,
        })
        picking, move_lines = self._create_picking_with_move_lines([
            self.product_fragile,
            second_fragile_product,
        ])

        move_lines.action_put_in_pack(package_name='BOX')

        self.assertEqual(len(picking.move_line_ids.result_package_id), 1)
        self.assertEqual(picking.move_line_ids.result_package_id.name, 'BOX-Fragile')
