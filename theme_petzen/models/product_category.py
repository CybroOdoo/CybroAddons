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


class ProductCategory(models.Model):
    """Petzen fields used by the website category and product snippets."""
    _inherit = 'product.category'

    image_1920 = fields.Image(
        string='Image', max_width=1920, max_height=1920,
        help="Image of the category tile on the website "
             "(\"Shop by Category\"). Without image, "
             "the default image of the theme is used.")
    is_pets_category = fields.Boolean(
        string='Show in Petzen Snippets',
        help='Show this category in the Petzen "Shop by Category" block and '
             'show products assigned to it or one of its sub-categories in '
             'the Petzen products block.')
