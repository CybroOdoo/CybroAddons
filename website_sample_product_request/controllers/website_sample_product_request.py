# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil (<https://www.cybrosys.com>)
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
from werkzeug.exceptions import NotFound
from odoo.http import request
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
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
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

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if
                         v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list, min_price=min_price,
                        max_price=max_price, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id,
                               partner=request.env.user.partner_id)

        filter_by_price_enabled = request.website.is_view_active(
            'website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = request.website.company_id.currency_id
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
        # No limit because attributes are obtained from complete product list
        product_count, details, fuzzy_search_term = request.website._search_with_fuzzy(
            "products_only", search,
            limit=None, order=self._get_search_order(post), options=options)
        search_product = details[0].get('results', request.env[
            'product.template']).with_context(bin_size=True)

        filter_by_price_enabled = request.website.is_view_active(
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
                # The if/else condition in the min_price / max_price value assignment
                # tackles the case where we switch to a list of products with different
                # available min / max prices than the ones set in the previous page.
                # In order to have logical results and not yield empty product lists, the
                # price filter is set to their respective available prices when the specified
                # min exceeds the max, and / or the specified max is lower than the available min.
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search([('product_tmpl_ids', 'in',
                                                  search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        pager = request.website.pager(url=url, total=product_count, page=page,
                                      step=ppg, scope=5, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]
        shop_type = post.get('type') if post.get('type') else False
        if shop_type:
            products = request.env['product.template'].search(
                [('is_sample_product', '=', True)])

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([
                ('product_tmpl_ids', 'in', search_product.ids),
                ('visibility', '=', 'visible'),
            ])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref(
                    'website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

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
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
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
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()
        sample_lines = order.order_line.filtered(
            lambda l: l.product_template_id.is_sample_product)
        order.is_sample_order = bool(sample_lines)
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
            _order = order
            # Keep the same pricelist context as the default cart before computing accessories
            if not request.env.context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()
        if post.get('type') == 'popover':
            return request.render("website_sale.cart_popover", values,
                                  headers={'Cache-Control': 'no-cache'})
        return request.render("website_sale.cart", values)
