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
#############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit the product category for restricted the users for
     particular products"""
    _inherit = 'product.template'

    restrict_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='product_template_res_users_rel',
        column1='product_template_id',
        column2='res_users_id',
        string="Restrict Users",
        help="Restrict the users for particular products")
    is_product = fields.Boolean(string='Product Restriction',
                                default=True,
                                help="Enable product restriction")
    is_category = fields.Boolean(string='Category Restriction',
                                 default=True,
                                 help="Enable category restriction")

    def write(self, vals):
        """Clear access caches when product restrictions are changed."""
        res = super().write(vals)
        if 'restrict_user_ids' in vals:
            self.env['ir.access']._clear_caches()
        return res
