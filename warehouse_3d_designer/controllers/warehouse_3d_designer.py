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
import logging
from xml.sax.saxutils import escape

from lxml import etree
from psycopg2 import IntegrityError

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.http.stream import content_disposition

_logger = logging.getLogger(__name__)

LAYOUT_INT_FIELDS = ('canvas_width', 'canvas_height', 'grid_size',
                     'cell_size_cm', 'floor_level')


def _xml_field(name, value):
    """Return an export ``<field>`` line with its value XML-escaped."""
    return f'            <field name="{name}">{escape(str(value))}</field>'


def _node_text(record_node, field_name):
    """Return the text of a field of an imported record, or ``None``."""
    node = record_node.find(f"field[@name='{field_name}']")
    return node.text if node is not None and node.text else None


class WarehouseDesignerController(http.Controller):
    """Controller for the Warehouse 3D Designer client actions."""

    def _get_writable_layout(self, layout_id):
        """Return the layout if it exists and the user may edit it."""
        layout = request.env['warehouse.layout'].browse(layout_id).exists()
        if layout:
            layout.check_access('write')
        return layout

    @http.route('/warehouse_3d/save_positions', type='jsonrpc', auth='user')
    def save_positions(self, layout_id, positions, removed_ids=None):
        """Batch save location positions from the designer canvas."""
        Location = request.env['stock.location']

        layout = self._get_writable_layout(layout_id)
        if not layout:
            return {
                'success': False,
                'error': request.env._('Layout not found'),
            }

        positions = positions or []
        removed_ids = removed_ids or []

        # --- Batch update placed locations ---
        loc_ids = [p['id'] for p in positions]
        child_ids_all = []
        for p in positions:
            child_ids_all.extend(c['id'] for c in p.get('children', []))

        # Only locations of this warehouse, this layout or their children
        # can be placed, whatever IDs the request contains
        all_locs = Location.search([
            ('id', 'in', loc_ids + child_ids_all),
            '|', '|',
            ('layout_id', '=', layout.id),
            ('warehouse_id', '=', layout.warehouse_id.id),
            ('location_id', 'in', loc_ids),
        ])
        loc_map = {loc.id: loc for loc in all_locs}

        updated_count = 0
        for pos in positions:
            loc = loc_map.get(pos['id'])
            if not loc:
                continue
            loc.write({
                'layout_id': layout.id,
                'pos_x': pos.get('pos_x', 0),
                'pos_y': pos.get('pos_y', 0),
                'size_x': pos.get('size_x', 2),
                'size_y': pos.get('size_y', 1),
                'location_color': pos.get('location_color', '#4A90D9'),
                'location_shape': pos.get('location_shape', 'rack'),
                'location_rotation': pos.get('location_rotation', 0),
                'shelf_rows': pos.get('shelf_rows', 1),
            })
            updated_count += 1

            # Child positions
            for child_pos in pos.get('children', []):
                child = loc_map.get(child_pos['id'])
                if child:
                    child.write({
                        'pos_x': child_pos.get('pos_x', 0),
                        'pos_y': child_pos.get('pos_y', 0),
                        'size_x': child_pos.get('size_x', 1),
                        'size_y': child_pos.get('size_y', 1),
                        'location_rotation': child_pos.get(
                            'location_rotation', 0),
                    })

        # --- Batch remove, only from this layout ---
        to_remove = Location.search([
            ('id', 'in', removed_ids),
            ('id', 'not in', loc_ids),
            ('layout_id', '=', layout.id),
        ])
        to_remove.write({'layout_id': False, 'pos_x': 0, 'pos_y': 0})

        return {
            'success': True,
            'updated_count': updated_count,
            'removed_count': len(to_remove),
        }

    @http.route('/warehouse_3d/save_map_objects', type='jsonrpc',
                auth='user')
    def save_map_objects(self, layout_id, objects, removed_ids=None):
        """Batch save, create, or delete map objects from the canvas.

        ``created_ids`` maps the temporary (negative) ID of each new object
        to its record ID, so saving again updates it instead of creating it
        twice.
        """
        MapObject = request.env['warehouse.map.object']

        layout = self._get_writable_layout(layout_id)
        if not layout:
            return {
                'success': False,
                'error': request.env._('Layout not found'),
            }

        objects = objects or []
        removed_ids = removed_ids or []

        # --- Batch remove ---
        # Only delete objects of this layout, even if the ID list is
        # malformed
        to_remove = MapObject.search([
            ('id', 'in', removed_ids),
            ('layout_id', '=', layout.id),
        ])
        removed_count = len(to_remove)
        to_remove.unlink()

        # --- Batch update/create ---
        updated_count = 0
        created_ids = {}
        for obj_data in objects:
            obj_id = obj_data.get('id')
            vals = {
                'layout_id': layout.id,
                'name': obj_data.get('name', 'Object'),
                'object_type': obj_data.get('object_type', 'wall'),
                'pos_x': obj_data.get('pos_x', 0),
                'pos_y': obj_data.get('pos_y', 0),
                'size_x': obj_data.get('size_x', 1),
                'size_y': obj_data.get('size_y', 1),
                'is_flipped': obj_data.get('is_flipped', False),
                'icon': obj_data.get('icon', '📌'),
                'color': obj_data.get('color', '#95A5A6'),
            }
            # Only update an existing object that belongs to this layout
            obj_record = MapObject
            if isinstance(obj_id, int) and obj_id > 0:
                obj_record = MapObject.search([
                    ('id', '=', obj_id),
                    ('layout_id', '=', layout.id),
                ])
            if obj_record:
                obj_record.write(vals)
                updated_count += 1
            else:
                created_ids[str(obj_id)] = MapObject.create(vals).id

        return {
            'success': True,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'updated_count': updated_count,
            'removed_count': removed_count,
        }

    # =========================================================================
    # Export / Import layout
    # =========================================================================

    @http.route('/warehouse_3d/export_layout', type='http', auth='user')
    def export_layout(self, layout_id, **kwargs):
        """Export all the floors of a warehouse as a downloadable XML file."""
        layout = request.env['warehouse.layout'].browse(int(layout_id))
        if not layout.exists():
            return request.not_found()

        layouts = request.env['warehouse.layout'].search([
            ('warehouse_id', '=', layout.warehouse_id.id),
        ]).sorted('floor_level')
        layouts_data = [(lay, lay.get_layout_data()) for lay in layouts]

        return self._export_xml(layouts_data, layout.name)

    @http.route('/warehouse_3d/import_layout', type='http', auth='user',
                methods=['POST'])
    def import_layout(self, layout_id, file, **kwargs):
        """Import a warehouse layout from an uploaded XML file."""
        env = request.env
        try:
            layout = self._get_writable_layout(int(layout_id))
        except AccessError as exc:
            return self._import_error(str(exc), 403)
        if not layout:
            return self._import_error(env._('Layout not found'), 404)

        raw = file.read()
        filename = file.filename or ''
        if not (filename.lower().endswith('.xml') or b'<?xml' in raw[:10]):
            return self._import_error(env._('Only XML files are supported'))

        # Entities and network access stay disabled for uploaded files
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            root = etree.fromstring(raw, parser=parser)
        except etree.XMLSyntaxError as exc:
            return self._import_error(
                env._('Invalid XML file: %s', exc))

        # All or nothing: a wrong value leaves the layouts as they were
        try:
            with env.cr.savepoint():
                result = self._import_xml(layout, root)
        except (ValueError, UserError, IntegrityError) as exc:
            return self._import_error(
                env._('Invalid layout file: %s', exc))
        return request.make_json_response(result)

    def _import_error(self, message, status=400):
        """Return an import failure the designer can display."""
        return request.make_json_response(
            {'success': False, 'error': message}, status=status)

    def _export_xml(self, layouts_data, base_name):
        """Export warehouse layouts to XML."""
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<odoo>',
            '    <data noupdate="1">',
            '',
        ]

        for layout, data in layouts_data:
            loc_ids = [loc['id'] for loc in data.get('locations', [])]
            for loc in data.get('locations', []):
                loc_ids.extend([c['id'] for c in loc.get('children', [])])

            locations = request.env['stock.location'].browse(loc_ids)
            # {id: 'module.xml_id'}
            ext_ids = locations.get_external_id()

            field = _xml_field
            xml_lines.extend([
                (f'        <!-- Layout Settings: Floor '
                 f'{layout.floor_level} -->'),
                (f'        <record id="layout_{layout.id}"'
                 f' model="warehouse.layout">'),
                field('name', layout.name),
                field('canvas_width', layout.canvas_width),
                field('canvas_height', layout.canvas_height),
                field('grid_size', layout.grid_size),
                field('cell_size_cm', layout.cell_size_cm),
                field('floor_level', layout.floor_level),
                field('measurement_unit', layout.measurement_unit),
            ])
            if layout.notes:
                xml_lines.append(field('notes', layout.notes))
            xml_lines.append('        </record>')
            xml_lines.append('')

            layout_xml_id = f"layout_{layout.id}"

            xml_lines.append('        <!-- Placed Locations -->')
            for loc in data.get('locations', []):
                self._append_location_xml(
                    xml_lines, loc, ext_ids, layout_xml_id)
                for child in loc.get('children', []):
                    self._append_location_xml(
                        xml_lines, child, ext_ids, layout_xml_id)

            xml_lines.append('')
            xml_lines.append('        <!-- Map Objects (Decorations) -->')
            for i, obj in enumerate(data.get('map_objects', []), 1):
                xml_lines.extend([
                    (f'        <record id="map_object_{layout.id}_{i}"'
                     f' model="warehouse.map.object">'),
                    field('name', obj.get('name', 'Object')),
                    field('object_type', obj.get('object_type', 'wall')),
                    field('pos_x', obj.get('pos_x', 0)),
                    field('pos_y', obj.get('pos_y', 0)),
                    field('size_x', obj.get('size_x', 1)),
                    field('size_y', obj.get('size_y', 1)),
                ])
                if obj.get('is_flipped'):
                    xml_lines.append(field('is_flipped', 'True'))
                xml_lines.extend([
                    field('icon', obj.get('icon', '📌')),
                    field('color', obj.get('color', '#95A5A6')),
                    (f'            <field name="layout_id"'
                     f' ref="{layout_xml_id}"/>'),
                    '        </record>',
                ])
            xml_lines.append('')

        xml_lines.extend(['    </data>', '</odoo>', ''])
        return request.make_response(
            '\n'.join(xml_lines),
            headers=[
                ('Content-Type', 'application/xml; charset=utf-8'),
                ('Content-Disposition', content_disposition(
                    f"{base_name.replace(' ', '_')}_all_floors.xml")),
            ],
        )

    def _append_location_xml(self, xml_lines, loc, ext_ids, layout_xml_id):
        """Append location data to the XML export. The complete name finds
        the location again at import when it has no external ID."""
        raw_xml_id = ext_ids.get(loc['id']) or f"location_{loc['id']}"

        field = _xml_field
        xml_lines.extend([
            f'        <record id="{raw_xml_id}" model="stock.location">',
            field('complete_name', loc['complete_name']),
            field('pos_x', loc.get('pos_x', 0)),
            field('pos_y', loc.get('pos_y', 0)),
            field('size_x', loc.get('size_x', 1)),
            field('size_y', loc.get('size_y', 1)),
        ])
        for name in ('location_shape', 'location_color',
                     'location_rotation', 'shelf_rows'):
            if loc.get(name):
                xml_lines.append(field(name, loc[name]))
        xml_lines.extend([
            f'            <field name="layout_id" ref="{layout_xml_id}"/>',
            '        </record>',
        ])

    def _find_imported_location(self, node, company):
        """Return the location of a record of the file: by external ID, or
        by complete name in the company. Other records are ignored."""
        Location = request.env['stock.location']
        xml_id = node.get('id') or ''
        location = Location
        if '.' in xml_id:
            record = request.env.ref(xml_id, raise_if_not_found=False)
            if record and record._name == 'stock.location':
                location = record
        complete_name = _node_text(node, 'complete_name')
        if not location and complete_name:
            location = Location.search([
                ('complete_name', '=', complete_name),
                ('company_id', 'in', [company.id, False]),
            ], limit=1)
        if location.sudo().company_id - company:
            return Location
        return location

    def _import_layouts(self, layout, root):
        """Update or create the layouts of the file, matched by name, then
        by floor as a floor can hold several layouts.

        Return the mapping of file IDs to layouts.
        """
        Layout = request.env['warehouse.layout']
        warehouse = layout.warehouse_id
        existing = Layout.search([('warehouse_id', '=', warehouse.id)])
        name_to_layout = {lay.name: lay for lay in existing}
        floor_to_layout = {lay.floor_level: lay for lay in existing}
        mapping = {}
        for node in root.findall(".//record[@model='warehouse.layout']"):
            vals = {}
            for name in LAYOUT_INT_FIELDS:
                value = _node_text(node, name)
                if value:
                    vals[name] = int(value)
            for name in ('name', 'measurement_unit', 'notes'):
                value = _node_text(node, name)
                if value:
                    vals[name] = value

            floor_level = vals.get('floor_level', 0)
            target = (name_to_layout.get(vals.get('name'))
                      or floor_to_layout.get(floor_level))
            if target:
                target.write(vals)
            else:
                target = Layout.create({
                    **vals, 'warehouse_id': warehouse.id})
                floor_to_layout[floor_level] = target
            mapping[node.get('id')] = target
        return mapping

    def _import_xml(self, layout, root):
        """Import warehouse layout data from a parsed XML file. The map
        objects of the imported layouts are replaced by those of the file,
        so importing a file twice does not duplicate them."""
        layouts = self._import_layouts(layout, root)

        def target_layout(node):
            ref_node = node.find("field[@name='layout_id']")
            ref = ref_node.get('ref') if ref_node is not None else None
            return layouts.get(ref, layout)

        matched_count = 0
        skipped_names = []
        for node in root.findall(".//record[@model='stock.location']"):
            loc = self._find_imported_location(node, layout.company_id)
            if not loc:
                skipped_names.append(
                    _node_text(node, 'complete_name') or node.get('id'))
                continue

            vals = {'layout_id': target_layout(node).id}
            for name in ('pos_x', 'pos_y', 'size_x', 'size_y', 'shelf_rows',
                         'location_rotation'):
                value = _node_text(node, name)
                if value:
                    vals[name] = int(float(value))
            for name in ('location_shape', 'location_color'):
                value = _node_text(node, name)
                if value:
                    vals[name] = value
            loc.write(vals)
            matched_count += 1

        MapObject = request.env['warehouse.map.object']
        object_nodes = root.findall(
            ".//record[@model='warehouse.map.object']")
        MapObject.search([
            ('layout_id', 'in', [lay.id for lay in layouts.values()]),
        ]).unlink()
        for node in object_nodes:
            vals = {
                'layout_id': target_layout(node).id,
                'name': _node_text(node, 'name') or 'Object',
                'is_flipped': _node_text(node, 'is_flipped') == 'True',
            }
            for name in ('object_type', 'icon', 'color'):
                value = _node_text(node, name)
                if value:
                    vals[name] = value
            for name in ('pos_x', 'pos_y', 'size_x', 'size_y'):
                value = _node_text(node, name)
                if value:
                    vals[name] = int(value)
            MapObject.create(vals)

        if skipped_names:
            _logger.warning('XML Import: skipped locations not found: %s',
                            ', '.join(skipped_names))

        return {
            'success': True,
            'matched_locations': matched_count,
            'skipped_locations': len(skipped_names),
            'skipped_names': skipped_names,
            'created_map_objects': len(object_nodes),
        }
