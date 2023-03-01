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
import datetime

from werkzeug.exceptions import NotFound
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale
from odoo import http
from odoo.http import request
from odoo import fields


class WebsiteProduct(http.Controller):
    """Class for dynamic snippets for products"""

    @http.route('/get_featured_product', auth='public', type='json',
                website=True)
    def get_featured_products(self):
        """Function to get featured products"""
        silon_configuration = request.env.ref(
            'theme_silon.silon_configuration_data')
        product_id = silon_configuration.featured_product_ids
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        for product in product_id:
            combination_info = product._get_combination_info_variant()
            res_product = product.read(['id', 'name', 'website_url',
                                        'rating_avg', 'rating_count'])[0]
            res_product['ratings'] = round(res_product['rating_avg'], 2)
            res_product['rating'] = rating
            res_product.update(combination_info)
            res['products'].append(res_product)
        products = res['products']
        values = {'products': products}
        response = http.Response(
            template='theme_silon.featured_product_snippet', qcontext=values)
        return response.render()

    @http.route('/get_popular_product', auth='public', type='json',
                website=True)
    def get_popular_products(self):
        """Function to get Popular Products"""
        products = request.env['product.template'].sudo().search([])
        for each in products:
            each.qty_sold = 0
            each.top_selling = False
        date = fields.Datetime.now()
        date_before = date - datetime.timedelta(days=7)
        orders = request.env['sale.order'].sudo().search([
            ('date_order', '<=', date),
            ('date_order', '>=',
             date_before),
            ('website_id', '!=', False),
            ('state', 'in', (
                'sale', 'done'))])
        for order in orders:
            order_line = order.order_line
            for product in order_line:
                product.product_id.qty_sold = product.product_id.qty_sold + 1
        website_product_ids = request.env['product.template'].sudo().search(
            [('is_published', '=', True),
             ('qty_sold', '!=', 0)],
            order='qty_sold desc', limit=4)

        website_product_ids.top_selling = True
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        for product in website_product_ids:
            combination_info = product._get_combination_info()
            res_product = product.read(['id', 'name', 'website_url',
                                        'rating_avg', 'rating_count'])[0]
            res_product['ratings'] = round(res_product['rating_avg'], 2)
            res_product.update(combination_info)
            res_product['rating'] = rating
            res['products'].append(res_product)
        products = res['products']
        values = {'website_product_ids': products}
        response = http.Response(
            template='theme_silon.popular_snippet', qcontext=values)
        return response.render()

    @http.route('/get_trending_product', auth='public', type='json',
                website=True)
    def get_trending_product(self):
        """Function to get Trending Products"""
        products = request.env['product.template'].sudo().search([])
        for each in products:
            each.views = 0
            each.most_viewed = False
        date = fields.Datetime.now()
        date_before = date - datetime.timedelta(days=7)
        products = request.env['website.track'].sudo().search(
            [('visit_datetime', '<=', date),
             ('visit_datetime', '>=', date_before),
             ('product_id', '!=', False)])
        for pro in products:
            pro.product_id.views = pro.product_id.views + 1

        product_ids = request.env['product.template'].sudo().search(
            [('is_published', '=', True),
             ('views', '!=', 0)],
            order='views desc', limit=8)

        product_ids.most_viewed = True
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        for product in product_ids:
            combination_info = product._get_combination_info()
            res_product = product.read(['id', 'name', 'website_url',
                                        'rating_avg', 'rating_count'])[0]
            res_product['ratings'] = round(res_product['rating_avg'], 2)
            res_product.update(combination_info)
            res_product['rating'] = rating
            res['products'].append(res_product)
        products = res['products']
        values = {'product_ids': products}
        response = http.Response(
            template='theme_silon.trending_snippet', qcontext=values)
        return response.render()


class PriceFilter(WebsiteSale):
    """Price filtering Class"""

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        """Override WebsiteSale shop for Price Filter"""
        maximum = minimum = 0
        add_qty = int(post.get('add_qty', 1))
        product_category = request.env['product.public.category']
        if category:
            category = product_category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = product_category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        product_ids = request.env['product.template'].search(
            ['&', ('sale_ok', '=', True), ('active', '=', True)])

        if product_ids and product_ids.ids:
            request.cr.execute(
                'select min(list_price),max(list_price) from product_template where id in %s',
                (tuple(product_ids.ids),))
            list_prices = request.cr.fetchall()

            minimum = list_prices[0][0]
            maximum = list_prices[0][1]

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values)
        if post.get('minimum') and post.get('maximum'):
            domain = domain + [('list_price', '>=', float(post.get('minimum'))),
                               ('list_price', '<=', float(post.get('maximum')))]

        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list,
                        order=post.get('order'), minimum=post.get('minimum'),
                        maximum=post.get('maximum'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(
            request.context, pricelist=pricelist.id,
            partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        product_template = request.env['product.template'].with_context(bin_size=True)

        search_product = product_template.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = product_category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = product_category
        categs = product_category.search(categs_domain)

        if category:
            url = f'{"/shop/category/%s"}' % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count,
                                      page=page, step=ppg, scope=7,
                                      url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]

        product_attribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = product_attribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = product_attribute.browse(attributes_ids)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'minimum': minimum,
            'maximum': maximum,

        }
        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)
