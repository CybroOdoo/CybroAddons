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
class TestChooseDeliveryPackage(TransactionCase):
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

    def test_action_put_in_pack_sets_package_type_and_shipping_weight(self):
        category = self.env['package.category'].create({'name': 'Wizard'})
        product = self._create_product('Wizard Product', category)
        picking = self._create_picking_with_lines([product])
        package_type = self.env['stock.package.type'].create({
            'name': 'Wizard Box',
            'company_id': self.env.company.id,
        })
        wizard = self.env['choose.delivery.package'].create({
            'picking_id': picking.id,
            'delivery_package_type_id': package_type.id,
            'shipping_weight': 4.5,
        })

        result = wizard.action_put_in_pack()

        self.assertFalse(result)
        package = picking.move_line_ids.result_package_id
        self.assertTrue(package)
        self.assertEqual(package.package_type_id, package_type)
        self.assertEqual(package.shipping_weight, 4.5)

    def test_action_put_in_pack_uses_context_move_lines_to_pack_ids(self):
        category = self.env['package.category'].create({'name': 'Selected'})
        first_product = self._create_product('Selected Product', category)
        second_product = self._create_product('Unselected Product', category)
        picking = self._create_picking_with_lines([first_product, second_product])
        first_line = picking.move_line_ids.filtered(
            lambda line: line.product_id == first_product)
        second_line = picking.move_line_ids - first_line
        wizard = self.env['choose.delivery.package'].with_context(
            move_lines_to_pack_ids=first_line.ids).create({
                'picking_id': picking.id,
            })

        wizard.action_put_in_pack()

        self.assertTrue(first_line.result_package_id)
        self.assertFalse(second_line.result_package_id)
