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
#############################################################################
import base64
from datetime import timedelta

from lxml import etree

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.binary import BinaryBytes
from odoo.tools.safe_eval import safe_eval

# 1x1 transparent PNG used as product image.
PNG_IMAGE = BinaryBytes(base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
    '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='))

MODULE = 'odoo_picking_order_line_views'


@tagged('post_install', '-at_install')
class TestPickingOrderLineViews(TransactionCase):
    """Test suite for the picking order line views,

    covering the related fields added on the move lines and moves, the
    reserved quantity per line, the stored fields used for grouping, the
    incoming and outgoing actions, the views and the menus.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Line View Product A',
            'is_storable': True,
            'image_1920': PNG_IMAGE,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Line View Product B',
            'is_storable': True,
        })
        quant_model = cls.env['stock.quant']
        quant_model._update_available_quantity(
            cls.product_a, cls.stock_location, 5.0)
        quant_model._update_available_quantity(
            cls.product_b, cls.stock_location, 50.0)

    def _create_picking(self, picking_type, location, location_dest,
                        lines, **vals):
        """Create, confirm and reserve a picking with the given lines."""
        picking = self.env['stock.picking'].create(dict({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
            'move_ids': [Command.create({
                'product_id': product.id,
                'product_uom_qty': qty,
                'location_id': location.id,
                'location_dest_id': location_dest.id,
            }) for product, qty in lines],
        }, **vals))
        picking.action_confirm()
        picking.action_assign()
        return picking

    def _create_delivery(self, **vals):
        """Return a reserved delivery of products A and B."""
        return self._create_picking(
            self.warehouse.out_type_id, self.stock_location,
            self.customer_location,
            [(self.product_a, 5.0), (self.product_b, 30.0)], **vals)

    def _create_receipt(self):
        """Return a reserved receipt of product A."""
        return self._create_picking(
            self.warehouse.in_type_id, self.supplier_location,
            self.stock_location, [(self.product_a, 3.0)])

    def _get_line(self, picking, product):
        """Return the move line of the given product in the picking."""
        return picking.move_line_ids.filtered(
            lambda line: line.product_id == product)

    def test_01_picking_related_fields(self):
        """Verify the move line shows the dates, type and source of its
        picking.
        """
        deadline = fields.Datetime.now() + timedelta(days=3)
        picking = self._create_delivery(
            origin='TEST-SO-001', date_deadline=deadline)
        line = self._get_line(picking, self.product_a)
        self.assertEqual(line.scheduled_date, picking.scheduled_date)
        self.assertEqual(line.picking_type_id, self.warehouse.out_type_id)
        self.assertEqual(line.code, 'outgoing')
        self.assertEqual(line.origin, 'TEST-SO-001')
        self.assertEqual(line.date_deadline, picking.date_deadline)
        self.assertFalse(line.has_deadline_issue)
        self.assertFalse(line.date_done)

    def test_02_effective_date_after_validation(self):
        """Verify the effective date is set once the picking is done."""
        picking = self._create_delivery()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        line = self._get_line(picking, self.product_a)
        self.assertTrue(line.date_done)
        self.assertEqual(line.date_done, picking.date_done)

    def test_03_reserved_matches_own_move(self):
        """Verify each line shows the availability of its own move, not the
        one of the first move of the picking.
        """
        picking = self._create_delivery()
        line_a = self._get_line(picking, self.product_a)
        line_b = self._get_line(picking, self.product_b)
        self.assertEqual(line_a.reserved_available,
                         line_a.move_id.forecast_availability)
        self.assertEqual(line_b.reserved_available,
                         line_b.move_id.forecast_availability)
        self.assertEqual(line_b.reserved_available, 30.0)

    def test_04_origin_kept_without_picking(self):
        """Verify a move line without picking keeps the source of its move."""
        move = self.env['stock.move'].create({
            'product_id': self.product_b.id,
            'product_uom_qty': 2.0,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'origin': 'TEST-MOVE-ORIGIN',
        })
        move._action_confirm()
        move._action_assign()
        self.assertTrue(move.move_line_ids)
        self.assertFalse(move.move_line_ids.picking_id)
        self.assertEqual(move.move_line_ids.origin, 'TEST-MOVE-ORIGIN')

    def test_05_product_image_on_lines_and_moves(self):
        """Verify the move and its lines show the product image."""
        picking = self._create_delivery()
        line = self._get_line(picking, self.product_a)
        image = bytes(self.product_a.image_1920)
        self.assertTrue(image)
        self.assertEqual(bytes(line.move_line_image), image)
        self.assertEqual(bytes(line.move_id.move_line_image), image)
        self.assertFalse(self._get_line(
            picking, self.product_b).move_line_image)

    def test_06_stored_fields_can_be_grouped(self):
        """Verify the stored fields used by the group by filters work."""
        self._create_delivery(origin='TEST-SO-GROUP')
        fields_model = self.env['stock.move.line']._fields
        for name in ('scheduled_date', 'picking_type_id', 'origin'):
            self.assertTrue(fields_model[name].store, name)
        groups = self.env['stock.move.line'].formatted_read_group(
            [('origin', '=', 'TEST-SO-GROUP')],
            groupby=['origin', 'picking_type_id'], aggregates=['__count'])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['__count'], 2)

    def test_07_incoming_action_shows_receipt_lines(self):
        """Verify the incoming action lists receipt lines only."""
        receipt = self._create_receipt()
        delivery = self._create_delivery()
        action = self.env.ref(f'{MODULE}.stock_move_in_views_action')
        lines = self.env['stock.move.line'].search(
            safe_eval(action.domain))
        self.assertTrue(receipt.move_line_ids <= lines)
        self.assertFalse(delivery.move_line_ids & lines)

    def test_08_outgoing_action_shows_delivery_lines(self):
        """Verify the outgoing action lists delivery lines only."""
        receipt = self._create_receipt()
        delivery = self._create_delivery()
        action = self.env.ref(f'{MODULE}.stock_move_out_views_action')
        lines = self.env['stock.move.line'].search(
            safe_eval(action.domain))
        self.assertTrue(delivery.move_line_ids <= lines)
        self.assertFalse(receipt.move_line_ids & lines)

    def test_09_actions_use_module_views(self):
        """Verify both actions open the same module list, kanban, form,
        pivot, graph and calendar views and the module search view.
        """
        expected = {
            mode: self.env.ref(
                f'{MODULE}.stock_move_line_operation_view_{mode}').id
            for mode in ('list', 'kanban', 'form', 'pivot', 'graph',
                         'calendar')
        }
        search_view = self.env.ref(
            f'{MODULE}.stock_move_line_operation_view_search')
        for direction in ('in', 'out'):
            action = self.env.ref(
                f'{MODULE}.stock_move_{direction}_views_action')
            views = {mode: view_id for view_id, mode in action.views}
            self.assertEqual(views, expected)
            self.assertIn('calendar', action.view_mode)
            self.assertEqual(action.search_view_id, search_view)

    def test_10_module_views_load(self):
        """Verify every view of the module can be loaded."""
        views = self.env['ir.ui.view'].search([
            ('model', '=', 'stock.move.line'),
            ('id', 'in', self.env['ir.model.data'].search([
                ('module', '=', MODULE), ('model', '=', 'ir.ui.view'),
            ]).mapped('res_id')),
        ])
        self.assertEqual(len(views), 7)
        for view in views:
            arch = self.env['stock.move.line'].get_view(
                view_id=view.id, view_type=view.type)['arch']
            self.assertTrue(arch, view.name)

    def test_11_search_filters_have_unique_names(self):
        """Verify the search filters have unique names, so 'To Do' and
        'Ready' can be used separately.
        """
        view = self.env.ref(f'{MODULE}.stock_move_line_operation_view_search')
        names = etree.fromstring(view.arch_db).xpath('//filter/@name')
        self.assertEqual(len(names), len(set(names)))
        self.assertIn('ready', names)

    def test_12_picking_form_shows_product_image(self):
        """Verify the picking form view shows the product image on moves."""
        arch = self.env['stock.picking'].get_view(
            view_id=self.env.ref('stock.view_picking_form').id)['arch']
        self.assertIn('move_line_image', arch)

    def test_13_menus_for_stock_users(self):
        """Verify both menus are under inventory and for stock users."""
        stock_user = self.env.ref('stock.group_stock_user')
        for xmlid in ('menu_stock_move_in', 'menu_stock_move_out'):
            menu = self.env.ref(f'{MODULE}.{xmlid}')
            self.assertEqual(
                menu.parent_id, self.env.ref('stock.menu_stock_warehouse_mgmt'))
            self.assertIn(stock_user, menu.group_ids)

    def test_14_search_and_group_by_category(self):
        """Verify the Category search and group by of the search views work
        with the standard product category field.
        """
        category = self.env['product.category'].create({
            'name': 'Test Line View Category',
        })
        self.product_b.categ_id = category
        picking = self._create_delivery()
        line_b = self._get_line(picking, self.product_b)
        move_lines = self.env['stock.move.line']
        self.assertEqual(
            move_lines.search([('product_category_id', 'ilike',
                                'Test Line View Category')]), line_b)
        groups = move_lines.formatted_read_group(
            [('picking_id', '=', picking.id)],
            groupby=['product_category_id'], aggregates=['__count'])
        counts = {(group['product_category_id'] or [False])[0]:
                  group['__count'] for group in groups}
        self.assertEqual(counts[category.id], 1)
        self.assertEqual(sum(counts.values()), 2)
        arch = self.env['stock.move.line'].get_view(
            view_id=self.env.ref(
                f'{MODULE}.stock_move_line_operation_view_search').id,
            view_type='search')['arch']
        self.assertIn('product_category_id', arch)
