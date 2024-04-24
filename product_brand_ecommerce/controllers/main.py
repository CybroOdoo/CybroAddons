# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok (<https://www.cybrosys.com>)
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
import logging
from datetime import datetime
from werkzeug.exceptions import NotFound
from odoo import fields, http, tools
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.tools import lazy

_logger = logging.getLogger(__name__)


class TableCompute(object):
    """
    Class for computing the arrangement of products on a grid.
    """
    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey, ppr):
        """
        Check if a specified rectangular area is available in the table.

        Parameters:
            - posx (int): The starting x-coordinate of the area.
            - posy (int): The starting y-coordinate of the area.
            - sizex (int): The width of the area.
            - sizey (int): The height of the area.
            - ppr (int): Maximum allowed x-coordinate in the table.

        Returns:
            bool: True if the area is available, False otherwise.

        The function iterates over the specified area and checks if each cell is
        within the bounds of the table and if the cell is unoccupied. It returns
        True if the entire area is available; otherwise, it returns False.
        """
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= ppr:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(ppr):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=20, ppr=4):
        """
        Arrange a list of products on a grid and format the result for HTML
        representation.

        Parameters:
            - products (list): A list of product objects to be arranged on the
            grid.
            - ppg (int): The maximum number of products per grid page
            (default is 20).
            - ppr (int): The maximum number of products per row in the grid
            (default is 4).

        Returns:
            list: A formatted representation of the arranged products suitable
             for HTML rendering.The result is a list of rows, where each row is
             a list of dictionaries representing products and their positions on
             the grid.

        The function iterates over the list of products and computes their
        positions on the grid.It uses a heuristic algorithm to determine the
        position of each product, taking into account the dimensions of the
        products, the maximum products per page, and the maximum products per
        row.The result is formatted as a list of rows, each containing
        dictionaries representing the products and their positions on the grid.
        """
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        x = 0
        for p in products:
            x = min(max(p.website_size_x, 1), ppr)
            y = min(max(p.website_size_y, 1), ppr)
            if index >= ppg:
                x = y = 1
            pos = minpos
            while not self._check_place(pos % ppr, pos // ppr, x, y, ppr):
                pos += 1
            # if 21st products (index 20) and the last line is full (ppr products in it), break
            # (pos + 1.0) / ppr is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) // ppr) > maxy:
                break
            if x == 1 and y == 1:  # simple heuristic for CPU optimization
                minpos = pos // ppr

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False
            self.table[pos // ppr][pos % ppr] = {
                'product': p, 'x': x, 'y': y,
                'ribbon': p.sudo().website_ribbon_id,
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos // ppr))
            index += 1
        # Format table according to HTML needs
        rows = sorted(self.table.items())
        rows = [r[1] for r in rows]
        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            x += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]
        return rows


class WebsiteSale(payment_portal.PaymentPortal):

    def sitemap_shop(env, rule, qs):
        """
        Generate sitemap entries for the Odoo eCommerce shop.
        """
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
        '/shop/category/<model("product.public.category"):category>/'
        'page/<int:page>',
        '''/shop/brand/<model("product.brand"):brand>''',
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0,
             ppg=False, brand=None, **post):
        """
        Render the eCommerce shop page.

        This function handles the rendering of the eCommerce shop page based on
        the provided parameters.
        It retrieves and filters products, applies pricing rules, and prepares
        the data for rendering.
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
        compute_brand = brand
        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category
        product_brand = request.env['product.brand']
        if not brand:
            brand = product_brand
        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        request_args = request.httprequest.args
        attrib_list = request_args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if
                         v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        filter_by_tags_enabled = website.is_view_active(
            'website_sale.filter_products_tags')
        if filter_by_tags_enabled:
            tags = request_args.getlist('tags')
            # Allow only numeric tag values to avoid internal error.
            if tags and all(tag.isnumeric() for tag in tags):
                post['tags'] = tags
                tags = {int(tag) for tag in tags}
            else:
                post['tags'] = None
                tags = {}

        keep = QueryURL('/shop', **self._shop_get_query_url_kwargs(
            category and int(category), search, min_price, max_price, **post))

        now = datetime.timestamp(datetime.now())
        pricelist = website.pricelist_id
        if 'website_sale_pricelist_time' in request.session:
            # Check if we need to refresh the cached pricelist
            pricelist_save_time = request.session['website_sale_pricelist_time']
            if pricelist_save_time < now - 60 * 60:
                request.session.pop('website_sale_current_pl', None)
                website.invalidate_recordset(['pricelist_id'])
                pricelist = website.pricelist_id
                request.session['website_sale_pricelist_time'] = now
                request.session['website_sale_current_pl'] = pricelist.id
        else:
            request.session['website_sale_pricelist_time'] = now
            request.session['website_sale_current_pl'] = pricelist.id

        filter_by_price_enabled = website.is_view_active(
            'website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = website.company_id.currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency, website.currency_id,
                request.website.company_id,
                fields.Date.today())
        else:
            conversion_rate = 1

        url = '/shop'
        if search:
            post['search'] = search
        if attrib_list:
            post['attrib'] = attrib_list

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
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
            domain = self._get_shop_domain(search, category, attrib_values)

            # This is ~4 times more efficient than a search for the cheapest and most expensive products
            query = Product._where_calc(domain)
            Product._apply_ir_rules(query, 'read')
            from_clause, where_clause, where_params = query.get_sql()
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

        if filter_by_tags_enabled:
            if (
                    search_product.product_tag_ids
                    or search_product.product_variant_ids.additional_product_tag_ids
            ):
                ProductTag = request.env['product.tag']
                all_tags = ProductTag.search(
                    [('product_ids.is_published', '=', True),
                     ('visible_on_ecommerce', '=', True)]
                    + website_domain
                )
            else:
                all_tags = []
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [(
                 'product_tmpl_ids', 'in', search_product.ids)] + website_domain
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

        # Try to fetch geoip based fpos or fallback on partner one
        fiscal_position_sudo = website.fiscal_position_id.sudo()
        products_prices = lazy(
            lambda: products._get_sales_prices(pricelist, fiscal_position_sudo))
        products_prices_brand = lazy(
            lambda: search_product._get_sales_prices(pricelist, fiscal_position_sudo))
        product_brand = request.env['product.brand'].search([])
        if compute_brand:
            products_brand = request.env['product.template'].search(
                ['&', '&', ('brand_id', '=', brand.id), ('sale_ok', '=', True),
                 ('is_published', '=', True)])
            product_brand_count = len(products_brand)
            pager_brand = request.website.pager(url=url,
                                                total=product_brand_count,
                                                page=page, step=ppg, scope=7,
                                                url_args=post)
            values = {
                'search': fuzzy_search_term or search,
                'original_search': fuzzy_search_term and search,
                'order': post.get('order', ''),
                'category': category,
                'brand': brand,
                'attrib_values': attrib_values,
                'attrib_set': attrib_set,
                'pager': pager_brand,
                'pricelist': pricelist,
                'fiscal_position': fiscal_position_sudo,
                'add_qty': add_qty,
                'products': products_brand,
                'search_product': search_product,
                'search_count': product_brand_count,  # common for all searchbox
                'bins': lazy(
                    lambda: TableCompute().process(products_brand, ppg, ppr)),
                'ppg': ppg,
                'ppr': ppr,
                'categories': categs,
                'attributes': attributes,
                'keep': keep,
                'search_categories_ids': search_categories.ids,
                'layout_mode': layout_mode,
                'brands':product_brand,
                'products_prices': products_prices,
                'get_product_prices': lambda product: lazy(
                    lambda: products_prices_brand[product.id]),
                'float_round': tools.float_round,
            }

            if filter_by_price_enabled:
                values['min_price'] = min_price or available_min_price
                values['max_price'] = max_price or available_max_price
                values['available_min_price'] = tools.float_round(
                    available_min_price,
                    2)
                values['available_max_price'] = tools.float_round(
                    available_max_price,
                    2)
            if filter_by_tags_enabled:
                values.update({'all_tags': all_tags, 'tags': tags})
            if category:
                values['main_object'] = category
            values.update(self._get_additional_shop_values(values))
            return request.render("website_sale.products", values)
        else:
            values = {
                'brand': brand,
                'search': search,
                'category': category,
                'original_search': fuzzy_search_term and search,
                'order': post.get('order', ''),
                'attrib_values': attrib_values,
                'attrib_set': attrib_set,
                'pager': pager,
                'pricelist': pricelist,
                'add_qty': add_qty,
                'products': products,
                'search_count': product_count,  # common for all searchbox
                'bins': lazy(
                    lambda: TableCompute().process(products, ppg, ppr)),
                'ppg': ppg,
                'ppr': ppr,
                'categories': categs,
                'attributes': attributes,
                'keep': keep,
                'search_categories_ids': search_categories.ids,
                'layout_mode': layout_mode,
                'brands': product_brand,
                'products_prices': products_prices,
                'get_product_prices': lambda product: lazy(
                    lambda: products_prices[product.id]),
                'float_round': tools.float_round,
            }
            if filter_by_price_enabled:
                values['min_price'] = min_price or available_min_price
                values['max_price'] = max_price or available_max_price
                values['available_min_price'] = tools.float_round(
                    available_min_price,
                    2)
                values['available_max_price'] = tools.float_round(
                    available_max_price,
                    2)
            if filter_by_tags_enabled:
                values.update({'all_tags': all_tags, 'tags': tags})
            if category:
                values['main_object'] = category
            values.update(self._get_additional_shop_values(values))
            return request.render("website_sale.products", values)
