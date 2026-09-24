# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import models, fields

class PropertyAmenity(models.Model):
    """
    Model to store various amenities available for properties (e.g., Gym, Pool).
    """
    _name = 'property.amenity'
    _description = 'Property Amenity'

    name = fields.Char(string="Name", required=True)
    icon = fields.Char(string="Icon Class")

class ProductTemplate(models.Model):
    """
    Extends the product.template model to include property-specific fields
    such as beds, baths, location, and square feet.
    """
    _inherit = 'product.template'

    is_property = fields.Boolean(string="Is Property", default=False)
    bed = fields.Integer(string="Beds")
    bath = fields.Integer(string="Baths")
    location = fields.Char(string="Location")
    squarefeet = fields.Integer(string="Squarefeet")
    listing_type = fields.Selection([
        ('rent', 'For Rent'),
        ('sale', 'For Sale')
    ], string="Listing Type", default='sale')
    property_type = fields.Selection([
        ('house', 'House'),
        ('villa', 'Villa'),
        ('apartment', 'Apartment'),
        ('commercial', 'Commercial'),
        ('studio', 'Studio'),
        ('office', 'Office')
    ], string="Property Type")
    amenity_ids = fields.Many2many('property.amenity', string="Amenities")
    is_featured = fields.Boolean(string="Is Featured", default=False)
    salesperson_id = fields.Many2one('res.users', string="Salesperson", required=True)

