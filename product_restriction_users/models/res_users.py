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
from odoo import api, fields, models


class ResUsers(models.Model):
    """Inherited the res_users model for adding the products
    and product category"""
    _inherit = 'res.users'

    restricted_type = fields.Selection(
        [('product', 'Product'), ('category', 'Category')],
        string='Restriction Type', default='product',
        help='Choose Product or Category depending upon your need')
    allowed_product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_template_res_users_rel',
        column1='res_users_id',
        column2='product_template_id',
        string="Products",
        help='Allow specific products for assigned users')
    allowed_product_category_ids = fields.Many2many(
        comodel_name='product.category',
        string="Product Categories",
        help='Allow specific product categories for assigned users')
    is_admin = fields.Boolean(compute='_compute_is_admin',
                              help='Check whether the user is an admin or not')

    def write(self, vals):
        """Clear access caches when product restrictions are changed."""
        res = super().write(vals)
        if {'restricted_type', 'allowed_product_ids', 'allowed_product_category_ids'} & set(vals):
            self.env['ir.access']._clear_caches()
        return res

    @api.depends('group_ids')
    def _compute_is_admin(self):
        """Compute the value of is_admin based on whether the user is admin or not"""
        for user in self:
            user.is_admin = user._is_admin() or user.has_group('base.group_erp_manager')
