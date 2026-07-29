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
    """Extend products with tour and hotel details for the Flynova theme."""

    _inherit = 'product.template'

    flynova_listing_type = fields.Selection(
        [
            ('tour', 'Tour'),
            ('hotel', 'Hotel'),
        ],
        string='Flynova Listing Type',
        help='Select whether this product is listed as a Tour or Hotel on the website.')
    duration = fields.Char(
        string='Duration',
        help='Trip or stay duration shown on the listing card, e.g. "5 Days / 4 Nights".')
    location_name = fields.Char(
        string='Location',
        help='Destination name displayed on the website, e.g. "Dubai, UAE".')
    gallery_image_ids = fields.Many2many(
        'ir.attachment', string='Gallery Images',
        help='Additional images shown in the product detail page gallery carousel.')
    included_details = fields.Text(
        string='Included Details',
        help='Services or amenities included in the package, one item per line.')
    excluded_details = fields.Text(
        string='Excluded Details',
        help='Services or items not covered by the package, one item per line.')
