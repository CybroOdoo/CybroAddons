# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
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
###################################################################################

from odoo import fields, models, api
from ast import literal_eval


class ProductVisibility(models.Model):
    _inherit = 'res.partner'

    filter_mode = fields.Selection([('null', 'No Filter'), ('product_only', 'Product Wise'),
                                    ('categ_only', 'Category Wise')], string='Filter Mode',  default='null')
    website_available_product_ids = fields.Many2many('product.template', string='Available Product',
                                                     domain="[('is_published', '=', True)]",
                                                     help='The website will only display products which are within one '
                                                          'of the selected category trees. If no category is specified,'
                                                          ' all available products will be shown')
    website_available_cat_ids = fields.Many2many('product.public.category', string='Available Product Categories',
                                                 help='The website will only display products which are selected.'
                                                      ' If no product is specified,'
                                                      ' all available products will be shown')

    @api.onchange("filter_mode")
    def onchange_filter_mod(self):
        if self.filter_mode == 'null':
            self.website_available_cat_ids = None
            self.website_available_product_ids = None

class WebsiteGuestVisibility(models.TransientModel):
    _inherit = 'res.config.settings'

    product_visibility_guest_user = fields.Boolean(string="Product visibility Guest User")
    filter_mode = fields.Selection([('product_only', 'Product Wise'),
                                    ('categ_only', 'Category Wise')], string='Filter Mode', default='product_only')

    available_product_ids = fields.Many2many('product.template', string='Available Product',
                                             domain="[('is_published', '=', True)]",
                                             help='The website will only display products which are within one '
                                                  'of the selected category trees. If no category is specified,'
                                                  ' all available products will be shown')
    available_cat_ids = fields.Many2many('product.public.category', string='Available Product Categories',
                                         help='The website will only display products which are selected.'
                                              ' If no product is specified,'
                                              ' all available products will be shown')

    @api.model
    def set_values(self):
        res = super(WebsiteGuestVisibility, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('product_visibility_guest_user',
                                                         self.product_visibility_guest_user)
        self.env['ir.config_parameter'].sudo().set_param('filter_mode', self.filter_mode)
        if not self.product_visibility_guest_user:
            self.available_cat_ids = None
            self.available_product_ids = None
            self.env['ir.config_parameter'].sudo().set_param('filter_mode','product_only')
        if self.filter_mode == 'product_only':
            self.available_cat_ids = None
        elif self.filter_mode == 'categ_only':
            self.available_product_ids = None

        self.env['ir.config_parameter'].sudo().set_param('website_product_visibility.available_product_ids',
                                                         self.available_product_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('website_product_visibility.available_cat_ids',
                                                         self.available_cat_ids.ids)
        return res

    @api.model
    def get_values(self):
        res = super(WebsiteGuestVisibility, self).get_values()
        product_ids = literal_eval(self.env['ir.config_parameter'].sudo().get_param('website_product_visibility.available_product_ids', 'False'))
        cat_ids = literal_eval(self.env['ir.config_parameter'].sudo().get_param('website_product_visibility.available_cat_ids', 'False'))
        mod = self.env['ir.config_parameter'].sudo().get_param('filter_mode')
        res.update(
            product_visibility_guest_user=self.env['ir.config_parameter'].sudo().get_param(
                'product_visibility_guest_user'),
            filter_mode=mod if mod else 'product_only',
            available_product_ids=[(6, 0, product_ids)],
            available_cat_ids=[(6, 0, cat_ids)],
        )
        return res
