# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.main import TableCompute


class WebsiteSales(WebsiteSale):
    """View of Product Brands in Website"""

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):categorys>/page/<int:page>''',
        '''/shop/brand/<model("product.brand"):brand>''',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, brand=None,
             **post):
        """
        Defined a url for product brands inside the existing function and controller of WebsiteSale
        """
        res = super(WebsiteSales, self).shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, brand=brand,
                    **post)
        website = request.env['website'].get_current_website()
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4
        Brand = request.env['product.brand']
        url = "/shop"
        if not brand:
            brand = Brand
        if category:
            url = "/shop/category/%s" % slug(category)

        Brand = request.env['product.brand'].search([])
        if brand:
            products_brand = request.env['product.template'].search(
                ['&', ('brand_id', '=', brand.id), ('sale_ok', '=', True), ('is_published', '=', True)])
            product_brand_count = len(products_brand)
            pager_brand = request.website.pager(url=url, total=product_brand_count, page=page, step=ppg, scope=7,
                                                url_args=post)
            res.qcontext.update({
                'brand': brand,
                'pager': pager_brand,
                'products': products_brand,
                'search_count': product_brand_count,  # common for all searchbox
                'bins': TableCompute().process(products_brand, ppg, ppr),
                'brands': Brand})
        else:
            res.qcontext.update({
                'brand': brand,
                'brands': Brand})
        return res


class ProductBrandWebsite(http.Controller):
    """Returns the featured brands"""

    @http.route(['/product_brand'], type="json", auth="public",
                methods=['POST'])
    def featured_brands(self):
        """Returns the brand name, image &id of the featured brands"""
        brands = http.request.env['product.brand'].search_read(
            [('is_featured_brand', '=', True)], ['name', 'brand_image', 'id'])
        return brands
