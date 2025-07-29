# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class OGConfiguration(models.Model):
    """Contains fields to add necessary values for snippets"""
    _name = 'og.configuration'
    _description = 'OG Configuration'

    name = fields.Char(string='Name', help="Name of the Configuration.")
    category_id = fields.Many2one(
        'product.public.category',
        string="Product Category",
        help="Select the product category to display products from.")
    best_products_ids = fields.Many2many('product.product',
                                         string="Best Products",
                                         help="Choose multiple products "
                                              "to display as Best Products",
                                         domain="[('sale_ok', '=', True)]")
