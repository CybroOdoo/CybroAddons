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

# Default colors per shape type
SHAPE_DEFAULTS = {
    'rack': {'size_x': 2, 'size_y': 1, 'color': '#4A90D9'},
    'shelf': {'size_x': 3, 'size_y': 1, 'color': '#50C878'},
    'bin': {'size_x': 1, 'size_y': 1, 'color': '#FFB347'},
    'zone': {'size_x': 6, 'size_y': 4, 'color': '#DDA0DD'},
    'dock': {'size_x': 2, 'size_y': 2, 'color': '#808080'},
    'floor': {'size_x': 4, 'size_y': 4, 'color': '#C8B560'},
    'packing': {'size_x': 3, 'size_y': 2, 'color': '#E67E22'},
    'refrigerator': {'size_x': 3, 'size_y': 2, 'color': '#2980B9'},
    'qc_area': {'size_x': 4, 'size_y': 3, 'color': '#8E44AD'},
}


class StockLocation(models.Model):
    """Extends stock.location with visual designer placement fields."""

    _inherit = 'stock.location'

    layout_id = fields.Many2one(
        'warehouse.layout',
        string='Layout',
        ondelete='set null',
        help='The warehouse layout this location is placed on.',
    )
    pos_x = fields.Integer(
        string='Grid X',
        default=0,
        help='Horizontal grid position on the layout canvas.',
    )
    pos_y = fields.Integer(
        string='Grid Y',
        default=0,
        help='Vertical grid position on the layout canvas.',
    )
    size_x = fields.Integer(
        string='Width (grid cells)',
        default=2,
        help='Width of the location block in grid cells.',
    )
    size_y = fields.Integer(
        string='Height (grid cells)',
        default=1,
        help='Height of the location block in grid cells.',
    )
    location_color = fields.Char(
        string='Color',
        default='#4A90D9',
        help='Hex color code for the location block on the canvas.',
    )
    location_rotation = fields.Integer(
        string='Rotation (degrees)',
        default=0,
        help='Rotation of the location block (e.g. 0, 90, 180, 270) '
             'mostly used for 3D elements like docks.',
    )
    location_shape = fields.Selection(
        selection=[
            ('rack', 'Rack'),
            ('shelf', 'Shelf'),
            ('bin', 'Bin'),
            ('zone', 'Zone'),
            ('dock', 'Dock'),
            ('floor', 'Floor Area'),
            ('packing', 'Packing Area'),
            ('refrigerator', 'Refrigerator/Cold Room'),
            ('qc_area', 'Quality Control Area'),
        ],
        string='Shape',
        default='rack',
        help='Visual shape type that determines the default size and icon.',
    )
    shelf_rows = fields.Integer(
        string='Number of Rows',
        default=1,
        help='Number of rows/layers for a shelf.',
    )
    is_on_layout = fields.Boolean(
        string='Placed on Layout',
        compute='_compute_is_on_layout',
        store=True,
        help='Whether this location has been placed on a layout.',
    )

    @api.depends('layout_id')
    def _compute_is_on_layout(self):
        """Compute whether the location is placed on a layout."""
        for loc in self:
            loc.is_on_layout = bool(loc.layout_id)

    @api.onchange('location_shape')
    def _onchange_location_shape(self):
        """Set default size and color when shape changes."""
        if self.location_shape and self.location_shape in SHAPE_DEFAULTS:
            defaults = SHAPE_DEFAULTS[self.location_shape]
            self.size_x = defaults['size_x']
            self.size_y = defaults['size_y']
            self.location_color = defaults['color']
