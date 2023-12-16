# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Neeraj Krishnan V M , Saneen K(<https://www.cybrosys.com>)
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
###############################################################################
from werkzeug.exceptions import NotFound
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo import fields, http, tools
from ast import literal_eval
from odoo.http import request
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression
from datetime import datetime
from odoo.tools import lazy


class ProductVisibilityCon(WebsiteSale):

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}
        category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def reset_domain(self, search, categories, available_products,
                     attrib_values, search_in_description=True):
        """
        Function returns a domain consist of filter conditions
        :param search: search variable
        :param categories: list of category available
        :param available_products: list of available product ids from
                    product.template
        :param attrib_values:product attiribute values
        :param search_in_description: boolean filed showing there is search
         variable exist or not"""

        domains = [request.website.sale_product_domain()]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('product_variant_ids.default_code', 'ilike', srch)]]
                if search_in_description:
                    subdomains.append([('description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))
        if available_products:
            domains.append([('id', 'in', available_products.ids)])
        if categories:
            domains.append([('public_categ_ids', 'child_of', categories.ids)])
        return expression.AND(domains)

    @http.route(type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        available_categ = available_products = ''
        user = request.env['res.users'].sudo().search(
            [('id', '=', request.env.user.id)])
        if not user:
            mode = request.env['ir.config_parameter'].sudo().get_param(
                'filter_mode')
            products = literal_eval(
                request.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.'
                    'available_products_for_guest_ids', 'False'))
            if mode == 'product_only':
                available_products = request.env['product.template'].search(
                    [('id', 'in', products)])
            cat = literal_eval(
                request.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.available_cat_for_guest_ids',
                    'False'))
            available_categ = request.env['product.public.category'].search(
                [('id', 'in', cat)])
            Category_avail = []
            Category = request.env['product.public.category']
            for ids in available_categ:
                if not ids.parent_id.id in available_categ.ids:
                    Category_avail.append(ids.id)
            categ = request.env['product.public.category'].search(
                [('id', 'in', Category_avail)])
            if mode == 'product_only':
                categ = Category.search([(
                    'product_tmpl_ids', 'in', available_products.ids)])
        else:
            partner = request.env['res.partner'].sudo().search(
                [('id', '=', user.partner_id.id)])
            mode = partner.filter_mode
            if mode == 'product_only':
                available_products = self.available_products()
            available_categ = partner.website_available_cat_ids
            Category_avail = []
            Category = request.env['product.public.category']
            for ids in available_categ:
                if not ids.parent_id.id in available_categ.ids:
                    Category_avail.append(ids.id)
            categ = request.env['product.public.category'].search(
                [('id', 'in', Category_avail)])
            if mode == 'product_only':
                categ = Category.search([(
                    'product_tmpl_ids', 'in', available_products.ids)])
        if not available_categ and not available_products and \
                request.env.user.has_group(
                    'base.group_portal'):
            mode = request.env['ir.config_parameter'].sudo().get_param(
                'filter_mode_portal')
            products = literal_eval(
                request.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.'
                    'available_products_for_portal_ids', 'False'))
            if mode == 'product_only':
                available_products = request.env['product.template'].search(
                    [('id', 'in', products)])
            cat = literal_eval(
                request.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.available_cat_for_portal_ids',
                    'False'))
            available_categ = request.env['product.public.category'].search(
                [('id', 'in', cat)])
            Category_avail = []
            Category = request.env['product.public.category']
            for ids in available_categ:
                if not ids.parent_id.id in available_categ.ids:
                    Category_avail.append(ids.id)
            categ = request.env['product.public.category'].search(
                [('id', 'in', Category_avail)])
            if mode == 'product_only':
                categ = Category.search([(
                    'product_tmpl_ids', 'in', available_products.ids)])
        if not available_categ and not available_products:
            return super(ProductVisibilityCon, self).shop(page, category,
                                                          search, ppg, **post)
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
            ppg = request.env['website'].get_current_website().shop_ppg or 20
        ppr = request.env['website'].get_current_website().shop_ppr or 4
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if
                         v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        domain = self._get_search_domain(search, category, attrib_values)
        Product = request.env['product.template'].with_context(bin_size=True)
        if available_products:
            domain_pro = self.reset_domain(search, category, available_products,
                                           attrib_values)
            Product = Product.search(domain_pro)
        keep = QueryURL('/shop', **self._shop_get_query_url_kwargs(
            category and int(category), search, min_price, max_price, **post))
        now = datetime.timestamp(datetime.now())
        pricelist = request.env['product.pricelist'].browse(
            request.session.get('website_sale_current_pl'))
        if not pricelist or request.session.get('website_sale_pricelist_time',
                                                0) < now - 60 * 60:
            # test: 1 hour in session
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
        fuzzy_search_term, product_count, search_product = \
            self._shop_lookup_products(
                attrib_set, options, post, search, website)
        filter_by_price_enabled = website.is_view_active(
            'website_sale.filter_products_price')
        if filter_by_price_enabled:
            # TODO Find an alternative way to obtain the domain through the
            #  search metadata.
            Product = request.env['product.template'].with_context(
                bin_size=True)
            domain = self._get_search_domain(search, category, attrib_values)
            # This is ~4 times more efficient than a search for the cheapest
            # and most expensive products
            from_clause, where_clause, where_params = Product._where_calc(
                domain).get_sql()
            query = f"""
                   SELECT COALESCE(MIN(list_price), 0) * {conversion_rate}, 
                   COALESCE(MAX(list_price), 0) * {conversion_rate}
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
                    min_price = min_price if min_price <= available_max_price \
                        else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price \
                        else available_max_price
                    post['max_price'] = max_price
        website_domain = website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if not category:
            domain = self.reset_domain(search, available_categ,
                                       available_products, attrib_values)
        search_product = Product.search(domain)
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False), (
            'product_tmpl_ids', 'in', search_product.ids)] + website_domain
        if search:
            search_categories = Category.search(
                [(
                    'product_tmpl_ids', 'in',
                    search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = available_categ
        categs = lazy(lambda: Category.search(categs_domain))
        if category:
            url = "/shop/category/%s" % slug(category)
        product_count = len(search_product)
        pager = website.pager(url=url, total=product_count, page=page, step=ppg,
                              scope=7, url_args=post)
        offset = pager['offset']
        products = Product.search(domain, limit=ppg, offset=pager['offset'],
                                  order=self._get_search_order(post))
        if not category:
            if available_products:
                products = Product.search(domain_pro, limit=ppg,
                                          offset=pager['offset'],
                                          order=self._get_search_order(post))
            else:
                products = Product.search(domain, limit=ppg,
                                          offset=pager['offset'],
                                          order=self._get_search_order(post))
        else:
            if available_products:
                products = Product.search(domain_pro, limit=ppg,
                                          offset=pager['offset'],
                                          order=self._get_search_order(post))
            else:
                products = Product.search(domain, limit=ppg,
                                          offset=pager['offset'],
                                          order=self._get_search_order(post))
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
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categ,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': categ.ids,
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

    def available_products(self):
        """Returns the available product (product.template) ids"""
        user = request.env['res.users'].sudo().search(
            [('id', '=', request.env.user.id)])
        partner = request.env['res.partner'].sudo().search(
            [('id', '=', user.partner_id.id)])
        return partner.website_available_product_ids
