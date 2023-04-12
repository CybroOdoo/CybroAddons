# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers import main

from odoo.tools import lazy


class WebsiteSale(main.WebsiteSale):
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """This function helps to override the functionalites of a website shop"""
        add_qty = int(post.get('add_qty', 1))
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

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

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if
                         v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        keep = QueryURL('/shop', **self._shop_get_query_url_kwargs(
            category and int(category), search, min_price, max_price, **post))

        now = datetime.timestamp(datetime.now())
        pricelist = request.env['product.pricelist'].browse(
            request.session.get('website_sale_current_pl'))
        if not pricelist or request.session.get('website_sale_pricelist_time',
                                                0) < now - 60 * 60:  # test: 1 hour in session
            pricelist = website.get_current_pricelist()
            request.session['website_sale_pricelist_time'] = now
            request.session['website_sale_current_pl'] = pricelist.id

        request.update_context(pricelist=pricelist.id,
                               partner=request.env.user.partner_id)

        filter_by_price_enabled = website.is_view_active(
            'website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = website.company_id.currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency, pricelist.currency_id,
                request.website.company_id, fields.Date.today())
        else:
            conversion_rate = 1

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            pricelist=pricelist,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post
        )
        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(
            attrib_set, options, post, search, website)

        filter_by_price_enabled = website.is_view_active(
            'website_sale.filter_products_price')
        if filter_by_price_enabled:
            # TODO Find an alternative way to obtain the domain through the search metadata.
            Product = request.env['product.template'].with_context(
                bin_size=True)
            domain = self._get_search_domain(search, category, attrib_values)

            # This is ~4 times more efficient than a search for the cheapest and most expensive products
            from_clause, where_clause, where_params = Product._where_calc(
                domain).get_sql()
            query = f"""
                SELECT COALESCE(MIN(list_price), 0) * {conversion_rate}, COALESCE(MAX(list_price), 0) * {conversion_rate}
                  FROM {from_clause}
                 WHERE {where_clause}
            """
            request.env.cr.execute(query, where_params)
            available_min_price, available_max_price = request.env.cr.fetchone()

            if min_price or max_price:
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        website_domain = website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in',
                  search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = lazy(lambda: Category.search(categs_domain))

        if category:
            url = "/shop/category/%s" % slug(category)

        pager = website.pager(url=url, total=product_count, page=page,
                              step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        product_count = request.env['product.template'].search_count(
            [('pd', '=', True)])
        if product_count == 0:
            products = search_product[offset:offset + ppg]
        else:
            products = request.env['product.template'].search(
                [('pd', '=', True)])

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = lazy(lambda: ProductAttribute.search([
                ('product_tmpl_ids', 'in', search_product.ids),
                ('visibility', '=', 'visible'),
            ]))
        else:
            attributes = lazy(lambda: ProductAttribute.browse(attributes_ids))

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'
            request.session['website_sale_shop_layout_mode'] = layout_mode

        products_prices = lazy(lambda: products._get_sales_prices(pricelist))

        values = {
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_product': search_product,
            'search_count': product_count,  # common for all searchbox
            'bins': lazy(
                lambda: main.TableCompute().process(products, ppg, ppr)),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'products_prices': products_prices,
            'get_product_prices': lambda product: lazy(
                lambda: products_prices[product.id]),
            'float_round': tools.float_round,
        }
        if filter_by_price_enabled:
            values['min_price'] = min_price or available_min_price
            values['max_price'] = max_price or available_max_price
            values['available_min_price'] = tools.float_round(
                available_min_price, 2)
            values['available_max_price'] = tools.float_round(
                available_max_price, 2)
        if category:
            values['main_object'] = category
        values.update(self._get_additional_shop_values(values))
        return request.render("website_sale.products", values)


class WebsiteEcoFoodNewArrivals(http.Controller):

    @http.route('/eco_food_new_arrivals', auth="public", type='json',
                website=True)
    def eco_food_new_arrivals(self):
        """this function used to create new arrivals products"""

        new_arrival = request.env['new.arrival'].sudo().search([])
        products = {
            'new_arrival': new_arrival.new_arrivals_ids.read()
        }
        return products

    @http.route('/add_to_cart/<int:id>', auth="public", type='http',
                website=True)
    def add_to_cart(self, id):
        """this function is used for adding to cart"""
        product = \
        request.env['product.product'].search([('product_tmpl_id', '=', id)])[
            0]
        so = request.website.sale_get_order(force_create=True)
        so._cart_update(
            product_id=product.id,
            add_qty=1,
            set_qty=1
        )

        return request.redirect('/shop/cart')

    @http.route('/add_to_wishlist_new_arrival/<int:product_id>', auth="public",
                type='http', website=True)
    def add_to_wishlist(self, product_id, **kw):
        """this function is used for adding to wishlist"""
        prod_id = request.env['product.template'].browse(product_id)
        product_ids = prod_id._create_first_product_variant().id
        website = request.website
        pricelist = website.pricelist_id
        product = request.env['product.product'].browse(product_ids)

        price = product._get_combination_info_variant(
            pricelist=website.pricelist_id,
        )['price']

        Wishlist = request.env['product.wishlist']
        if request.website.is_public_user():
            Wishlist = Wishlist.sudo()
            partner_id = False
        else:
            partner_id = request.env.user.partner_id.id

        wish = Wishlist._add_to_wishlist(
            pricelist.id,
            pricelist.currency_id.id,
            request.website.id,
            price,
            product_ids,
            partner_id
        )

        if not partner_id:
            request.session['wishlist_ids'] = request.session.get(
                'wishlist_ids', []) + [wish.id]

        return request.redirect('/shop/wishlist')

    @http.route('/cart_quantity_minus', auth="public", type='json',
                website=True)
    def cart_quantity_minus(self, line_id):
        """this function is used for cart quantity minus"""

        so = request.website.sale_get_order()
        for rec in so.order_line:
            if rec.id == line_id:
                rec.product_uom_qty -= 1

    @http.route('/cart_quantity_plus', auth="public", type='json',
                website=True)
    def cart_quantity_plus(self, line_id):
        """this function is used for cart quantity plus"""

        so = request.website.sale_get_order()
        for rec in so.order_line:
            if rec.id == line_id:
                rec.product_uom_qty += 1

    @http.route('/cart/del/my/product', auth="public", type='json',
                website=True)
    def delete_cart_products(self, line_id):
        """this function is used for cart quantity delete product"""

        so = request.website.sale_get_order()
        id = int(line_id)
        for rec in so.order_line:
            if rec.id == id:
                rec.unlink()

    @http.route('/get_best_seller', auth="public", type='json', website=True)
    def get_best_seller(self):
        """this function is used for get bestseller product"""

        best_seller = request.env['dynamic.products'].sudo().search([])
        values = {
            'best_seller': best_seller.product_tmpl_ids.read()
        }
        return values

    @http.route('/get_featured_products', auth="public", type='json',
                website=True)
    def get_featured_products(self):
        """this function is used for get featured products"""
        featured_product = request.env['featured.products'].sudo().search([],
                                                                          limit=8)

        product = [rec.read()[0] for rec in featured_product]
        slide1 = []
        slide2 = []
        slide3 = []
        slide4 = []

        for rec in featured_product.featured_products_ids:
            if len(slide1) < 2:
                slide1.append(rec.read())
            elif len(slide2) < 2:
                slide2.append(rec.read())
            elif len(slide3) < 2:
                slide3.append(rec.read())
            elif len(slide4) < 2:
                slide4.append(rec.read())

        values = {
            'slide1': slide1,
            'slide2': slide2,
            'slide3': slide3,
            'slide4': slide4,
        }
        return values

    @http.route('/get_recently_added_products', auth="public", type='json',
                website=True)
    def get_recently_added_products(self):
        """this is the function that will return the most recently added products"""
        recently_added_prod = request.env[
            'recently_added.products'].sudo().search([], order='id desc',
                                                     limit=16)

        recent = [rec.read()[0] for rec in recently_added_prod]
        slide1 = []
        slide2 = []

        for rec in recently_added_prod.recent_products_ids:
            if len(slide1) < 6:
                slide1.append(rec.read())
            elif len(slide2) < 6:
                slide2.append(rec.read())

        values = {
            'slide1': slide1,
            'slide2': slide2
        }
        return values
