# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request
from odoo.tools import lazy
from werkzeug.exceptions import NotFound
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale

class WebsiteShop(WebsiteSale):
    """Shop Controller
        super the controller to set 3 columns of products in
        website shop instead of 4 """
    @http.route(['/shop/config/website'], type='jsonrpc', auth='user')
    def _change_website_config(self, **options):
        """ Function for shop configuration """
        if not request.env.user.has_group(
                'website.group_website_restricted_editor'):
            raise NotFound()
        current_website = request.env.website or request.env['website'].browse(
            request.env.context['host_id'])
        # Restrict options we can write to.
        writable_fields = {
            'shop_ppg', 'shop_ppr', 'shop_default_sort',
            'product_page_image_layout', 'product_page_image_width',
            'product_page_grid_columns', 'product_page_image_spacing'
        }
        # Default ppg to 1.
        if 'ppg' in options and not options['ppg']:
            options['ppg'] = 1
        if 'product_page_grid_columns' in options:
            options['product_page_grid_columns'] = int(
                options['product_page_grid_columns'])
        write_vals = {k: v for k, v in options.items() if k in writable_fields}
        if write_vals:
            current_website.write(write_vals)
        current_website.select = True

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Function for website shop"""
        current_website = request.env.website or request.env['website'].browse(
            request.env.context['host_id'])
        if current_website.select:
            ppg = current_website.shop_ppg
            ppr = current_website.shop_ppr
        else:
            ppg = 12
            ppr = 3
        res = super().shop(page=page, category=category, search=search,
                           min_price=min_price, max_price=max_price, ppg=ppg,
                           **post)
        products = res.qcontext['products']
        res.qcontext.update({
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
            'ppr': ppr,
        })
        return res
