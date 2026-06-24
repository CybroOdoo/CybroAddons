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
    """Model to manage and display restaurant guest reviews on the website."""
    _name = 'theme.restaurant.review'
    _description = 'Restaurant Review'
    _order = 'review_date desc, sequence asc, id desc'

    name = fields.Char(string='Guest Name', required=True,
                       help='Name of the guest who submitted the review.')
    rating = fields.Integer(string='Rating', default=5,
                            help='Rating value given by the guest.')
    review_text = fields.Text(string='Review', required=True,
                              help='Feedback or comments provided by the guest.')
    review_date = fields.Date(string='Review Date',
                              default=fields.Date.context_today,
                              help='Date on which the review was received.')
    avatar_url = fields.Char(string='Avatar URL',
                             help="URL of the guest's profile picture or avatar.")
    image_1920 = fields.Image(string='Guest Image',
                              help='Uploaded image of the guest.')
    is_published = fields.Boolean(string='Is Published', default=True,
                                  help='If checked, the review will be visible on the public website.')
    active = fields.Boolean(default=True, string='Active',
                            help='Determines if the record is active or archived.')
    sequence = fields.Integer(default=10, string='Sequence',
                              help='Ordering index for displaying reviews.')
    website_id = fields.Many2one('website', string='Website',
                                 help='The specific website where this review should be displayed.')
