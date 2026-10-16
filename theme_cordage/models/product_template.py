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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit product template to add custom fields for cordage theme."""
    _inherit = 'product.template'

    x_cordage_badge = fields.Char(string='Cordage Badge', help='Badge to be displayed on the product')
    x_cordage_rating = fields.Float(string='Cordage Rating', help='Rating of the product')
    x_cordage_reviews = fields.Integer(string='Cordage Reviews', help='Number of reviews for the product')
    x_cordage_unit = fields.Char(string='Cordage Unit', help='Unit of the product')
    x_cordage_price_per_meter = fields.Float(string='Cordage Price / Metre', help='Price per meter of the product')
    x_cordage_tags = fields.Char(string='Cordage Tags', help='Tags of the product')
    x_cordage_rope_class = fields.Char(string='Cordage Rope Class', help='Rope class of the product')
