# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Rosmy John (<https://www.cybrosys.com>)
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
#############################################################################
from datetime import datetime
from werkzeug.exceptions import NotFound
from odoo.http import request
from odoo.tools import lazy
from odoo import fields, http, tools
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    """This class inherits from the base WebsiteSale class and includes
    overridden methods and additional functionality for handling sample
    products in the shop,creating sitemap entries for categories, and
    managing the shopping cart."""

    def sitemap_shop(env, rule, qs):
        """This function is overridden to create category.
        Generate sitemap entries for categories in the shop.
           Args:
           env(env): Environment of the function.
           rule: The Sitemap rule object.
           qs (str): Query string parameter.
           Returns:
              yield (dict):Sitemap entries for shop categories."""
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}
        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """This function is used to create sample products shop.
        page:Representing the page number for pagination.
        category: An optional parameter specifying the category of products
        to display.
        search: An optional string representing the search term entered by
        the user.
        min_price: An optional float indicating the minimum price for
        filtering products.
        max_price: An optional float indicating the maximum price for
        filtering products.
        ppg: A boolean indicating whether to override the number of
        products per page.
        **post: Additional keyword arguments that can be passed to the function.
        return: If `shop_type` is set, render a sample order template view.
             Otherwise, render the products template with the necessary values.
        """
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
        keep = QueryURL('/shop',
                        **self._shop_get_query_url_kwargs(
                            category and int(category), search, min_price,
                            max_price,
                            **post))
        now = datetime.timestamp(datetime.now())
        pricelist = request.env['product.pricelist'].browse(
            request.session.get('website_sale_current_pl'))
        if not pricelist or request.session.get('website_sale_pricelist_time',
                                                0) < now - 60 * 60:
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
        fuzzy_search_term, product_count, search_product = (
            self._shop_lookup_products(attrib_set, options, post,
                                       search, website))
        filter_by_price_enabled = website.is_view_active(
            'website_sale.filter_products_price')
        if filter_by_price_enabled:
            product = request.env['product.template'].with_context(
                bin_size=True)
            domain = self._get_search_domain(search, category, attrib_values)
            from_clause, where_clause, where_params = product._where_calc(
                domain).get_sql()
            query = (
                f"SELECT COALESCE(MIN(list_price), 0) * {conversion_rate}, "
                f"COALESCE(MAX(list_price), 0) * {conversion_rate} "
                f"FROM {from_clause} "
                f"WHERE {where_clause}"
            )
            request.env.cr.execute(query, where_params)
            available_min_price, available_max_price = request.env.cr.fetchone()
            if min_price or max_price:
                if min_price:
                    min_price = min_price if min_price <= available_max_price \
                        else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price \
                        else available_max_price
                    post['max_price'] = max_price
        website_domain = website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [(
                    'product_tmpl_ids', 'in',
                    search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = lazy(lambda: Category.search(categs_domain))
        if category:
            url = "/shop/category/%s" % slug(category)
        pager = website.pager(url=url, total=product_count, page=page, step=ppg,
                              scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]
        shop_type = post.get('type') if post.get('type') else False
        if shop_type:
            products = request.env['product.template'].search(
                [('is_sample_product', '=', True)])
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
        fiscal_position_id = website._get_current_fiscal_position_id(
            request.env.user.partner_id)
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
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
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
            'fiscal_position_id': fiscal_position_id,
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
        if shop_type:
            return request.render(
                "website_sample_product_request.sample_order_template_view",
                values)
        else:
            return request.render("website_sale.products", values)

    @http.route(['/shop/cart'], type='http', auth="public", website=True,
                sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        """This function is used to create sample product cart."""
        order = request.website.sale_get_order()
        sample_order_line = order.order_line
        for rec in sample_order_line:
            if rec.product_template_id.is_sample_product:
                order.is_sample_order = True
            else:
                order.is_sample_order = False
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()
        request.session['website_sale_cart_quantity'] = order.cart_quantity
        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search(
                [('access_token', '=', access_token)], limit=1)
            if not abandoned_order:
                raise NotFound()
            if abandoned_order.state != 'draft':
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (
                    revive == 'merge' and not request.session.get(
                'sale_order_id')):
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write(
                    {'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get(
                    'sale_order_id'):
                values.update({'access_token': abandoned_order.access_token})
        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            order.order_line.filtered(
                lambda l: not l.product_id.active).unlink()
            values['suggested_products'] = order._cart_accessories()
            values.update(self._get_express_shop_payment_values(order))
        if post.get('type') == 'popover':
            return request.render("website_sale.cart_popover", values,
                                  headers={'Cache-Control': 'no-cache'})
        return request.render("website_sale.cart", values)
