# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute


class ProductBrand(http.Controller):
    @http.route(['/shop/brand/<model("product.brand"):brand>'], type='http',
                auth="public", website=True)
    def brand_product(self, brand=None, page=0, search='', ppg=False, **post):

        brand_ids = request.env['product.brand']

        if brand:
            brand = brand_ids.search([('id', '=', int(brand))], limit=1)
        else:
            brand = brand_ids
        if brand:
            url = "/shop/brand/%s" % slug(brand)
        product_obj = request.env['product.template']
        product = product_obj.sudo().search(
            [('website_published', '=', True), ('brand_id', '=', brand.id)])
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4
        pager = request.website.pager(url=url, total=len(product), page=page,
                                      step=ppg)
        products = product_obj.sudo().search([('brand_id', '=', brand.id),
                                              ('website_published', '=', True)],
                                             order="id desc",
                                             offset=pager['offset'])
        keep = QueryURL('shop/brand')
        values = {
            'pager': pager,
            'products': products,
            'bins': TableCompute().process(products, ppg, ppr),
            'rows': ppr,
            'keep': keep, }
        return request.render("website_sale.products", values)
