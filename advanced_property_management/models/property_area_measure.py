# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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
from odoo import api, fields, models


class PropertyAreaMeasure(models.Model):
    """A class for the model property.area.measure to represent
    the area of each sections"""
    _name = 'property.area.measure'
    _description = 'Property Area Measurement'

    name = fields.Char(string='Section', required=True,
                       help='Name of the room or section')
    length = fields.Float(string='Length(ft)', help='The length of the room')
    width = fields.Float(string='Width(ft)', help='The width of the room')
    height = fields.Float(string='Height(ft)', help='The height of the room')
    area = fields.Float(string='Area(ft²)', compute='_compute_area',
                        help='The total area of the room')
    property_id = fields.Many2one('property.property', string='Property',
                                  help='The corresponding property')

    @api.depends('length', 'width', 'height')
    def _compute_area(self):
        """ The total area of the room for each record is calculated """
        for rec in self:
            rec.area = rec.length * rec.width
