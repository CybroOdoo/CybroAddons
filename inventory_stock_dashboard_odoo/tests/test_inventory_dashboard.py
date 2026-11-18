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
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from odoo.addons.inventory_stock_dashboard_odoo.models import stock_quant
from odoo.addons.inventory_stock_dashboard_odoo.models.dashboard_utils import (
    localized_name,
)

DELIVERED_QTY = 100000.0


@tagged('post_install', '-at_install')
class TestInventoryDashboard(TransactionCase):
    """ Tests the data methods that feed the inventory dashboard."""

    @classmethod
    def _create_product(cls, name):
        return cls.env['product.product'].create({
            'name': name,
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.category.id,
        })

    @classmethod
    def _create_picking(cls, product, qty, **values):
        picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.out_type.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'move_ids': [Command.create({
                'product_id': product.id,
                'product_uom_qty': qty,
                'location_id': cls.stock_location.id,
                'location_dest_id': cls.customer_location.id,
            })],
            **values,
        })
        picking.action_confirm()
        return picking

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.out_type = warehouse.out_type_id
        cls.stock_location = warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        # Two internal locations with the same name but different parents.
        cls.shelf_a = cls.env['stock.location'].create({
            'name': 'Dashboard Shelf',
            'location_id': cls.stock_location.id,
            'usage': 'internal',
        })
        cls.shelf_b = cls.env['stock.location'].create({
            'name': 'Dashboard Shelf',
            'location_id': warehouse.view_location_id.id,
            'usage': 'internal',
        })
        cls.category = cls.env['product.category'].create(
            {'name': 'Dashboard Test Category'})
        cls.product = cls._create_product('Dashboard Test Product')
        cls.low_product = cls._create_product('Dashboard Low Product')
        cls.dead_product = cls._create_product('Dashboard Dead Product')
        cls.empty_product = cls._create_product('Dashboard Empty Product')
        cls.split_product = cls._create_product('Dashboard Split Product')
        quant = cls.env['stock.quant']
        quant._update_available_quantity(
            cls.product, cls.stock_location, DELIVERED_QTY * 2)
        quant._update_available_quantity(
            cls.low_product, cls.stock_location, 2.0)
        # The dead product is spread over three locations: 7 + 3 + 4.
        quant._update_available_quantity(
            cls.dead_product, cls.stock_location, 7.0)
        quant._update_available_quantity(cls.dead_product, cls.shelf_a, 3.0)
        quant._update_available_quantity(cls.dead_product, cls.shelf_b, 4.0)
        # Short in one location, but 8 units in total.
        quant._update_available_quantity(
            cls.split_product, cls.stock_location, 10.0)
        quant._update_available_quantity(cls.split_product, cls.shelf_a, -2.0)
        # A delivered picking.
        cls.done_picking = cls._create_picking(cls.product, DELIVERED_QTY)
        cls.done_picking.action_assign()
        cls.done_picking.move_ids.write(
            {'quantity': DELIVERED_QTY, 'picked': True})
        cls.done_picking.button_validate()
        # A waiting picking and a backorder of the delivered picking.
        cls.waiting_picking = cls._create_picking(cls.empty_product, 10.0)
        cls._create_picking(
            cls.empty_product, 1.0, backorder_id=cls.done_picking.id)
        # The dead product is old and has no outgoing moves.
        cls.env.flush_all()
        cls.env.cr.execute(
            "UPDATE product_product SET create_date = %s WHERE id = %s",
            (fields.Datetime.now() - timedelta(days=400),
             cls.dead_product.id))
        cls.env.invalidate_all()

    def _set_param(self, key, value):
        full_key = f'inventory_stock_dashboard_odoo.{key}'
        parameter = self.env['ir.config_parameter'].sudo()
        record = parameter.search([('key', '=', full_key)], limit=1)
        if record:
            record.value = value
        else:
            parameter.create({'key': full_key, 'value': value})

    def _create_user(self, login, group_xmlids):
        return self.env['res.users'].create({
            'name': login,
            'login': login,
            'group_ids': [Command.set(
                [self.env.ref(xmlid).id for xmlid in group_xmlids])],
        })

    def test_localized_name(self):
        self.assertEqual(
            localized_name({'en_US': 'Chair', 'fr_FR': 'Chaise'}, 'fr_FR'),
            'Chaise')
        self.assertEqual(
            localized_name({'en_US': 'Chair'}, 'fr_FR'), 'Chair')
        self.assertEqual(localized_name({'de_DE': 'Stuhl'}), 'Stuhl')
        self.assertEqual(localized_name({}), '')
        self.assertEqual(localized_name('{"en_US": "Chair"}'), 'Chair')
        self.assertEqual(localized_name('{broken'), '{broken')
        self.assertEqual(localized_name('Chair'), 'Chair')

    def test_access_rights(self):
        """ Only the Inventory users can read the dashboard data."""
        calls = [
            ('stock.move', 'get_the_top_products', ()),
            ('stock.move', 'stock_move_last_ten_days', (None,)),
            ('stock.move', 'get_dead_of_stock', ()),
            ('stock.move.line', 'get_product_moves', ()),
            ('stock.move.line', 'product_move_by_category',
             (self.category.id,)),
            ('stock.quant', 'get_out_of_stock', ()),
            ('stock.picking', 'get_operation_types', ()),
            ('stock.picking', 'get_product_category', ()),
            ('stock.picking', 'get_locations', ()),
        ]
        basic_user = self._create_user(
            'dashboard_basic_user', ['base.group_user'])
        for model, method, args in calls:
            with self.assertRaises(AccessError, msg=f'{model}.{method}'):
                getattr(self.env[model].with_user(basic_user), method)(*args)
        stock_user = self._create_user(
            'dashboard_stock_user',
            ['base.group_user', 'stock.group_stock_user'])
        result = self.env['stock.move'].with_user(
            stock_user).get_the_top_products()
        self.assertIn(self.product.name, result['products'])
        locations = self.env['stock.picking'].with_user(
            stock_user).get_locations()
        self.assertIn(self.stock_location.complete_name, locations)

    def test_top_products(self):
        move = self.env['stock.move']
        for method in (
                'get_the_top_products', 'top_products_last_ten',
                'top_products_last_thirty', 'top_products_last_three_months',
                'top_products_last_year'):
            result = getattr(move, method)()
            self.assertIn(self.product.name, result['products'], method)
            index = result['products'].index(self.product.name)
            self.assertEqual(result['count'][index], DELIVERED_QTY, method)

    def test_top_products_use_done_date(self):
        """ A delivery done 20 days ago is out of the last ten days."""
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE stock_move SET date = %s WHERE id = ANY(%s)",
            (fields.Datetime.now() - timedelta(days=20),
             self.done_picking.move_ids.ids))
        self.env.invalidate_all()
        move = self.env['stock.move']
        self.assertNotIn(
            self.product.name, move.top_products_last_ten()['products'])
        self.assertIn(
            self.product.name, move.top_products_last_thirty()['products'])

    def test_stock_moves_by_location(self):
        move = self.env['stock.move']
        for method in (
                'stock_move_last_ten_days', 'this_month',
                'last_three_month', 'last_year'):
            result = getattr(move, method)(None)
            self.assertIn(
                self.stock_location.complete_name, result['name'], method)
            self.assertEqual(len(result['name']), len(result['count']))
            index = result['name'].index(self.stock_location.complete_name)
            self.assertGreaterEqual(result['count'][index], 1, method)

    def test_product_moves(self):
        line = self.env['stock.move.line']
        # A reserved line is not a done move.
        reserved_picking = self._create_picking(self.low_product, 1.0)
        reserved_picking.action_assign()
        result = line.get_product_moves()
        self.assertEqual(
            len(result['category_id']), len(result['category_name']))
        self.assertIn(self.category.id, result['category_id'])
        self.assertIn('Dashboard Test Category', result['category_name'])
        for option in (self.category.id, str(self.category.id)):
            result = line.product_move_by_category(option)
            self.assertEqual(len(result['name']), len(result['count']))
            self.assertIn(self.product.name, result['name'])
            self.assertIn(DELIVERED_QTY, result['count'])
            self.assertNotIn(self.low_product.name, result['name'])
        self.assertEqual(
            line.product_move_by_category(None), {'name': [], 'count': []})

    def test_operation_types(self):
        picking = self.env['stock.picking']
        no_transfer, late, waiting, names, backorder = (
            picking.get_operation_types())
        self.assertGreaterEqual(no_transfer[self.out_type.id], 3)
        self.assertEqual(names[self.out_type.id], self.out_type.display_name)
        self.assertGreaterEqual(waiting[self.out_type.id], 1)
        self.assertGreaterEqual(backorder[self.out_type.id], 1)
        self.assertGreaterEqual(late[self.out_type.id], 1)
        # The "Late" link of the tile opens the transfers counted here.
        now = fields.Datetime.now()
        late_domain = [
            ('picking_type_id', '=', self.out_type.id),
            ('state', 'in', ('assigned', 'waiting', 'confirmed')),
            '|', '|',
            ('has_deadline_issue', '=', True),
            ('date_deadline', '<=', now),
            ('scheduled_date', '<=', now),
        ]
        self.assertEqual(
            picking.search_count(late_domain), late[self.out_type.id])

    def test_categories_and_locations(self):
        picking = self.env['stock.picking']
        result = picking.get_product_category()
        self.assertEqual(len(result['name']), len(result['count']))
        index = result['name'].index(self.category.display_name)
        quants = self.env['stock.quant'].search([
            ('product_id.categ_id', '=', self.category.id),
            ('location_id.usage', '=', 'internal')])
        self.assertAlmostEqual(
            result['count'][index], sum(quants.mapped('quantity')))
        locations = picking.get_locations()
        self.assertIn(self.stock_location.complete_name, locations)
        # Locations with the same name are not merged.
        self.assertNotEqual(
            self.shelf_a.complete_name, self.shelf_b.complete_name)
        self.assertAlmostEqual(locations[self.shelf_a.complete_name], 1.0)
        self.assertAlmostEqual(locations[self.shelf_b.complete_name], 4.0)

    def test_out_of_stock(self):
        quant = self.env['stock.quant']
        self.assertIsNone(quant.get_out_of_stock())
        self._set_param('out_of_stock', 'True')
        self._set_param('out_of_stock_quantity', '5')
        with patch.object(stock_quant, 'OUT_OF_STOCK_LIMIT', 1000000):
            result = quant.get_out_of_stock()
        names = result['product_name']
        self.assertEqual(len(names), len(result['total_quantity']))
        self.assertIn(self.low_product.display_name, names)
        # A product that never had stock is out of stock too.
        self.assertIn(self.empty_product.display_name, names)
        self.assertNotIn(self.product.display_name, names)
        self.assertNotIn(self.dead_product.display_name, names)
        # 10 units in one location and -2 in another: 8 units in total.
        self.assertNotIn(self.split_product.display_name, names)
        with patch.object(stock_quant, 'OUT_OF_STOCK_LIMIT', 1):
            self.assertEqual(len(quant.get_out_of_stock()['product_name']), 1)

    def test_dead_stock(self):
        move = self.env['stock.move']
        self.assertIsNone(move.get_dead_of_stock())
        self._set_param('dead_stock_bol', 'True')
        self._set_param('dead_stock', '1')
        for period in ('day', 'week', 'month', 'unknown'):
            self._set_param('dead_stock_type', period)
            result = move.get_dead_of_stock()
            names = result['product_name']
            self.assertEqual(len(names), len(result['total_quantity']))
            # One row per product, with the quantity of all the locations.
            self.assertEqual(names.count(self.dead_product.display_name), 1)
            index = names.index(self.dead_product.display_name)
            self.assertAlmostEqual(result['total_quantity'][index], 14.0)
            self.assertNotIn(self.product.display_name, names)
