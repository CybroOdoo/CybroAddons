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
from odoo import api, fields, models
from odoo.tools import _


class WarehouseLayout(models.Model):
    """Warehouse floor layout for the visual designer."""

    _name = 'warehouse.layout'
    _description = 'Warehouse Layout'
    _order = 'name'

    name = fields.Char(
        string='Layout Name',
        required=True,
        help='Name of the layout, e.g. Main Warehouse Floor 1.',
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        ondelete='cascade',
        help='The warehouse this layout belongs to.',
    )
    canvas_width = fields.Integer(
        string='Canvas Width (grid cells)',
        default=40,
        required=True,
        help='Number of horizontal grid cells on the canvas.',
    )
    canvas_height = fields.Integer(
        string='Canvas Height (grid cells)',
        default=30,
        required=True,
        help='Number of vertical grid cells on the canvas.',
    )
    grid_size = fields.Integer(
        string='Grid Size (pixels)',
        default=30,
        required=True,
        help='Pixel size of each grid cell. Controls the zoom level.',
    )
    background_image = fields.Binary(
        string='Floor Plan Image',
        help='Optional: upload a floor plan image to display behind the grid.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, the layout will be hidden from the list.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help='Company this layout belongs to.',
    )
    floor_level = fields.Integer(
        string='Floor Level',
        default=0,
        help='Floor number for multi-story warehouses. '
             '0 = Ground Floor, positive = upper floors, negative = basement.',
    )
    notes = fields.Text(
        string='Notes',
        help='Optional notes about this layout.',
    )
    cell_size_cm = fields.Integer(
        string='Cell Size (cm)',
        default=100,
        required=True,
        help='Physical size of one grid cell in centimeters. Default 100 cm = 1 meter.',
    )
    measurement_unit = fields.Selection(
        selection=[
            ('m', 'Meters'),
            ('cm', 'Centimeters'),
            ('inch', 'Inches'),
        ],
        string='Measurement Unit',
        default='m',
        required=True,
        help='Unit for displaying measurements in the designer.',
    )
    location_ids = fields.One2many(
        'stock.location',
        'layout_id',
        string='Placed Locations',
        help='Stock locations placed on this layout canvas.',
    )
    map_object_ids = fields.One2many(
        'warehouse.map.object',
        'layout_id',
        string='Map Objects',
        help='Decoration objects placed on this layout canvas.',
    )
    location_count = fields.Integer(
        string='# Locations',
        compute='_compute_location_count',
        help='Number of locations placed on this layout.',
    )

    _sql_constraints = [
        ('canvas_width_positive', 'CHECK(canvas_width > 0)', 'Canvas width must be positive.'),
        ('canvas_height_positive', 'CHECK(canvas_height > 0)', 'Canvas height must be positive.'),
        ('grid_size_range', 'CHECK(grid_size >= 10 AND grid_size <= 100)', 'Grid size must be between 10 and 100 pixels.'),
    ]

    @api.depends('location_ids')
    def _compute_location_count(self):
        """Compute the number of locations placed on this layout."""
        for layout in self:
            layout.location_count = len(layout.location_ids)

    def action_open_designer(self):
        """Open the warehouse designer client action for this layout."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'warehouse_designer',
            'name': _('Warehouse Designer — %s', self.name),
            'context': {
                'default_layout_id': self.id,
            },
        }

    # =========================================================================
    # Heatmap — single aggregated SQL via read_group (no N+1)
    # =========================================================================

    def get_heatmap_data(self):
        """Return stock fill percentage for placed locations and their children."""
        self.ensure_one()
        placed = self.env['stock.location'].search([
            ('layout_id', '=', self.id),
            ('usage', '=', 'internal'),
        ])
        if not placed:
            return {}

        # Collect parent IDs + all child IDs for per-location heatmap
        child_locs = placed.mapped('child_ids').filtered(
            lambda c: c.usage == 'internal'
        )
        all_locs = placed | child_locs
        loc_ids = all_locs.ids

        # Single aggregated query for ALL locations (parents + children)
        quant_data = self.env['stock.quant'].read_group(
            domain=[('location_id', 'in', loc_ids), ('quantity', '>', 0)],
            fields=['quantity:sum', 'product_id:count_distinct'],
            groupby=['location_id'],
        )

        # Build lookup: {location_id: {qty, product_count}}
        quant_map = {}
        for group in quant_data:
            lid = group['location_id'][0]
            quant_map[lid] = {
                'qty': group['quantity'],
                'product_count': group['product_id'],
            }

        result = {}
        for loc in all_locs:
            qdata = quant_map.get(loc.id, {'qty': 0, 'product_count': 0})
            total_qty = qdata['qty']
            product_count = qdata['product_count']

            capacity = 0
            if loc.storage_category_id:
                product_caps = loc.storage_category_id.product_capacity_ids
                if product_caps:
                    capacity = sum(product_caps.mapped('quantity'))
            if capacity <= 0:
                capacity = 100

            fill_pct = min((total_qty / capacity * 100) if capacity else 0, 100)
            result[loc.id] = {
                'qty': total_qty,
                'weight': loc.net_weight,
                'product_count': product_count,
                'fill_pct': round(fill_pct, 1),
            }
        return result

    # =========================================================================
    # Product search
    # =========================================================================

    def search_product_locations(self, query, cross_floor=False):
        """Search products across placed locations on this layout.

        If cross_floor is True, searches across all layouts that belong
        to the same warehouse.
        """
        self.ensure_one()
        if not query:
            return []

        if cross_floor:
            sibling_layouts = self.search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('active', '=', True),
            ])
            layout_ids = sibling_layouts.ids
        else:
            layout_ids = [self.id]

        placed_locs = self.env['stock.location'].search([
            ('layout_id', 'in', layout_ids),
        ])
        if not placed_locs:
            return []

        # Build layout lookup for floor labels
        layout_map = {}
        if cross_floor:
            for sl in sibling_layouts:
                layout_map[sl.id] = {
                    'name': sl.name,
                    'floor_level': sl.floor_level,
                }

        # Map location → layout
        loc_layout = {loc.id: loc.layout_id.id for loc in placed_locs}

        products = self.env['product.product'].search([
            '|',
            ('name', 'ilike', query),
            ('default_code', 'ilike', query),
        ], limit=50)
        if not products:
            return []

        quants = self.env['stock.quant'].search([
            ('product_id', 'in', products.ids),
            ('location_id', 'in', placed_locs.ids),
            ('quantity', '>', 0),
        ])

        results = []
        for q in quants:
            entry = {
                'product_id': q.product_id.id,
                'product_name': q.product_id.display_name,
                'location_id': q.location_id.id,
                'location_name': q.location_id.complete_name,
                'quantity': q.quantity,
            }
            if cross_floor:
                lid = loc_layout.get(q.location_id.id)
                linfo = layout_map.get(lid, {})
                entry['layout_id'] = lid
                entry['floor_level'] = linfo.get('floor_level', 0)
                entry['layout_name'] = linfo.get('name', '')
            results.append(entry)
        return results

    # =========================================================================
    # Layout data — pre-fetches children to avoid N+1 on child_ids
    # =========================================================================

    def get_layout_data(self):
        """Return full layout data for the designer client action."""
        self.ensure_one()
        warehouse = self.warehouse_id

        # Placed locations (pre-fetch child_ids to avoid lazy N+1)
        placed = self.env['stock.location'].search([
            ('layout_id', '=', self.id),
        ])
        # Pre-fetch relational fields in batch
        placed.mapped('child_ids')

        # Unplaced internal locations — exclude children whose parent
        # is already on the layout to prevent duplicate placement
        placed_ids = placed.ids
        unplaced = self.env['stock.location'].search([
            ('warehouse_id', '=', warehouse.id),
            ('usage', '=', 'internal'),
            ('layout_id', '=', False),
            ('location_id', 'not in', placed_ids),
        ])

        # Map objects
        map_objects = self.env['warehouse.map.object'].search([
            ('layout_id', '=', self.id),
        ])

        # Pre-calculate product summaries for all locations on this layout
        placed_ids_set = set(placed.ids)
        unplaced_ids_set = set(unplaced.ids)
        all_tracked_ids_set = placed_ids_set | unplaced_ids_set
        all_descendants = self.env['stock.location'].search(
            [('id', 'child_of', list(all_tracked_ids_set))]
        )

        quants = self.env['stock.quant'].search([
            ('location_id', 'in', all_descendants.ids),
            ('quantity', '>', 0),
        ])

        loc_products = {}
        # Create a mapping from descendant to its top-level placed/unplaced
        # ancestor
        descendant_to_placed = {}
        for desc in all_descendants:
            curr = desc
            while curr and curr.id not in all_tracked_ids_set:
                curr = curr.location_id
            if curr:
                descendant_to_placed[desc.id] = curr.id

        for q in quants:
            loc_id = q.location_id.id

            # Find the top-level placed location ID this quant belongs to
            tracked_id = descendant_to_placed.get(loc_id)
            if tracked_id not in all_tracked_ids_set:
                continue

            if tracked_id not in loc_products:
                loc_products[tracked_id] = []

            # Check if product is already in list (multiple quants for same
            # product)
            existing = next(
                (p for p in loc_products[tracked_id]
                 if p['product_id'] == q.product_id.id), None
            )
            if existing:
                existing['qty'] += q.quantity
            else:
                loc_products[tracked_id].append({
                    'product_id': q.product_id.id,
                    'product_name': q.product_id.display_name,
                    'qty': q.quantity,
                    'uom': q.product_uom_id.name
                    if q.product_uom_id else '',
                })

        # Sibling floors for the same warehouse
        sibling_layouts = self.search([
            ('warehouse_id', '=', warehouse.id),
            ('active', '=', True),
        ], order='floor_level asc')
        sibling_floors = [{
            'id': sl.id,
            'name': sl.name,
            'floor_level': sl.floor_level,
        } for sl in sibling_layouts]

        return {
            'layout': {
                'id': self.id,
                'name': self.name,
                'canvas_width': self.canvas_width,
                'canvas_height': self.canvas_height,
                'grid_size': self.grid_size,
                'background_image': self.background_image,
                'cell_size_cm': self.cell_size_cm,
                'measurement_unit': self.measurement_unit,
                'floor_level': self.floor_level,
            },
            'sibling_floors': sibling_floors,
            'locations': [{
                'id': loc.id,
                'name': loc.name,
                'complete_name': loc.complete_name,
                'pos_x': loc.pos_x,
                'pos_y': loc.pos_y,
                'size_x': loc.size_x,
                'size_y': loc.size_y,
                'location_color': loc.location_color,
                'location_shape': loc.location_shape,
                'location_rotation': loc.location_rotation,
                'shelf_rows': loc.shelf_rows,
                'usage': loc.usage,
                'is_empty': loc.is_empty,
                'net_weight': loc.net_weight,
                'product_summary': loc_products.get(loc.id, []),
                'children': [{
                    'id': child.id,
                    'name': child.name,
                    'complete_name': child.complete_name,
                    'location_shape': child.location_shape,
                    'pos_x': child.pos_x,
                    'pos_y': child.pos_y,
                    'size_x': child.size_x,
                    'size_y': child.size_y,
                    'location_rotation': child.location_rotation,
                    'location_color': child.location_color,
                    'usage': child.usage,
                    'product_summary': loc_products.get(child.id, []),
                } for child in loc.child_ids],
            } for loc in placed],
            'unplaced_locations': [{
                'id': loc.id,
                'name': loc.name,
                'complete_name': loc.complete_name,
                'usage': loc.usage,
                'product_summary': loc_products.get(loc.id, []),
            } for loc in unplaced],
            'map_objects': [{
                'id': obj.id,
                'name': obj.name,
                'object_type': obj.object_type,
                'pos_x': obj.pos_x,
                'pos_y': obj.pos_y,
                'size_x': obj.size_x,
                'size_y': obj.size_y,
                'is_flipped': obj.is_flipped,
                'icon': obj.icon,
                'color': obj.color,
                'connected_layout_id':
                    obj.connected_layout_id.id
                    if obj.connected_layout_id else False,
            } for obj in map_objects],
        }
