# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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


class ThemeRestaurantReview(models.Model):
    """Model to store and manage restaurant reviews submitted by guests on the website."""
    _name = 'theme.restaurant.review'
    _description = 'Restaurant Review'
    _inherit = ['website.published.mixin']
    _order = 'review_date desc, sequence asc, id desc'
    
    is_published = fields.Boolean(
        string='Is Published', help="Whether this review is visible on the website.", default=True)
    name = fields.Char(
        string='Guest Name', help="Name of the guest who provided the review.", required=True)
    sequence = fields.Integer(
        string='Sequence', help="Determine the display order of the reviews.", default=10)
    active = fields.Boolean(
        string='Active', help="Whether this review record is active.", default=True)
    website_id = fields.Many2one(
        'website', string='Website', help="The website where this review was submitted.",
        required=True, default=lambda self: self.env['website'].get_current_website())
    review_date = fields.Date(
        string='Review Date', help="The date when the review was submitted.",
        required=True, default=fields.Date.context_today)
    rating = fields.Integer(
        string='Rating', help="The star rating given by the guest (1 to 5).",
        required=True, default=5)
    review_text = fields.Text(
        string='Review Text', help="The content of the guest's review.", required=True)
    avatar_url = fields.Char(
        string='Avatar URL', help="URL of the guest's avatar image.")
    image_1920 = fields.Image(
        string='Avatar Image', help="Upload an image for the guest's avatar.",
        max_width=1920, max_height=1920)

    _sql_constraints = [
        ('theme_restaurant_review_rating_check', 'CHECK(rating >= 1 AND rating <= 5)', 'Rating must be between 1 and 5.'),
    ]
