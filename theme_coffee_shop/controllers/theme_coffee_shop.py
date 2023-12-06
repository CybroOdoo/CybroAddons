# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
from collections import defaultdict
from datetime import datetime
from itertools import product as cartesian_product
from werkzeug.exceptions import NotFound
from odoo import http, tools
from odoo.http import request
from odoo.osv import expression
from odoo.tools import lazy
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom


class TableComputeCoffee(object):
    """ Compute data related to coffee shop theme """

    def __init__(self):
        """ The init for menu page"""
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey, ppr):
        """Function for check place"""
        res = True
        for yaxix in range(sizey):
            for xaxix in range(sizex):
                if posx + xaxix >= ppr:
                    res = False
                    break
                row = self.table.setdefault(posy + yaxix, {})
                if row.setdefault(posx + xaxix) is not None:
                    res = False
                    break
            for x in range(ppr):
                self.table[posy + yaxix].setdefault(xaxix, None)
        return res

    def process(self, products, ppg=20, ppr=4):
        """Compute products positions on the grid"""
        minpos = 0
        index = 0
        maxy = 0
        rec = 0
        for pdct in products:
            rec = min(max(pdct.website_size_x, 1), ppr)
            res = min(max(pdct.website_size_y, 1), ppr)
            if index >= ppg:
                rec = res = 1
            pos = minpos
            while not self._check_place(pos % ppr, pos // ppr, rec, res, ppr):
                pos += 1
            if index >= ppg and ((pos + 1.0) // ppr) > maxy:
                break
            if rec == 1 and res == 1:
                minpos = pos // ppr
            for y2 in range(res):
                for x2 in range(rec):
                    self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False
            self.table[pos // ppr][pos % ppr] = {
                'product': pdct, 'x': rec, 'y': res,
                'ribbon': pdct._get_website_ribbon(),
            }
            if index <= ppg:
                maxy = max(maxy, res + (pos // ppr))
            index += 1
        rows = sorted(self.table.items())
        rows = [r[1] for r in rows]
        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            rec += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]
        return rows


class ThemeCoffeeMenu(http.Controller):
    """ Controller for rendering datas to menu page """

    def _get_search_order(self, post):
        """ OrderBy will be parsed in orm and so no direct sql injection id is
                    added to be sure that order is a unique sort key
        """
        order = post.get('order') or 'website_sequence ASC'
        return 'is_published desc, %s, id desc' % order

    def _get_search_domain(self, search, category, attrib_values,
                           search_in_description=True):
        """Function for getting search domain"""
        domains = [request.website.sale_product_domain()]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('product_variant_ids.default_code', 'ilike', srch)]
                ]
                if search_in_description:
                    subdomains.append([('website_description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))
        if category:
            domains.append([('public_categ_ids', 'child_of', int(category))])
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domains.append(
                        [('attribute_line_ids.value_ids', 'in', ids)])
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domains.append([('attribute_line_ids.value_ids', 'in', ids)])
        return expression.AND(domains)

    def sitemap_shop(env, rule, qs):
        """Sitemap for shop"""
        if not qs or qs.lower() in '/menu':
            yield {'loc': '/menu'}
        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/menu/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/menu/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def _get_search_options(
            self, category=None, attrib_values=None, pricelist=None, **post):
        """Function for returning search options"""
        return {
            'displayDescription': True,
            'displayDetail': True,
            'displayExtraDetail': True,
            'displayExtraLink': True,
            'displayImage': True,
            'allowFuzzy': not post.get('noFuzzy'),
            'category': str(category.id) if category else None,
            'attrib_values': attrib_values,
            'display_currency': pricelist.currency_id,
        }

    def _shop_lookup_products(self, attrib_set, options, post, search,
                              website):
        """ No limit because attributes are obtained from complete
            product list"""
        product_count, details, fuzzy_search_term = website._search_with_fuzzy(
            "products_only", search, limit=None,
            order=self._get_search_order(post), options=options
        )
        search_result = details[0].get(
            'results', request.env['product.template']
        ).with_context(bin_size=True)
        if attrib_set:
            attribute_values = request.env['product.attribute.value'].browse(
                attrib_set)
            values_per_attribute = defaultdict(
                lambda: request.env['product.attribute.value'])
            multi_value_attribute = False
            for value in attribute_values:
                values_per_attribute[value.attribute_id] |= value
                if len(values_per_attribute[value.attribute_id]) > 1:
                    multi_value_attribute = True

            def filter_template(template, attribute_values_list):
                """Transform product.attribute.value to product. template.
                attribute.value """
                attribute_value_to_ptav = dict()
                for ptav in template.attribute_line_ids.product_template_value_ids:
                    attribute_value_to_ptav[
                        ptav.product_attribute_value_id] = ptav.id
                possible_combinations = False
                for attribute_values in attribute_values_list:
                    ptavs = request.env[
                        'product.template.attribute.value'].browse(
                        [attribute_value_to_ptav[val]
                         for val in attribute_values
                         if val in attribute_value_to_ptav]
                    )
                    if len(ptavs) < len(attribute_values):
                        continue
                    if len(ptavs) == len(template.attribute_line_ids):
                        if template._is_combination_possible(ptavs):
                            return True
                    elif len(ptavs) < len(template.attribute_line_ids):
                        if len(attribute_values_list) == 1:
                            if any(template._get_possible_combinations(
                                    necessary_values=ptavs)):
                                return True
                        if not possible_combinations:
                            possible_combinations = template._get_possible_combinations()
                        if any(len(ptavs & combination) == len(ptavs)
                               for combination in possible_combinations):
                            return True
                return False

            possible_attrib_values_list = (
                [attribute_values]
                if not multi_value_attribute
                else [
                    request.env['product.attribute.value'].browse(
                        [v.id for v in values])
                    for values in
                    cartesian_product(*values_per_attribute.values())
                ]
            )
            search_result = search_result.filtered(
                lambda tmpl: filter_template(tmpl, possible_attrib_values_list)
            )
        return fuzzy_search_term, product_count, search_result

    def _menu_get_query_url_kwargs(self, category, search, attrib=None,
                                   order=None):
        """Function for returning category, search, order and attribute"""
        return {
            'category': category,
            'search': search,
            'attrib': attrib,
            'order': order,
        }

    def _get_additional_shop_values(self, values):
        """ Hook to update values used for rendering
        website_sale.products template """
        return {}

    @http.route([
        '/menu',
        '/menu/page/<int:page>',
        '/menu/category/<model("product.public.category"):category>',
        '/menu/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def menu_page(self, page=0, category=None, search='',
                  min_price=0.0, max_price=0.0, ppg=False, **post):
        """Get menu page """
        add_qty = int(post.get('add_qty', 1))
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
        attrib_values = [[int(x) for x in v.split("-")]
                         for v in attrib_list if v
                         ]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        keep = QueryURL('/menu', **self._menu_get_query_url_kwargs(
            category and int(category), search, min_price, max_price, **post))
        now = datetime.timestamp(datetime.now())
        pricelist = request.env['product.pricelist'].browse(
            request.session.get('website_sale_current_pl'))
        if not pricelist or request.session.get('website_sale_pricelist_time',
                                                0) < now - 60 * 60:
            pricelist = website.get_current_pricelist()
            request.session['website_sale_pricelist_time'] = now
            request.session['website_sale_current_pl'] = pricelist.id
        request.context = dict(request.context, pricelist=pricelist.id,
                               partner=request.env.user.partner_id)
        url = "/menu"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list
        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            pricelist=pricelist,
            **post
        )
        fuzzy_search_term, product_count, search_product = \
            self._shop_lookup_products(attrib_set, options, post,
                                       search, website)
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
            url = "/menu/category/%s" % slug(category)
        pager = website.pager(url=url, total=product_count, page=page,
                              step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]
        ProductAttribute = request.env['product.attribute']
        if products:
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
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_product': search_product,
            'search_count': product_count,
            'bins': lazy(
                lambda: TableComputeCoffee().process(products, ppg, ppr)),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'products_prices': products_prices,
            'get_product_prices': lambda product: lazy(
                lambda: products_prices[product.id]
            ),
            'float_round': tools.float_round,
        }
        if category:
            values['main_object'] = category
        values.update(self._get_additional_shop_values(values))
        return request.render("theme_coffee_shop.coffee_menu", values)
