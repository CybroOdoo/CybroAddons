# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
import logging
import xml.etree.ElementTree as ET

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WarehouseDesignerController(http.Controller):
    """Controller for the Warehouse 3D Designer client actions."""

    @http.route('/warehouse_3d/save_positions', type='json', auth='user')
    def save_positions(self, layout_id, positions, removed_ids=None):
        """Batch save location positions from the designer canvas."""
        Layout = request.env['warehouse.layout']
        Location = request.env['stock.location']

        layout = Layout.browse(layout_id)
        if not layout.exists():
            return {'success': False, 'error': 'Layout not found'}

        positions = positions or []
        removed_ids = removed_ids or []

        # --- Batch update placed locations ---
        loc_ids = [p['id'] for p in positions]
        child_ids_all = []
        for p in positions:
            child_ids_all.extend(c['id'] for c in p.get('children', []))

        # Pre-fetch all records in one query
        all_ids = list(set(loc_ids + child_ids_all + removed_ids))
        all_locs = Location.browse(all_ids).exists()
        loc_map = {loc.id: loc for loc in all_locs}

        updated_count = 0
        for pos in positions:
            loc = loc_map.get(pos['id'])
            if not loc:
                continue
            loc.write({
                'layout_id': layout_id,
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
                        'location_rotation': child_pos.get('location_rotation', 0),
                    })

        # --- Batch remove ---
        removed_count = 0
        if removed_ids:
            to_remove = Location.browse(removed_ids).exists()
            if to_remove:
                to_remove.write({'layout_id': False, 'pos_x': 0, 'pos_y': 0})
                removed_count = len(to_remove)

        return {
            'success': True,
            'updated_count': updated_count,
            'removed_count': removed_count,
        }

    @http.route('/warehouse_3d/save_map_objects', type='json', auth='user')
    def save_map_objects(self, layout_id, objects, removed_ids=None):
        """Batch save, create, or delete map objects from the designer canvas."""
        Layout = request.env['warehouse.layout']
        MapObject = request.env['warehouse.map.object']

        layout = Layout.browse(layout_id)
        if not layout.exists():
            return {'success': False, 'error': 'Layout not found'}

        objects = objects or []
        removed_ids = removed_ids or []

        # --- Batch remove ---
        removed_count = 0
        if removed_ids:
            # We don't want to accidentally delete objects from other layouts if there's a malformed ID list
            to_remove = MapObject.search([('id', 'in', removed_ids), ('layout_id', '=', layout_id)])
            if to_remove:
                removed_count = len(to_remove)
                to_remove.unlink()

        # --- Batch update/create ---
        updated_count = 0
        created_count = 0
        for obj_data in objects:
            obj_id = obj_data.get('id')
            vals = {
                'layout_id': layout_id,
                'name': obj_data.get('name', 'Object'),
                'object_type': obj_data.get('object_type', 'wall'),
                'pos_x': obj_data.get('pos_x', 0),
                'pos_y': obj_data.get('pos_y', 0),
                'size_x': obj_data.get('size_x', 1),
                'size_y': obj_data.get('size_y', 1),
                'is_flipped': obj_data.get('is_flipped', False),
                'icon': obj_data.get('icon', '📌'),
                'color': obj_data.get('color', '#95A5A6'),
                'connected_layout_id': obj_data.get('connected_layout_id') or False,
            }
            # Only update existing if it exists and actually belongs to this layout
            if obj_id and isinstance(obj_id, int):
                obj_record = MapObject.search([('id', '=', obj_id), ('layout_id', '=', layout_id)])
                if obj_record:
                    obj_record.write(vals)
                    updated_count += 1
                else:
                    MapObject.create(vals)
                    created_count += 1
            else:
                MapObject.create(vals)
                created_count += 1

        return {
            'success': True,
            'created_count': created_count,
            'updated_count': updated_count,
            'removed_count': removed_count,
        }

    # =========================================================================
    # Export / Import layout
    # =========================================================================

    @http.route('/warehouse_3d/export_layout', type='http', auth='user')
    def export_layout(self, layout_id, format='xml', **kwargs):
        """Export a warehouse layout as a downloadable XML file."""
        layout_id = int(layout_id)
        layout = request.env['warehouse.layout'].browse(layout_id)
        if not layout.exists():
            return request.not_found()

        if layout.warehouse_id:
            layouts = request.env['warehouse.layout'].search([('warehouse_id', '=', layout.warehouse_id.id)])
            layouts = layouts.sorted('floor_level')
        else:
            layouts = layout

        layouts_data = [(l, l.get_layout_data()) for l in layouts]
        
        return self._export_xml(layouts_data, layout.name)

    @http.route('/warehouse_3d/import_layout', type='http', auth='user',
                methods=['POST'], csrf=False)
    def import_layout(self, layout_id, file, **kwargs):
        """Import a warehouse layout from an uploaded XML file."""
        layout_id = int(layout_id)
        Layout = request.env['warehouse.layout']
        Location = request.env['stock.location']
        MapObject = request.env['warehouse.map.object']

        layout = Layout.browse(layout_id)
        if not layout.exists():
            return request.make_json_response(
                {'success': False, 'error': 'Layout not found'}, status=404,
            )

        raw = file.read()
        filename = file.filename or ''
        
        is_xml = filename.lower().endswith('.xml') or b'<?xml' in raw[:10]
        
        if not is_xml:
            return request.make_json_response(
                {'success': False, 'error': 'Only XML files are supported'},
                status=400,
            )

        return self._import_xml(layout, raw, Location, MapObject)

    def _export_xml(self, layouts_data, base_name):
        """Export warehouse layouts to XML."""
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<odoo>',
            '    <data noupdate="1">',
            ''
        ]
        
        for layout, data in layouts_data:
            loc_ids = [loc['id'] for loc in data.get('locations', [])]
            for loc in data.get('locations', []):
                loc_ids.extend([c['id'] for c in loc.get('children', [])])
                
            locations = request.env['stock.location'].browse(loc_ids)
            ext_ids = locations.get_external_id() # returns {id: 'module.xml_id'}
            
            xml_lines.extend([
                f'        <!-- Layout Settings: Floor {layout.floor_level} -->',
                f'        <record id="demo_layout_{layout.id}" model="warehouse.layout">',
                f'            <field name="name">{layout.name}</field>',
                f'            <field name="canvas_width">{layout.canvas_width}</field>',
                f'            <field name="canvas_height">{layout.canvas_height}</field>',
                f'            <field name="grid_size">{layout.grid_size}</field>',
            ])
            if layout.cell_size_cm:
                xml_lines.append(f'            <field name="cell_size_cm">{layout.cell_size_cm}</field>')
            if layout.floor_level:
                xml_lines.append(f'            <field name="floor_level">{layout.floor_level}</field>')
            if layout.measurement_unit:
                xml_lines.append(f'            <field name="measurement_unit">{layout.measurement_unit}</field>')
            if layout.notes:
                xml_lines.append(f'            <field name="notes">{layout.notes}</field>')
            xml_lines.append('        </record>')
            xml_lines.append('')
            
            layout_xml_id = f"demo_layout_{layout.id}"
            
            xml_lines.append('        <!-- Placed Locations -->')
            for loc in data.get('locations', []):
                self._append_location_xml(xml_lines, loc, ext_ids, layout_xml_id)
                for child in loc.get('children', []):
                    self._append_location_xml(xml_lines, child, ext_ids, layout_xml_id)
                    
            xml_lines.append('')
            xml_lines.append('        <!-- Map Objects (Decorations) -->')
            for i, obj in enumerate(data.get('map_objects', []), 1):
                xml_lines.extend([
                    f'        <record id="demo_map_obj_{layout.id}_{i}" model="warehouse.map.object">',
                    f'            <field name="name">{obj.get("name", "Object")}</field>',
                    f'            <field name="object_type">{obj.get("object_type", "wall")}</field>',
                    f'            <field name="pos_x">{obj.get("pos_x", 0)}</field>',
                    f'            <field name="pos_y">{obj.get("pos_y", 0)}</field>',
                    f'            <field name="size_x">{obj.get("size_x", 1)}</field>',
                    f'            <field name="size_y">{obj.get("size_y", 1)}</field>',
                ])
                if obj.get('is_flipped'):
                    xml_lines.append('            <field name="is_flipped">True</field>')
                xml_lines.extend([
                    f'            <field name="icon">{obj.get("icon", "📌")}</field>',
                    f'            <field name="color">{obj.get("color", "#95A5A6")}</field>',
                    f'            <field name="layout_id" ref="{layout_xml_id}"/>',
                    '        </record>'
                ])
            xml_lines.append('')
            
        xml_lines.extend(['    </data>', '</odoo>', ''])
        payload = '\n'.join(xml_lines)
        
        safe_name = base_name.replace(' ', '_').encode('ascii', 'ignore').decode('ascii')
        if not safe_name:
            safe_name = 'layout'
            
        return request.make_response(
            payload,
            headers=[
                ('Content-Type', 'application/xml; charset=utf-8'),
                ('Content-Disposition', f'attachment; filename="{safe_name}_all_floors.xml"'),
            ],
        )

    def _append_location_xml(self, xml_lines, loc, ext_ids, layout_xml_id):
        """Append location data to the XML export."""
        raw_xml_id = ext_ids.get(loc['id'])
        if not raw_xml_id:
            raw_xml_id = f"stock_location_demo_{loc['id']}"
        
        xml_lines.extend([
            f'        <record id="{raw_xml_id}" model="stock.location">',
            f'            <field name="pos_x">{loc.get("pos_x", 0)}</field>',
            f'            <field name="pos_y">{loc.get("pos_y", 0)}</field>',
            f'            <field name="size_x">{loc.get("size_x", 1)}</field>',
            f'            <field name="size_y">{loc.get("size_y", 1)}</field>',
        ])
        if loc.get('location_shape'):
            xml_lines.append(f'            <field name="location_shape">{loc["location_shape"]}</field>')
        if loc.get('location_color'):
            xml_lines.append(f'            <field name="location_color">{loc["location_color"]}</field>')
        if loc.get('location_rotation'):
            xml_lines.append(f'            <field name="location_rotation">{loc["location_rotation"]}</field>')
        if loc.get('shelf_rows'):
            xml_lines.append(f'            <field name="shelf_rows">{loc["shelf_rows"]}</field>')
        xml_lines.extend([
            f'            <field name="layout_id" ref="{layout_xml_id}"/>',
            '        </record>'
        ])
        
    def _import_xml(self, layout, raw, Location, MapObject):
        """Import warehouse layout data from XML."""
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            return request.make_json_response(
                {'success': False, 'error': 'Invalid XML file: %s' % str(exc)},
                status=400,
            )
            
        warehouse = layout.warehouse_id
        Layout = request.env['warehouse.layout']
        existing_layouts = Layout.search([('warehouse_id', '=', warehouse.id)]) if warehouse else layout
        floor_to_layout = {l.floor_level: l for l in existing_layouts}
        
        layout_mapping = {}  # xml_id -> real_layout.id
        
        for layout_record in root.findall(".//record[@model='warehouse.layout']"):
            xml_id = layout_record.get('id')
            if not xml_id:
                continue
                
            l_vals = {}
            for field in ('name', 'canvas_width', 'canvas_height', 'grid_size', 'cell_size_cm', 'measurement_unit', 'floor_level'):
                field_node = layout_record.find(f"field[@name='{field}']")
                if field_node is not None and field_node.text:
                    if field in ('canvas_width', 'canvas_height', 'grid_size', 'cell_size_cm', 'floor_level'):
                        l_vals[field] = int(field_node.text or 0)
                    else:
                        l_vals[field] = field_node.text
                        
            notes_node = layout_record.find("field[@name='notes']")
            if notes_node is not None and notes_node.text:
                l_vals['notes'] = notes_node.text
                
            floor_level = l_vals.get('floor_level', 0)
            target_layout = floor_to_layout.get(floor_level)
            
            if target_layout:
                target_layout.write(l_vals)
                layout_mapping[xml_id] = target_layout.id
            else:
                l_vals['warehouse_id'] = warehouse.id if warehouse else False
                new_layout = Layout.create(l_vals)
                floor_to_layout[floor_level] = new_layout
                layout_mapping[xml_id] = new_layout.id

        matched_count = 0
        skipped_names = []
        
        for loc_node in root.findall(".//record[@model='stock.location']"):
            xml_id = loc_node.get('id')
            if not xml_id:
                continue
                
            loc = request.env.ref(xml_id, raise_if_not_found=False)
            if not loc and '.' not in xml_id:
                loc = request.env.ref(f"warehouse_3d_designer.{xml_id}", raise_if_not_found=False)
            
            if not loc:
                skipped_names.append(xml_id)
                continue
                
            layout_ref = loc_node.find("field[@name='layout_id']")
            target_layout_id = layout.id
            if layout_ref is not None and layout_ref.get('ref'):
                target_layout_id = layout_mapping.get(layout_ref.get('ref'), layout.id)
                
            vals = {'layout_id': target_layout_id}
            
            for field in ('pos_x', 'pos_y', 'size_x', 'size_y', 'shelf_rows'):
                node = loc_node.find(f"field[@name='{field}']")
                if node is not None and node.text:
                    vals[field] = int(node.text or 0)
            
            for field in ('location_shape', 'location_color'):
                node = loc_node.find(f"field[@name='{field}']")
                if node is not None and node.text:
                    vals[field] = node.text
                    
            rot_node = loc_node.find("field[@name='location_rotation']")
            if rot_node is not None and rot_node.text:
                vals['location_rotation'] = float(rot_node.text or 0.0)
                
            loc.write(vals)
            matched_count += 1

        obj_count = 0
        for obj_node in root.findall(".//record[@model='warehouse.map.object']"):
            layout_ref = obj_node.find("field[@name='layout_id']")
            target_layout_id = layout.id
            if layout_ref is not None and layout_ref.get('ref'):
                target_layout_id = layout_mapping.get(layout_ref.get('ref'), layout.id)
                
            vals = {'layout_id': target_layout_id}
            
            for field in ('name', 'object_type', 'icon', 'color'):
                node = obj_node.find(f"field[@name='{field}']")
                if node is not None and node.text:
                    vals[field] = node.text
                    
            for field in ('pos_x', 'pos_y', 'size_x', 'size_y'):
                node = obj_node.find(f"field[@name='{field}']")
                if node is not None and node.text:
                    vals[field] = int(node.text or 0)
                    
            flip_node = obj_node.find("field[@name='is_flipped']")
            if flip_node is not None and flip_node.text == 'True':
                vals['is_flipped'] = True
            else:
                vals['is_flipped'] = False
                
            MapObject.create(vals)
            obj_count += 1

        if skipped_names:
            _logger.warning('XML Import: skipped locations not found: %s', ', '.join(skipped_names))

        return request.make_json_response({
            'success': True,
            'matched_locations': matched_count,
            'skipped_locations': len(skipped_names),
            'skipped_names': skipped_names,
            'created_map_objects': obj_count,
        })
