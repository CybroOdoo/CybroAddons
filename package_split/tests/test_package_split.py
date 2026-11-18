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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged

from odoo.addons.mail.tests.common import mail_new_test_user


@tagged('post_install', '-at_install')
class TestPackageSplit(TransactionCase):
    """Unit tests covering package categories, settings, packing split, and wizard flows."""

    @classmethod
    def setUpClass(cls):
        """Set up warehouse, products, categories, package types, and carrier fixtures."""
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)],
            limit=1,
        )
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Package Split Warehouse',
                'code': 'PSW',
            })
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.picking_type_out.set_package_type = False
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.partner = cls.env['res.partner'].create({'name': 'Package Split Customer'})

        cls.category_chair = cls.env['package.category'].create({'name': 'Chair'})
        cls.category_desk = cls.env['package.category'].create({'name': 'Desk'})

        cls.package_type_box = cls.env['stock.package.type'].create({
            'name': 'Box Package Type',
            'sequence_code': 'BOX',
        })
        cls.package_type_uom = cls.env['stock.package.type'].create({
            'name': 'UoM Package Type',
            'sequence_code': 'UOMPKG',
        })

        cls.product_chair = cls.env['product.product'].create({
            'name': 'Office Chair',
            'is_storable': True,
            'weight': 3.0,
            'package_category_id': cls.category_chair.id,
        })
        cls.product_desk = cls.env['product.product'].create({
            'name': 'Office Desk',
            'is_storable': True,
            'weight': 5.0,
            'package_category_id': cls.category_desk.id,
        })
        cls.product_uncategorized = cls.env['product.product'].create({
            'name': 'Uncategorized Lamp',
            'is_storable': True,
            'weight': 1.0,
        })

        cls.uom_box = cls.env['uom.uom'].create({
            'name': 'Package Box Unit',
            'relative_factor': 1.0,
            'relative_uom_id': cls.product_chair.uom_id.id,
            'package_type_id': cls.package_type_uom.id,
        })

        carrier_product = cls.env['product.product'].create({
            'name': 'Split Carrier Service',
            'type': 'service',
        })
        cls.carrier = cls.env['delivery.carrier'].create({
            'name': 'Split Carrier',
            'delivery_type': 'fixed',
            'product_id': carrier_product.id,
        })

        cls.env['res.config.settings'].create({
            'group_stock_tracking_lot': True,
            'enable_package_split': True,
        }).execute()

    def _create_picking_with_lines(self, items, carrier=False, set_package_type=False):
        """Create an outgoing picking with confirmed stock moves and picked move lines."""
        self.picking_type_out.set_package_type = set_package_type
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'carrier_id': carrier.id if carrier else False,
        })
        for product, quantity, packaging_uom in items:
            self.env['stock.quant']._update_available_quantity(
                product,
                self.stock_location,
                quantity,
            )
            move_vals = {
                'picking_id': picking.id,
                'picking_type_id': self.picking_type_out.id,
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'product_uom_qty': quantity,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            }
            move = self.env['stock.move'].create(move_vals)
            if packaging_uom:
                move.packaging_uom_id = packaging_uom
            self.env['stock.move.line'].create({
                'picking_id': picking.id,
                'move_id': move.id,
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'quantity': quantity,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
                'picked': True,
            })
        return picking

    def test_package_category_constraints_and_user_access(self):
        """Verify required field constraint, chatter tracking, and base user CRUD rights."""
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env['package.category'].create({})

        basic_user = mail_new_test_user(
            self.env,
            login='package_split_basic_user',
            groups='base.group_user',
        )
        category = self.env['package.category'].with_user(basic_user).create({
            'name': 'Fragile',
        })
        self.assertEqual(category.name, 'Fragile')
        message = category.message_post(body="Category configured")
        self.assertIn(message, category.message_ids)
        category.with_user(basic_user).write({'name': 'Fragile Items'})
        self.assertEqual(category.name, 'Fragile Items')
        category.with_user(basic_user).unlink()

    def test_settings_and_product_template_compute(self):
        """Verify config settings compute, persistence, and product template compute."""
        settings_a = self.env['res.config.settings'].create({
            'group_stock_tracking_lot': False,
        })
        settings_b = self.env['res.config.settings'].create({
            'group_stock_tracking_lot': True,
        })
        (settings_a | settings_b)._compute_enable_package_split()
        self.assertFalse(settings_a.enable_package_split)
        self.assertTrue(settings_b.enable_package_split)

        settings_disabled = self.env['res.config.settings'].create({
            'group_stock_tracking_lot': True,
            'enable_package_split': False,
        })
        settings_disabled.execute()
        self.product_chair.product_tmpl_id.invalidate_recordset(['package_split_value'])
        self.product_chair.invalidate_recordset(['package_split_value'])
        self.assertFalse(self.product_chair.product_tmpl_id.package_split_value)

        settings_b.execute()
        self.product_chair.product_tmpl_id.invalidate_recordset(['package_split_value'])
        self.product_chair.invalidate_recordset(['package_split_value'])
        self.assertTrue(self.product_chair.product_tmpl_id.package_split_value)

    def test_put_in_pack_splits_by_category_and_respects_toggle(self):
        """Verify move lines split by package category only when package split is enabled."""
        picking_split = self._create_picking_with_lines([
            (self.product_chair, 2.0, self.uom_box),
            (self.product_desk, 1.0, False),
            (self.product_uncategorized, 3.0, False),
        ])
        first_package = picking_split.action_put_in_pack()
        self.assertTrue(first_package)

        result_packages = picking_split.move_line_ids.result_package_id
        self.assertEqual(len(result_packages), 3)

        chair_line = picking_split.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_chair,
        )
        desk_line = picking_split.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_desk,
        )
        uncat_line = picking_split.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_uncategorized,
        )
        self.assertTrue(chair_line.result_package_id.name.endswith('-Chair'))
        self.assertEqual(chair_line.result_package_id.package_type_id, self.package_type_uom)
        self.assertTrue(desk_line.result_package_id.name.endswith('-Desk'))
        self.assertFalse(
            uncat_line.result_package_id.name.endswith(('-Chair', '-Desk')),
        )

        self.env['res.config.settings'].create({
            'group_stock_tracking_lot': True,
            'enable_package_split': False,
        }).execute()
        picking_standard = self._create_picking_with_lines([
            (self.product_chair, 1.0, False),
            (self.product_desk, 1.0, False),
        ])
        single_package = picking_standard.action_put_in_pack()
        self.assertTrue(single_package)
        self.assertEqual(len(picking_standard.move_line_ids.result_package_id), 1)

    def test_put_in_pack_edge_cases_and_capacity_split(self):
        """Verify empty packables, already-packed outer packs, and package capacity splits."""
        empty_result = self.env['stock.move.line'].action_put_in_pack()
        self.assertFalse(empty_result)

        picking = self._create_picking_with_lines([
            (self.product_chair, 6.0, False),
        ])
        chunk_lines = picking.move_line_ids.action_put_in_pack(
            package_type_id=self.package_type_box.id,
            package_capacity=2.0,
        )
        self.assertEqual(len(set(chunk_lines.ids)), 3)
        self.assertEqual(len(picking.move_line_ids), 3)
        self.assertEqual(len(picking.move_line_ids.result_package_id), 3)

        outer_result = picking.action_put_in_pack(
            package_type_id=self.package_type_uom.id,
        )
        self.assertTrue(outer_result)
        self.assertEqual(len(picking.move_line_ids.result_package_id.package_dest_id), 1)

    def test_put_in_pack_wizard_category_split_and_carrier_weight(self):
        """Verify Put in Pack wizard splits by category and propagates type and weight."""
        picking = self._create_picking_with_lines(
            [
                (self.product_chair, 2.0, False),
                (self.product_desk, 1.0, False),
            ],
            set_package_type=True,
        )
        action = picking.action_put_in_pack()
        self.assertEqual(action['res_model'], 'stock.put.in.pack')

        wizard = self.env['stock.put.in.pack'].with_context(**action['context']).create({
            'package_type_id': self.package_type_box.id,
        })
        wiz_result = wizard.action_put_in_pack()
        self.assertTrue(wiz_result)

        split_packages = picking.move_line_ids.result_package_id
        self.assertEqual(len(split_packages), 2)
        self.assertEqual(set(split_packages.package_type_id.ids), {self.package_type_box.id})

        picking_carrier = self._create_picking_with_lines(
            [(self.product_chair, 2.0, False)],
            carrier=self.carrier,
            set_package_type=True,
        )
        carrier_action = picking_carrier.action_put_in_pack()
        carrier_wizard = self.env['stock.put.in.pack'].with_context(
            **carrier_action['context'],
        ).create({
            'package_type_id': self.package_type_box.id,
        })
        carrier_wizard.shipping_weight = 7.5
        carrier_result = carrier_wizard.action_put_in_pack()
        self.assertTrue(carrier_result)
        self.assertEqual(
            picking_carrier.move_line_ids.result_package_id.shipping_weight,
            7.5,
        )
