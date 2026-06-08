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

import odoo.tests


class TestClickAndCollect(odoo.tests.TransactionCase):
    """Comprehensive test suite for the Click & Collect POS module.
    Covers: sale order lines, POS config address fields, picking creation,
    delivery count filtering, stock moves, and POS-facing RPC methods.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Shared partner and products
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner CAC',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product CAC',
            'type': 'consu',
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Test Product CAC 2',
            'type': 'consu',
        })
        # Location records for POS config
        cls.state = cls.env['res.country.state'].search([], limit=1)
        cls.country = cls.env['res.country'].search([], limit=1)
        # POS config with full address
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop',
            'street': 'Test Street',
            'city': 'Test City',
            'state_id': cls.state.id,
            'country_id': cls.country.id,
        })
        # Base sale order with one C&C line (not yet confirmed)
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'is_click_and_collect': True,
                    'pos_config_id': cls.pos_config.id,
                })
            ]
        })

    # ------------------------------------------------------------------
    # 1. Sale Order Line Custom Fields
    # ------------------------------------------------------------------
    def test_01_sale_order_line_is_click_and_collect_field(self):
        """is_click_and_collect flag must be stored on the order line."""
        line = self.sale_order.order_line[0]
        self.assertTrue(
            line.is_click_and_collect,
            "is_click_and_collect should be True on the C&C line."
        )

    def test_02_sale_order_line_pos_config_id_field(self):
        """pos_config_id must link to the correct POS configuration."""
        line = self.sale_order.order_line[0]
        self.assertEqual(
            line.pos_config_id, self.pos_config,
            "pos_config_id should point to the test POS config."
        )

    # ------------------------------------------------------------------
    # 2. POS Config Address Fields
    # ------------------------------------------------------------------
    def test_03_pos_config_address_fields_stored(self):
        """Custom address fields on pos.config must be saved correctly."""
        self.assertEqual(self.pos_config.street, 'Test Street')
        self.assertEqual(self.pos_config.city, 'Test City')
        self.assertEqual(self.pos_config.state_id, self.state)
        self.assertEqual(self.pos_config.country_id, self.country)

    def test_04_pos_config_optional_street2_and_zip(self):
        """Street2 and zip are optional and should be blank by default."""
        self.assertFalse(self.pos_config.street2)
        self.assertFalse(self.pos_config.zip)

    # ------------------------------------------------------------------
    # 3. Core Workflow: Picking created on order confirmation
    # ------------------------------------------------------------------
    def test_05_click_and_collect_workflow(self):
        """Confirming a C&C order must create exactly one C&C picking."""
        self.sale_order.action_confirm()
        cac_pickings = self.env['stock.picking'].search([
            ('origin', '=', self.sale_order.name),
            ('is_click_and_collect_order', '=', True)
        ])
        self.assertEqual(len(cac_pickings), 1,
                         "Exactly one C&C picking should be created.")
        self.assertEqual(self.sale_order.collect_count, 1,
                         "collect_count should equal 1 after confirmation.")

    def test_06_is_click_and_collect_order_flag_on_picking(self):
        """The created picking must have is_click_and_collect_order=True."""
        self.sale_order.action_confirm()
        picking = self.env['stock.picking'].search([
            ('origin', '=', self.sale_order.name),
            ('is_click_and_collect_order', '=', True)
        ], limit=1)
        self.assertTrue(picking, "A C&C picking must exist.")
        self.assertTrue(picking.is_click_and_collect_order,
                        "is_click_and_collect_order must be True on picking.")

    def test_07_cac_picking_linked_to_partner(self):
        """C&C picking must be linked to the sale order's partner."""
        self.sale_order.action_confirm()
        picking = self.env['stock.picking'].search([
            ('origin', '=', self.sale_order.name),
            ('is_click_and_collect_order', '=', True)
        ], limit=1)
        self.assertEqual(picking.partner_id, self.partner,
                         "Picking partner must match the sale order partner.")

    # ------------------------------------------------------------------
    # 4. Stock Move created for C&C Line
    # ------------------------------------------------------------------
    def test_08_stock_move_created_for_cac_line(self):
        """A stock.move must be created for the C&C line and linked to picking."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })]
        })
        order.action_confirm()
        picking = self.env['stock.picking'].search([
            ('origin', '=', order.name),
            ('is_click_and_collect_order', '=', True)
        ], limit=1)
        self.assertTrue(picking.move_ids, "Picking must contain at least one stock move.")
        move = picking.move_ids[0]
        self.assertEqual(move.product_id, self.product)
        self.assertEqual(move.product_uom_qty, 3,
                         "Move demand must match the order line quantity.")
        self.assertEqual(move.sale_line_id, order.order_line[0],
                         "Move must be linked to the correct sale order line.")

    # ------------------------------------------------------------------
    # 5. No C&C picking when line is NOT click_and_collect
    # ------------------------------------------------------------------
    def test_09_no_cac_picking_for_normal_line(self):
        """Standard order lines (is_click_and_collect=False) must not produce C&C pickings."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'is_click_and_collect': False,
            })]
        })
        order.action_confirm()
        cac_pickings = self.env['stock.picking'].search([
            ('origin', '=', order.name),
            ('is_click_and_collect_order', '=', True)
        ])
        self.assertEqual(len(cac_pickings), 0,
                         "No C&C picking should be created for a normal line.")
        self.assertEqual(order.collect_count, 0,
                         "collect_count must be 0 for orders with no C&C lines.")

    # ------------------------------------------------------------------
    # 6. Multiple C&C lines → multiple pickings
    # ------------------------------------------------------------------
    def test_10_multiple_cac_lines_create_multiple_pickings(self):
        """Each C&C order line should produce its own stock picking."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
                (0, 0, {
                    'product_id': self.product2.id,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
            ]
        })
        order.action_confirm()
        cac_pickings = self.env['stock.picking'].search([
            ('origin', '=', order.name),
            ('is_click_and_collect_order', '=', True)
        ])
        self.assertEqual(len(cac_pickings), 2,
                         "Two C&C lines must produce two separate C&C pickings.")
        self.assertEqual(order.collect_count, 2,
                         "collect_count must reflect 2 C&C pickings.")

    # ------------------------------------------------------------------
    # 7. Delivery count excludes C&C pickings
    # ------------------------------------------------------------------
    def test_11_delivery_count_excludes_cac_pickings(self):
        """Standard delivery_count must NOT include C&C pickings."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })]
        })
        order.action_confirm()
        non_cac_pickings = order.picking_ids.filtered(
            lambda p: not p.is_click_and_collect_order)
        self.assertEqual(
            order.delivery_count, len(non_cac_pickings),
            "delivery_count must only count non-C&C pickings."
        )

    # ------------------------------------------------------------------
    # 8. Smart Button Action
    # ------------------------------------------------------------------
    def test_12_action_view_click_and_collect_model_and_domain(self):
        """Smart button must return the correct model and domain filter."""
        self.sale_order.action_confirm()
        action = self.sale_order.action_view_click_and_collect()
        self.assertEqual(action['res_model'], 'stock.picking')
        self.assertEqual(action['domain'], [
            ('origin', '=', self.sale_order.name),
            ('is_click_and_collect_order', '=', True)
        ])

    def test_13_action_view_click_and_collect_action_type(self):
        """Smart button action must be a window action with list,form view."""
        action = self.sale_order.action_view_click_and_collect()
        self.assertEqual(action['type'], 'ir.actions.act_window',
                         "Action type must be ir.actions.act_window.")
        self.assertEqual(action['view_mode'], 'list,form',
                         "view_mode must be list,form.")
        self.assertEqual(action['name'], 'Click And Collect',
                         "Action name must be 'Click And Collect'.")

    # ------------------------------------------------------------------
    # 9. POS RPC: action_stock_picking returns correct data
    # ------------------------------------------------------------------
    def test_14_action_stock_picking_returns_correct_data(self):
        """action_stock_picking must return a list with correct product/partner info."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })]
        })
        order.action_confirm()
        line_id = order.order_line[0].id
        result = self.env['stock.picking'].action_stock_picking([line_id])
        self.assertIsInstance(result, list,
                              "action_stock_picking must return a list.")
        self.assertEqual(len(result), 1,
                         "Should return one record for one matching line.")
        data = result[0]
        self.assertEqual(data['id'], line_id)
        self.assertEqual(data['order_id'], order.name)
        self.assertEqual(data['partner_id'], self.partner.name)
        self.assertEqual(data['product_id'], self.product.name)
        self.assertEqual(data['product_uom_quantity'], 2)

    def test_15_action_stock_picking_empty_for_unknown_line(self):
        """action_stock_picking must return empty list for unknown line IDs."""
        result = self.env['stock.picking'].action_stock_picking([999999999])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0,
                         "No records should match a non-existent line ID.")

    # ------------------------------------------------------------------
    # 10. POS RPC: action_confirmation_click validates picking
    # ------------------------------------------------------------------
    def test_16_action_confirmation_click_returns_true(self):
        """action_confirmation_click must return True when a valid picking exists."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })]
        })
        order.action_confirm()
        line_id = order.order_line[0].id
        result = self.env['stock.picking'].action_confirmation_click(line_id)
        self.assertTrue(result,
                        "action_confirmation_click must return True on success.")

    def test_17_action_confirmation_click_returns_false_for_unknown_line(self):
        """action_confirmation_click must return False for a non-existent line."""
        result = self.env['stock.picking'].action_confirmation_click(999999999)
        self.assertFalse(result,
                         "action_confirmation_click must return False when no picking is found.")
