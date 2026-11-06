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
    """Store an optional image for each internal product category and flag the
    categories shown by the Petzen category / product snippets."""
    _inherit = 'product.category'

    image_1920 = fields.Image(
        string="Image", max_width=1920, max_height=1920,
        help="Image of the category tile on the Petzen home page; a default "
             "picture is used when it is empty.")
    is_pets_category = fields.Boolean(
        string="Pets Category",
        help="Show this category (and the products of its sub-categories) in "
             "the Petzen \"Shop by Category\" and products snippets.")
