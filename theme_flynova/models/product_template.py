# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Product Template"""
    _inherit = 'product.template'

    flynova_listing_type = fields.Selection(
        [
            ('tour', 'Tour'),
            ('hotel', 'Hotel'),
        ],
        string="Flynova Listing Type",
        help="Used by the Flynova theme to decide whether this product appears as a tour or a hotel."
    )
    duration = fields.Char(string="Duration", help="e.g. 1 Week, 5 Days")
    location_name = fields.Char(string="Location", help="e.g. Thailand, Japan")
    gallery_image_ids = fields.Many2many(comodel_name='ir.attachment', string="Gallery Images",
                                         help="Additional images displayed in the photo gallery on the product detail page.")
    included_details = fields.Text(string="Included Details", help="List items separated by new lines")
    excluded_details = fields.Text(string="Excluded Details", help="List items separated by new lines")
