"""This module inherits stock.location model."""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class StockLocation(models.Model):
    """Class for adding fields to stock.location"""
    _inherit = 'stock.location'

    length = fields.Float(string="Length (M)",
                          help="Length of the location in meters")
    width = fields.Float(string="Width (M)",
                         help="Width of the location in meters")
    height = fields.Float(string="Height (M)",
                          help="Height of the location in meters")
    pos_x = fields.Float(string="X (in px)",
                         help="Position of the location along X-axis")
    pos_y = fields.Float(string="Y (in px)",
                         help="Position of the location along Y-axis")
    pos_z = fields.Float(string="Z (in px)",
                         help="Position of the location along Z-axis")
    unique_code = fields.Char(string="Location Code",
                              help="Unique code of the location")
    max_capacity = fields.Integer(string="Capacity (Units)",
                                  help="Maximum capacity of the location in "
                                       "terms of Units")

    _sql_constraints = [
        ('unique_code', 'UNIQUE(unique_code)',
         "The location code must be unique per company !"),
    ]

    def action_view_location_3d_button(self):
        """
        This method is used to handle the view_location_3d_button button action.
        ------------------------------------------------
        @param self: object pointer.
        @return: client action with location id and company id to display.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'open_form_3d_view',
            'context': {
                'loc_id': self.id,
                'company_id': self.company_id.id,
            }
        }
