# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_out = cls.env.ref('stock.picking_type_out')
        cls.unit = cls.env.ref('uom.product_uom_unit')

    def _create_product(self, name, package_category=None):
        return self.env['product.product'].create({
            'name': name,
            'is_storable': True,
            'uom_id': self.unit.id,
            'uom_po_id': self.unit.id,
            'package_category_id': package_category.id if package_category else False,
        })

    def _create_picking_with_lines(self, products):
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        for product in products:
            move = self.env['stock.move'].create({
                'name': product.display_name,
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': 1,
                'picking_id': picking.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })
            self.env['stock.move.line'].create({
                'picking_id': picking.id,
                'move_id': move.id,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
                'quantity': 1,
                'picked': True,
            })
        return picking

    def test_put_in_pack_splits_move_lines_by_package_category(self):
        chilled = self.env['package.category'].create({'name': 'Chilled'})
        dry = self.env['package.category'].create({'name': 'Dry'})
        chilled_product_1 = self._create_product('Chilled Product 1', chilled)
        chilled_product_2 = self._create_product('Chilled Product 2', chilled)
        dry_product = self._create_product('Dry Product', dry)
        picking = self._create_picking_with_lines([
            chilled_product_1, chilled_product_2, dry_product])

        packages = picking._put_in_pack(picking.move_line_ids)

        self.assertEqual(len(packages), 2)
        chilled_lines = picking.move_line_ids.filtered(
            lambda line: line.product_id.package_category_id == chilled)
        dry_lines = picking.move_line_ids.filtered(
            lambda line: line.product_id.package_category_id == dry)
        self.assertEqual(len(chilled_lines.result_package_id), 1)
        self.assertEqual(len(dry_lines.result_package_id), 1)
        self.assertNotEqual(chilled_lines.result_package_id, dry_lines.result_package_id)
        self.assertIn('Chilled', chilled_lines.result_package_id.name)
        self.assertIn('Dry', dry_lines.result_package_id.name)
        self.assertEqual(len(picking.package_level_ids), 2)

    def test_put_in_pack_applies_packaging_package_type(self):
        package_type = self.env['stock.package.type'].create({
            'name': 'Box Type',
            'company_id': self.env.company.id,
        })
        category = self.env['package.category'].create({'name': 'Boxed'})
        product = self._create_product('Boxed Product', category)
        packaging = self.env['product.packaging'].create({
            'name': 'Box',
            'product_id': product.id,
            'qty': 1,
            'package_type_id': package_type.id,
        })
        picking = self._create_picking_with_lines([product])
        picking.move_ids.product_packaging_id = packaging

        package = picking._put_in_pack(picking.move_line_ids)[0]

        self.assertEqual(package.package_type_id, package_type)
