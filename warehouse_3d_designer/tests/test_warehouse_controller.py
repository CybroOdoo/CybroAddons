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
import json

from odoo.tests import HttpCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestWarehouseController(HttpCase):
    """Test the save, export and import routes as real users."""

    @classmethod
    def setUpClass(cls):
        """Create a layout, a manager and an inventory user."""
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env, login='wh_manager', groups='stock.group_stock_manager')
        cls.stock_user = new_test_user(
            cls.env, login='wh_user', groups='stock.group_stock_user')
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Designer Test', 'code': 'DTW'})
        cls.layout = cls.env['warehouse.layout'].create({
            'name': 'Ground Floor',
            'warehouse_id': cls.warehouse.id,
        })
        stock = cls.warehouse.lot_stock_id
        cls.location = cls.env['stock.location'].create({
            'name': 'Rack A', 'location_id': stock.id})
        cls.child = cls.env['stock.location'].create({
            'name': 'Bin 1', 'location_id': cls.location.id})
        cls.other = cls.env['stock.location'].create({
            'name': 'Rack B', 'location_id': stock.id})

    def _call(self, route, **params):
        """Call a jsonrpc route and return its result."""
        response = self.url_open(
            route,
            data=json.dumps({'params': params}),
            headers={'Content-Type': 'application/json'},
        )
        return response.json()

    def _save_positions(self, positions, removed_ids=None):
        """Save positions on the layout."""
        return self._call(
            '/warehouse_3d/save_positions', layout_id=self.layout.id,
            positions=positions, removed_ids=removed_ids)

    def _import(self, content, filename='layout.xml'):
        """Upload a file to the import route."""
        return self.url_open(
            '/warehouse_3d/import_layout',
            data={
                'layout_id': self.layout.id,
                'csrf_token': self.csrf_token(),
            },
            files={'file': (filename, content)},
        )

    def _export(self):
        """Download the export of the layout."""
        return self.url_open(
            f'/warehouse_3d/export_layout?layout_id={self.layout.id}')

    def test_01_save_positions(self):
        """Positions of a location and its children are saved."""
        self.authenticate('wh_manager', 'wh_manager')
        result = self._call(
            '/warehouse_3d/save_positions', layout_id=self.layout.id,
            positions=[{
                'id': self.location.id, 'pos_x': 5, 'pos_y': 6,
                'location_shape': 'shelf', 'shelf_rows': 3,
                'children': [{'id': self.child.id, 'pos_x': 1}],
            }],
        )['result']
        self.assertTrue(result['success'])
        self.assertEqual(result['updated_count'], 1)
        self.assertEqual(self.location.layout_id, self.layout)
        self.assertEqual((self.location.pos_x, self.location.pos_y), (5, 6))
        self.assertEqual(self.location.shelf_rows, 3)
        self.assertEqual(self.child.pos_x, 1)

    def test_02_removed_location_leaves_the_layout(self):
        """A location removed from the canvas stays removed after saving."""
        self.location.write({'layout_id': self.layout.id, 'pos_x': 9})
        self.authenticate('wh_manager', 'wh_manager')
        result = self._save_positions([], [self.location.id])['result']
        self.assertEqual(result['removed_count'], 1)
        self.assertFalse(self.location.layout_id)
        self.assertEqual(self.location.pos_x, 0)

    def test_03_removed_then_placed_again(self):
        """Removing a location and placing it again keeps it placed."""
        self.location.layout_id = self.layout
        self.authenticate('wh_manager', 'wh_manager')
        self._save_positions([{'id': self.location.id}], [self.location.id])
        self.assertEqual(self.location.layout_id, self.layout)

    def test_04_removal_is_limited_to_the_layout(self):
        """A location of another layout cannot be removed from here."""
        other_layout = self.layout.copy({'floor_level': 1})
        self.location.layout_id = other_layout
        self.authenticate('wh_manager', 'wh_manager')
        self._save_positions([], [self.location.id])
        self.assertEqual(self.location.layout_id, other_layout)

    def test_05_foreign_warehouse_location_is_ignored(self):
        """Locations of another warehouse are not placed on this layout."""
        other_warehouse = self.env['stock.warehouse'].create({
            'name': 'Second', 'code': 'WH2'})
        location = other_warehouse.lot_stock_id
        self.authenticate('wh_manager', 'wh_manager')
        result = self._save_positions([{'id': location.id}])['result']
        self.assertEqual(result['updated_count'], 0)
        self.assertFalse(location.layout_id)

    def test_06_inventory_user_cannot_save(self):
        """The read-only users cannot change a layout through the routes."""
        self.authenticate('wh_user', 'wh_user')
        for route, params in (
                ('/warehouse_3d/save_positions',
                 {'positions': [{'id': self.location.id}]}),
                ('/warehouse_3d/save_map_objects',
                 {'objects': [{'id': -1, 'name': 'Wall'}]})):
            with mute_logger('odoo.http'):
                response = self._call(
                    route, layout_id=self.layout.id, **params)
            self.assertIn('error', response)
        self.assertFalse(self.location.layout_id)
        self.assertFalse(self.layout.map_object_ids)

    def test_07_missing_layout(self):
        """Saving on a deleted layout reports it."""
        self.authenticate('wh_manager', 'wh_manager')
        for route, params in (
                ('/warehouse_3d/save_positions', {'positions': []}),
                ('/warehouse_3d/save_map_objects', {'objects': []})):
            result = self._call(route, layout_id=999999, **params)['result']
            self.assertFalse(result['success'])

    def test_08_new_map_object_is_not_duplicated(self):
        """Saving twice updates the new object instead of creating it twice,
        using the record ID returned for its temporary ID."""
        self.authenticate('wh_manager', 'wh_manager')
        obj = {'id': -1234, 'name': 'Wall', 'object_type': 'wall'}
        route = '/warehouse_3d/save_map_objects'
        result = self._call(
            route, layout_id=self.layout.id, objects=[obj])['result']
        self.assertEqual(result['created_count'], 1)
        record_id = result['created_ids']['-1234']
        obj.update(id=record_id, pos_x=8)
        result = self._call(
            route, layout_id=self.layout.id, objects=[obj])['result']
        self.assertEqual(result['updated_count'], 1)
        self.assertEqual(len(self.layout.map_object_ids), 1)
        self.assertEqual(self.layout.map_object_ids.pos_x, 8)

    def test_09_map_object_removal(self):
        """Only objects of this layout are deleted or updated."""
        other_layout = self.layout.copy({'floor_level': 1})
        Object = self.env['warehouse.map.object']
        mine = Object.create({'name': 'Mine', 'layout_id': self.layout.id})
        foreign = Object.create({'name': 'Foreign',
                                 'layout_id': other_layout.id})
        self.authenticate('wh_manager', 'wh_manager')
        result = self._call(
            '/warehouse_3d/save_map_objects', layout_id=self.layout.id,
            objects=[{'id': foreign.id, 'name': 'Taken'}],
            removed_ids=[mine.id, foreign.id])['result']
        self.assertEqual(result['removed_count'], 1)
        self.assertFalse(mine.exists())
        self.assertEqual(foreign.name, 'Foreign')
        self.assertEqual(foreign.layout_id, other_layout)

    def test_10_export(self):
        """The export is an XML file named after the layout."""
        self.location.write({'layout_id': self.layout.id, 'pos_x': 12})
        self.authenticate('wh_manager', 'wh_manager')
        response = self._export()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ground_Floor_all_floors.xml',
                      response.headers['Content-Disposition'])
        self.assertIn('Rack A', response.text)
        self.assertIn('<field name="pos_x">12</field>', response.text)

    def test_11_export_escapes_names(self):
        """Special characters cannot break the file or its header."""
        self.layout.name = 'A & B "<1>"'
        self.authenticate('wh_manager', 'wh_manager')
        response = self._export()
        self.assertEqual(response.status_code, 200)
        self.assertIn('A &amp; B', response.text)

    def test_12_round_trip_restores_the_layout(self):
        """Locations without external ID and map objects come back from an
        exported file, and importing it twice does not duplicate objects."""
        self.location.write({'layout_id': self.layout.id, 'pos_x': 12,
                             'location_shape': 'shelf'})
        self.env['warehouse.map.object'].create({
            'name': 'North Wall', 'layout_id': self.layout.id,
            'is_flipped': True})
        self.authenticate('wh_manager', 'wh_manager')
        content = self._export().content

        self.location.write({'layout_id': False, 'pos_x': 0,
                             'location_shape': 'rack'})
        self.layout.map_object_ids.unlink()

        for _attempt in range(2):
            result = self._import(content).json()
            self.assertTrue(result['success'], result)
            self.assertEqual(result['skipped_locations'], 0)
            self.assertEqual(result['matched_locations'], 2)
        self.assertEqual(self.location.layout_id, self.layout)
        self.assertEqual(self.location.pos_x, 12)
        self.assertEqual(self.location.location_shape, 'shelf')
        self.assertEqual(len(self.layout.map_object_ids), 1)
        self.assertTrue(self.layout.map_object_ids.is_flipped)

    def test_13_import_creates_new_floors(self):
        """A floor missing in the warehouse is created."""
        content = b"""<?xml version="1.0"?><odoo><data>
            <record id="f2" model="warehouse.layout">
                <field name="name">Second Floor</field>
                <field name="floor_level">2</field>
                <field name="canvas_width">50</field>
            </record>
        </data></odoo>"""
        self.authenticate('wh_manager', 'wh_manager')
        self.assertTrue(self._import(content).json()['success'])
        floor = self.env['warehouse.layout'].search([
            ('warehouse_id', '=', self.warehouse.id),
            ('floor_level', '=', 2),
        ])
        self.assertEqual(floor.name, 'Second Floor')
        self.assertEqual(floor.canvas_width, 50)

    def test_14_import_refuses_other_files(self):
        """Files that are not XML, or are not valid, are refused."""
        self.authenticate('wh_manager', 'wh_manager')
        response = self._import(b'hello', 'layout.txt')
        self.assertEqual(response.status_code, 400)
        response = self._import(b'<odoo><broken>')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_15_import_is_all_or_nothing(self):
        """A wrong value reports an error and changes nothing."""
        content = b"""<odoo>
            <record id="f0" model="warehouse.layout">
                <field name="name">Renamed</field>
                <field name="grid_size">abc</field>
            </record>
        </odoo>"""
        self.authenticate('wh_manager', 'wh_manager')
        response = self._import(content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.layout.name, 'Ground Floor')

    def test_16_import_rolls_back_invalid_values(self):
        """Values refused by the database do not end in a server error."""
        content = b"""<odoo>
            <record id="f0" model="warehouse.layout">
                <field name="name">Renamed</field>
                <field name="grid_size">1</field>
            </record>
        </odoo>"""
        self.authenticate('wh_manager', 'wh_manager')
        with mute_logger('odoo.sql_db'):
            response = self._import(content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.layout.name, 'Ground Floor')

    def test_17_import_only_touches_locations(self):
        """An external ID of another model in a location record is skipped,
        as is a location of another company."""
        other_company = self.env['res.company'].create({'name': 'Other Co'})
        foreign = self.env['stock.location'].create({
            'name': 'Foreign', 'company_id': other_company.id,
            'usage': 'internal'})
        foreign_xml_id = self.env['ir.model.data'].create({
            'module': 'wh_test', 'name': 'foreign', 'model': 'stock.location',
            'res_id': foreign.id,
        }).complete_name
        content = f"""<odoo>
            <record id="base.user_admin" model="stock.location">
                <field name="pos_x">5</field>
            </record>
            <record id="{foreign_xml_id}" model="stock.location">
                <field name="pos_x">5</field>
            </record>
        </odoo>""".encode()
        self.authenticate('wh_manager', 'wh_manager')
        with mute_logger('odoo.addons.warehouse_3d_designer.controllers.'
                         'warehouse_3d_designer'):
            result = self._import(content).json()
        self.assertEqual(result['matched_locations'], 0)
        self.assertEqual(result['skipped_locations'], 2)
        self.assertFalse(foreign.sudo().layout_id)

    def test_18_import_ignores_entities(self):
        """External entities of an uploaded file are not read."""
        content = b"""<?xml version="1.0"?>
            <!DOCTYPE odoo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
            <odoo>
            <record id="f0" model="warehouse.layout">
                <field name="notes">&xxe;</field>
            </record>
            </odoo>"""
        self.authenticate('wh_manager', 'wh_manager')
        self._import(content)
        self.assertNotIn('root:', self.layout.notes or '')

    def test_19_inventory_user_cannot_import(self):
        """The read-only users cannot import."""
        self.authenticate('wh_user', 'wh_user')
        response = self._import(b'<odoo/>')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

    def test_20_import_needs_csrf_token(self):
        """A forged upload from another site is refused."""
        self.authenticate('wh_manager', 'wh_manager')
        with mute_logger('odoo.http'):
            response = self.url_open(
                '/warehouse_3d/import_layout',
                data={'layout_id': self.layout.id},
                files={'file': ('layout.xml', b'<odoo/>')},
            )
        self.assertEqual(response.status_code, 400)

    def test_21_missing_layout_routes(self):
        """Export and import of a deleted layout report it."""
        self.authenticate('wh_manager', 'wh_manager')
        with mute_logger('odoo.http'):
            response = self.url_open(
                '/warehouse_3d/export_layout?layout_id=999999')
        self.assertEqual(response.status_code, 404)
        response = self.url_open(
            '/warehouse_3d/import_layout',
            data={'layout_id': 999999,
                  'csrf_token': self.csrf_token()},
            files={'file': ('layout.xml', b'<odoo/>')},
        )
        self.assertEqual(response.status_code, 404)

    def test_22_round_trip_with_two_layouts_on_a_floor(self):
        """Layouts sharing a floor keep their own locations."""
        zone = self.layout.copy({'name': 'Cold Zone'})
        self.location.layout_id = self.layout
        self.other.layout_id = zone
        self.authenticate('wh_manager', 'wh_manager')
        content = self._export().content
        (self.location | self.other).layout_id = False
        self.assertTrue(self._import(content).json()['success'])
        self.assertEqual(self.location.layout_id, self.layout)
        self.assertEqual(self.other.layout_id, zone)
