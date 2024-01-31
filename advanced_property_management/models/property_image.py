# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class PropertyImages(models.Model):
    """A class for the model property image to represent
    the related images for a property"""
    _name = 'property.image'
    _description = 'Property Images'

    name = fields.Char(string='Name', required=True,
                       help='Name for the given image')
    description = fields.Text(string='Description',
                              help='A brief description of the image given')
    image = fields.Binary(string='Image', required=True,
                          help='The properties image')
    property_id = fields.Many2one('property.property',
                                  string='Property',
                                  help='Related property')
