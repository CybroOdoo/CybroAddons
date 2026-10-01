
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models

DEFAULT_COLORS = [
    '#AEC6CF',
    '#FFB7B2',
    '#77DD77',
    '#FDFD96',
    '#C3B1E1',
    '#FFDAC1',
    '#CFCFC4',
    '#B0E0E6'
]


class DashboardColorGroup(models.Model):
    """Model representing a group/palette of colors."""
    _name = 'dashboard.color.group'
    _description = 'Dashboard Color Group'
    _order = 'sequence, name'

    name = fields.Char(string='Group Name', required=True, help='Name of the color group.')
    sequence = fields.Integer(string='Sequence', default=10, help='Sequence order of the group.')
    color_ids = fields.One2many('dashboard.color', 'group_id', string='Colors', help='Colors in this group.')

    def get_colors(self):
        """
        Get the list of hex color codes for this group.
        Fallback to default colors if none exist.
        """
        return self.color_ids.mapped('hex_code') if self.color_ids else DEFAULT_COLORS


class DashboardColor(models.Model):
    """Model representing an individual hex color in a color group."""
    _name = 'dashboard.color'
    _description = 'Dashboard Color'
    _order = 'sequence, name'

    name = fields.Char(string='Color Name', required=True, help='Name of the color.')
    hex_code = fields.Char(
        string='Hex Code',
        required=True,
        help='Color in hex format (e.g., #FF5733).'
    )
    group_id = fields.Many2one(
        'dashboard.color.group',
        string='Color Group',
        required=True,
        ondelete='cascade',
        help='Group to which this color belongs.'
    )
    sequence = fields.Integer(string='Sequence', default=10, help='Sequence order of the color.')
