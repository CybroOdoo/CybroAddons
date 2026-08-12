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


# Default icons and colors for map object types
OBJECT_DEFAULTS = {
    'wall': {'icon': '🧱', 'color': '#555555', 'size_x': 1, 'size_y': 1},
    'room': {'icon': '🚪', 'color': '#7F8C8D', 'size_x': 4, 'size_y': 3},
}


class WarehouseMapObject(models.Model):
    """Non-location decoration object for the warehouse layout."""

    _name = 'warehouse.map.object'
    _description = 'Warehouse Map Object'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help='Label for this map object, e.g. "Fire Ext. #3".',
    )
    layout_id = fields.Many2one(
        'warehouse.layout',
        string='Layout',
        required=True,
        ondelete='cascade',
        help='The warehouse layout this object belongs to.',
    )
    object_type = fields.Selection(
        selection=[
            ('wall', 'Wall'),
            ('room', 'Room/Office'),
        ],
        string='Object Type',
        required=True,
        default='wall',
        help='Type of map decoration object.',
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
        string='Width (cells)',
        default=1,
        help='Width of the object in grid cells.',
    )
    size_y = fields.Integer(
        string='Height (cells)',
        default=1,
        help='Height of the object in grid cells.',
    )
    is_flipped = fields.Boolean(
        string='Is Flipped Edge',
        default=False,
        help='For walls: flip the wall to the opposite edge of its cell.',
    )
    icon = fields.Char(
        string='Icon',
        default='🏷️',
        help='Emoji or character icon displayed on the map.',
    )
    color = fields.Char(
        string='Color',
        default='#95A5A6',
        help='Hex color code for the object on the canvas.',
    )
    connected_layout_id = fields.Many2one(
        'warehouse.layout',
        string='Connected Floor',
        ondelete='set null',
        help='For stairs/elevators: the layout (floor) this object '
             'connects to.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help='Company this map object belongs to.',
    )

    @api.onchange('object_type')
    def _onchange_object_type(self):
        """Set defaults when object type changes."""
        if self.object_type and self.object_type in OBJECT_DEFAULTS:
            defaults = OBJECT_DEFAULTS[self.object_type]
            self.icon = defaults['icon']
            self.color = defaults['color']
            self.size_x = defaults['size_x']
            self.size_y = defaults['size_y']
