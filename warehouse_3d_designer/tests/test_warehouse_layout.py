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

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import BinaryBytes, mute_logger


@tagged('post_install', '-at_install')
class TestWarehouseLayout(TransactionCase):
    """Test the layout data, the heatmap and the product search."""

    @classmethod
    def setUpClass(cls):
        """Create a layout with a rack holding stock in a sub-location."""
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Designer Test', 'code': 'DTW'})
        cls.layout = cls.env['warehouse.layout'].create({
            'name': 'Ground Floor',
            'warehouse_id': cls.warehouse.id,
        })
        cls.rack = cls.env['stock.location'].create({
            'name': 'Rack A',
            'location_id': cls.warehouse.lot_stock_id.id,
            'layout_id': cls.layout.id,
            'pos_x': 3,
            'pos_y': 4,
        })
        cls.bin = cls.env['stock.location'].create({
            'name': 'Bin 1',
            'location_id': cls.rack.id,
        })
        cls.deep_bin = cls.env['stock.location'].create({
            'name': 'Box 9',
            'location_id': cls.bin.id,
        })
        cls.free = cls.env['stock.location'].create({
            'name': 'Unplaced Shelf',
            'location_id': cls.warehouse.lot_stock_id.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Blue Widget',
            'default_code': 'BW-1',
            'is_storable': True,
        })
        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.rack, 25)
        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.bin, 5)
        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.deep_bin, 2)

    def test_01_defaults_and_company(self):
        """A layout takes the company of its warehouse."""
        self.assertEqual(self.layout.company_id, self.warehouse.company_id)
        self.assertEqual(self.layout.location_count, 1)
        self.assertEqual(self.layout.canvas_width, 40)

    def test_02_constraints(self):
        """Canvas settings out of range are refused."""
        for vals in ({'grid_size': 5}, {'canvas_width': 0},
                     {'canvas_height': -1}, {'cell_size_cm': 0}):
            with self.subTest(vals=vals), mute_logger('odoo.sql_db'):
                with self.assertRaises(IntegrityError), self.cr.savepoint():
                    self.layout.write(vals)
                    self.layout.flush_recordset()

    def test_03_open_designer(self):
        """The button opens the designer client action on this layout."""
        action = self.layout.action_open_designer()
        self.assertEqual(action['tag'], 'warehouse_designer')
        self.assertEqual(action['context']['default_layout_id'],
                         self.layout.id)

    def test_04_location_shape_defaults(self):
        """Choosing a shape sets its default size and color."""
        location = self.env['stock.location'].new({'location_shape': 'zone'})
        location._onchange_location_shape()
        self.assertEqual((location.size_x, location.size_y), (6, 4))
        self.assertEqual(location.location_color, '#DDA0DD')

    def test_05_map_object_type_defaults(self):
        """Choosing an object type sets its default look and takes the
        company of the layout."""
        obj = self.env['warehouse.map.object'].new({'object_type': 'room'})
        obj._onchange_object_type()
        self.assertEqual((obj.size_x, obj.size_y), (4, 3))
        self.assertEqual(obj.color, '#7F8C8D')
        record = self.env['warehouse.map.object'].create({
            'name': 'Office',
            'layout_id': self.layout.id,
        })
        self.assertEqual(record.company_id, self.layout.company_id)

    def test_06_copied_location_is_not_placed(self):
        """A duplicated location does not land on top of the original."""
        self.assertFalse(self.rack.copy().layout_id)

    def test_07_layout_data(self):
        """Placed locations carry their position, children and products;
        unplaced ones are offered, without children of placed locations."""
        data = self.layout.get_layout_data()
        self.assertEqual(data['layout']['name'], 'Ground Floor')
        self.assertEqual(data['sibling_floors'][0]['id'], self.layout.id)
        placed = {loc['id']: loc for loc in data['locations']}
        self.assertEqual(list(placed), [self.rack.id])
        rack = placed[self.rack.id]
        self.assertEqual((rack['pos_x'], rack['pos_y']), (3, 4))
        self.assertEqual([c['id'] for c in rack['children']], [self.bin.id])
        self.assertEqual(len(rack['product_summary']), 1)
        self.assertEqual(rack['product_summary'][0]['qty'], 30)
        unplaced = [loc['id'] for loc in data['unplaced_locations']]
        self.assertIn(self.free.id, unplaced)
        self.assertNotIn(self.bin.id, unplaced)
        self.assertFalse(data['layout']['background_image'])

    def test_08_layout_data_with_floor_plan_and_objects(self):
        """The floor plan is sent as base64 text and objects are listed."""
        self.layout.background_image = BinaryBytes(base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
            '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='))
        self.env['warehouse.map.object'].create({
            'name': 'North Wall',
            'layout_id': self.layout.id,
            'pos_x': 7,
        })
        data = self.layout.get_layout_data()
        self.assertIsInstance(data['layout']['background_image'], str)
        self.assertEqual(data['map_objects'][0]['name'], 'North Wall')
        self.assertEqual(data['map_objects'][0]['pos_x'], 7)

    def test_09_heatmap_default_capacity(self):
        """Without storage category the capacity is 100 units."""
        heatmap = self.layout.get_heatmap_data()
        self.assertEqual(heatmap[self.rack.id]['qty'], 25)
        self.assertEqual(heatmap[self.rack.id]['product_count'], 1)
        self.assertEqual(heatmap[self.rack.id]['fill_pct'], 25)
        self.assertEqual(heatmap[self.bin.id]['fill_pct'], 5)

    def test_10_heatmap_storage_category_capacity(self):
        """The capacity comes from the storage category, capped at 100%."""
        category = self.env['stock.storage.category'].create({
            'name': 'Small Rack',
            'product_capacity_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 10,
            })],
        })
        self.rack.storage_category_id = category
        self.assertEqual(
            self.layout.get_heatmap_data()[self.rack.id]['fill_pct'], 100)

    def test_11_heatmap_empty_layout(self):
        """A layout without locations has no heatmap."""
        empty = self.layout.copy({'floor_level': 1})
        self.assertEqual(empty.get_heatmap_data(), {})

    def test_12_search_product(self):
        """Products are found by name and by reference."""
        for query in ('Blue Wid', 'BW-1'):
            results = self.layout.search_product_locations(query)
            self.assertEqual(results[0]['product_id'], self.product.id)
        self.assertFalse(self.layout.search_product_locations('nothing'))
        self.assertFalse(self.layout.search_product_locations(''))

    def test_13_search_finds_stock_in_sub_locations(self):
        """Stock in a sub-location points to the placed location, which is
        the one the designer can highlight, and names the real location."""
        results = self.layout.search_product_locations('Blue Widget')
        self.assertEqual(len(results), 3)
        self.assertEqual({r['location_id'] for r in results}, {self.rack.id})
        self.assertIn(self.deep_bin.complete_name,
                      [r['location_name'] for r in results])

    def test_14_search_empty_layout(self):
        """A layout without locations finds nothing."""
        empty = self.layout.copy({'floor_level': 1})
        self.assertFalse(empty.search_product_locations('Blue'))

    def test_15_inventory_user_reads_layouts(self):
        """Inventory users use the read-only map, and cannot edit it."""
        user = new_test_user(
            self.env, login='map_user', groups='stock.group_stock_user')
        layout = self.layout.with_user(user)
        self.assertEqual(layout.get_layout_data()['layout']['id'], layout.id)
        self.assertTrue(layout.get_heatmap_data())
        self.assertTrue(layout.search_product_locations('Blue'))
        with self.assertRaises(AccessError):
            layout.name = 'Changed'

    def test_16_other_company_is_hidden(self):
        """Layouts and map objects stay inside their company."""
        self.env['warehouse.map.object'].create({
            'name': 'North Wall',
            'layout_id': self.layout.id,
        })
        other_company = self.env['res.company'].create({'name': 'Other Co'})
        user = new_test_user(
            self.env, login='other_manager',
            groups='stock.group_stock_manager',
            company_id=other_company.id, company_ids=[other_company.id])
        self.assertFalse(
            self.env['warehouse.layout'].with_user(user).search([
                ('id', '=', self.layout.id)]))
        self.assertFalse(
            self.env['warehouse.map.object'].with_user(user).search([
                ('layout_id', '=', self.layout.id)]))
