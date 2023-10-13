# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Neeraj Krishnan V M, Saneen K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models, api
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    """Inherit the model res.config.settings for adding the fields for
    selecting the product for website visitors and portal users"""
    _inherit = 'res.config.settings'

    product_visibility_guest_user = fields.Boolean(
        string="Product visibility Guest User", help="Product Visibility")
    filter_mode = fields.Selection([('product_only', 'Product Wise'),
                                    ('categ_only', 'Category Wise')],
                                   string='Filter Mode', default='product_only')
    available_products_for_guest_ids = fields.Many2many(
        'product.template',
        string='Available Product',
        domain="[('is_published', '=', True)]",
        help='The website will only display products which are within one of '
             'the selected category trees. If no category is specified,all '
             'available products will be shown')
    available_cat_for_guest_ids = fields.Many2many(
        'product.public.category',
        string='Available Product Categories',
        help='The website will only display products which are selected. If no '
             'product is specified,all available products will be shown')
    product_visibility_portal_user = fields.Boolean(
        string="Product visibility Portal User", help="Product Visibility")
    filter_mode_portal = fields.Selection([('product_only', 'Product Wise'),
                                           ('categ_only', 'Category Wise')],
                                          string='Filter Mode',
                                          default='product_only')
    available_products_for_portal_ids = fields.Many2many(
        'product.template',
        relation="available_product_for_portal_rel",
        string='Available Product',
        domain="[('is_published', '=', True)]",
        help='The website will only display products which are within one of '
             'the selected category trees. If no category is specified,all '
             'available products will be shown')
    available_cat_for_portal_ids = fields.Many2many(
        'product.public.category',
        relation="available_cat_for_portal_rel",
        string='Available Product Categories',
        help='The website will only display products which are selected. If no '
             'product is specified,all available products will be shown')

    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'product_visibility_guest_user',
            self.product_visibility_guest_user)
        self.env['ir.config_parameter'].sudo().set_param(
            'product_visibility_portal_user',
            self.product_visibility_portal_user)
        self.env['ir.config_parameter'].sudo().set_param('filter_mode',
                                                         self.filter_mode)
        self.env['ir.config_parameter'].sudo().set_param(
            'filter_mode_portal', self.filter_mode_portal)
        if not self.product_visibility_guest_user:
            self.available_cat_for_guest_ids = None
            self.available_products_for_guest_ids = None
            self.env['ir.config_parameter'].sudo().set_param('filter_mode',
                                                             'product_only')
        if not self.product_visibility_portal_user:
            self.available_products_for_portal_ids = None
            self.available_cat_for_portal_ids = None
        if self.filter_mode == 'product_only':
            self.available_cat_for_guest_ids = None
        elif self.filter_mode == 'categ_only':
            self.available_products_for_guest_ids = None
        if self.filter_mode_portal == 'product_only':
            self.available_cat_for_portal_ids = None
        elif self.filter_mode_portal == 'categ_only':
            self.available_products_for_portal_ids = None
        self.env['ir.config_parameter'].sudo().set_param(
            'website_product_visibility.available_products_for_guest_ids',
            self.available_products_for_guest_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'website_product_visibility.available_products_for_portal_ids',
            self.available_products_for_portal_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'website_product_visibility.available_cat_for_guest_ids',
            self.available_cat_for_guest_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'website_product_visibility.available_cat_for_portal_ids',
            self.available_cat_for_portal_ids.ids)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        product_visibility_guest_user = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_visibility_guest_user')
        product_visibility_portal_user = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_visibility_portal_user')
        filter_mode = self.env['ir.config_parameter'].sudo().get_param(
            'filter_mode')
        filter_mode_portal = self.env['ir.config_parameter'].sudo().get_param(
            'filter_mode_portal')
        available_products_for_guest_ids = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.available_products_for_guest_ids',
                'False')) or []
        available_products_for_portal_ids = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.available_products_for_portal_ids',
                'False')) or []
        available_cat_for_guest_ids = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.available_cat_for_guest_ids',
                'False')) or []
        available_cat_for_portal_ids = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.available_cat_for_portal_ids',
                'False')) or []
        res.update(
            product_visibility_guest_user=product_visibility_guest_user,
            product_visibility_portal_user=product_visibility_portal_user,
            filter_mode=filter_mode if filter_mode else 'product_only',
            filter_mode_portal=filter_mode_portal if filter_mode_portal
            else 'product_only',
            available_products_for_guest_ids=[
                (6, 0, available_products_for_guest_ids)],
            available_products_for_portal_ids=[
                (6, 0, available_products_for_portal_ids)],
            available_cat_for_guest_ids=[(6, 0, available_cat_for_guest_ids)],
            available_cat_for_portal_ids=[(6, 0, available_cat_for_portal_ids)]
        )
        return res
