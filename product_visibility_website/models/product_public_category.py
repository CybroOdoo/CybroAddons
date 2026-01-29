# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Neeraj Krishnan V M(<https://www.cybrosys.com>)
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

from ast import literal_eval

from odoo import api, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'
    """Inherit the product.public.category model to filter the categories based 
       on the user's filter mode"""

    @api.model
    def _search_fetch(self, search_detail, search, limit, order):
        results, count = super(ProductPublicCategory, self)._search_fetch\
            (search_detail, search, limit, order)
        filter_mode = self.env['ir.config_parameter'].sudo().get_param\
            ('filter_mode')
        if not self.env.user.active and filter_mode == 'categ_only':
            category = literal_eval(self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.available_cat_ids'))
            results = results.filtered(lambda r: r.id in category)
        else:
            partner = self.env.user.partner_id
            if partner.filter_mode == 'categ_only':
                category = partner.website_available_cat_ids.ids
                results = results.filtered(lambda r: r.id in category)
            elif partner.filter_mode == 'product_only':
                products = partner.website_available_product_ids.ids
                results = results.filtered(lambda r: any(item in r.product_tmpl_ids.ids
                                                         for item in products))
        return results, len(results)


