# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
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
###################################################################################

from werkzeug.exceptions import NotFound
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo import http
from ast import literal_eval
from odoo.http import request
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo.osv import expression



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

    def reset_domain(self, search, categories, available_products, attrib_values, search_in_description=True):
        '''
        Function returns a domain consist of filter conditions
        :param search: search variable
        :param categories: list of category available
        :param available_products: list of available product ids from product.template
        :param attrib_values:product attiribute values
        :param search_in_description: boolean filed showing there is search variable exist or not'''

        domains = [request.website.sale_product_domain()]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('product_variant_ids.default_code', 'ilike', srch)]
                ]
                if search_in_description:
                    subdomains.append([('description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))
        if available_products:
            domains.append([('id', 'in', available_products.ids)])
        if categories:
            domains.append([('public_categ_ids', 'child_of', categories.ids)])
        if attrib_values:
            print("hello world....")
            # attrib = None
            # ids = []
            # print("hello...", ids)
            # for value in attrib_values:
            #     if not attrib:
            #         attrib = value[0]
            #         ids.append(value[1])
            #     elif value[0] == attrib:
            #         ids.append(value[1])
            #     else:
            #         domains.append([('attribute_line_ids.value_ids', 'in', ids)])
            #         attrib = value[0]
            #         ids = [value[1]]
            # if attrib:
            #     domains.append([('attribute_line_ids.value_ids', 'in', ids)])

        return expression.AND(domains)

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        ''''Override shop function.'''
        available_categ =  available_products = ''
        user = request.env['res.users'].sudo().search([('id', '=', request.env.user.id)])
        if not user:
            mode = request.env['ir.config_parameter'].sudo().get_param('filter_mode')
            products = literal_eval(request.env['ir.config_parameter'].sudo().get_param('website_product_visibility.available_product_ids', 'False'))
            if mode == 'product_only':
                available_products = request.env['product.template'].search([('id', 'in', products)])
            cat = literal_eval(request.env['ir.config_parameter'].sudo().get_param('website_product_visibility.available_cat_ids', 'False'))
            available_categ = request.env['product.public.category'].search([('id', 'in', cat)])
        else:
            partner = request.env['res.partner'].sudo().search([('id', '=', user.partner_id.id)])
            mode = partner.filter_mode
            if mode == 'product_only':
                available_products = self.availavle_products()
            available_categ = partner.website_available_cat_ids

        Category_avail = []
        Category = request.env['product.public.category']

        for ids in available_categ:
            if not ids.parent_id.id in available_categ.ids:
                Category_avail.append(ids.id)
        categ = request.env['product.public.category'].search([('id', 'in', Category_avail)])
        if mode == 'product_only':
            categ = Category.search([('parent_id', '=', False), ('product_tmpl_ids', 'in', available_products.ids)])

        # supering shop***

        if not available_categ and not available_products:
            return super(ProductVisibilityCon, self).shop(page, category, search, ppg, **post)
        add_qty = int(post.get('add_qty', 1))

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
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        domain = self._get_search_domain(search, category, attrib_values)
        Product = request.env['product.template'].with_context(bin_size=True)
        if available_products:
            domain_pro = self.reset_domain(search, category, available_products, attrib_values)
            Product = Product.search(domain_pro)
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list,
                        order=post.get('order'))
        pricelist_context, pricelist = self._get_pricelist_context()
        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)
        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list
        if not category:
            domain = self.reset_domain(search, available_categ, available_products, attrib_values)
        search_product = Product.search(domain)
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False), ('product_tmpl_ids', 'in', search_product.ids)] + website_domain
        if search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = available_categ
        if category:
            url = "/shop/category/%s" % slug(category)
        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))
        if not category:
            if available_products:
                products = Product.search(domain_pro, limit=ppg, offset=pager['offset'],
                                          order=self._get_search_order(post))
            else:
                products = Product.search(domain, limit=ppg, offset=pager['offset'],
                                          order=self._get_search_order(post))
        else:
            if available_products:
                products = Product.search(domain_pro, limit=ppg, offset=pager['offset'],
                                          order=self._get_search_order(post))
            else:
                products = Product.search(domain, limit=ppg, offset=pager['offset'],
                                          order=self._get_search_order(post))
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

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
            'categories': categ,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': categ.ids,
            'layout_mode': layout_mode,
        }

        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)

    def availavle_products(self):
        ''''Returns the available product (product.template) ids'''
        user = request.env['res.users'].sudo().search([('id', '=', request.env.user.id)])
        partner = request.env['res.partner'].sudo().search([('id', '=', user.partner_id.id)])
        return partner.website_available_product_ids

    # --------------------------------------------------------------------------
    # Products Search Bar
    # --------------------------------------------------------------------------

    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        """
        Returns list of products according to the term and product options

        Params:
            term (str): search term written by the user
            options (dict)
                - 'limit' (int), default to 5: number of products to consider
                - 'display_description' (bool), default to True
                - 'display_price' (bool), default to True
                - 'order' (str)
                - 'max_nb_chars' (int): max number of characters for the
                                        description if returned

        Returns:
            dict (or False if no result)
                - 'products' (list): products (only their needed field values)
                        note: the prices will be strings properly formatted and
                        already containing the currency
                - 'products_count' (int): the number of products in the database
                        that matched the search query
        """

        user = request.env['res.users'].sudo().search([('id', '=', request.env.user.id)])
        available_categ = available_products = ''
        if not user:
            mode = request.env['ir.config_parameter'].sudo().get_param('filter_mode')
            products = literal_eval(
                request.env['ir.config_parameter'].sudo().get_param('website_product_visibility.available_product_ids',
                                                                    'False'))
            if mode == 'product_only':
                available_products = request.env['product.template'].search([('id', 'in', products)])
            cat = literal_eval(
                request.env['ir.config_parameter'].sudo().get_param('website_product_visibility.available_cat_ids',
                                                                    'False'))
            available_categ = request.env['product.public.category'].search([('id', 'in', cat)])
        else:
            partner = request.env['res.partner'].sudo().search([('id', '=', user.partner_id.id)])
            mode = partner.filter_mode
            if mode != 'categ_only':
                available_products = self.availavle_products()
            available_categ = partner.website_available_cat_ids
        ProductTemplate = request.env['product.template']
        display_description = options.get('display_description', True)
        display_price = options.get('display_price', True)
        order = self._get_search_order(options)
        max_nb_chars = options.get('max_nb_chars', 999)
        category = options.get('category')
        attrib_values = options.get('attrib_values')

        if not available_products and not available_categ:
            domain = self._get_search_domain(term, category, attrib_values, display_description)
        else:
            domain = self.reset_domain(term,available_categ, available_products, attrib_values,display_description)
        products = ProductTemplate.search(
            domain,
            limit=min(20, options.get('limit', 5)),
            order=order
        )
        fields = ['id', 'name', 'website_url']
        if display_description:
            fields.append('description_sale')

        res = {
            'products': products.read(fields),
            'products_count': ProductTemplate.search_count(domain),
        }

        if display_description:
            for res_product in res['products']:
                desc = res_product['description_sale']
                if desc and len(desc) > max_nb_chars:
                    res_product['description_sale'] = "%s..." % desc[:(max_nb_chars - 3)]

        if display_price:
            FieldMonetary = request.env['ir.qweb.field.monetary']
            monetary_options = {
                'display_currency': request.website.get_current_pricelist().currency_id,
            }
            for res_product, product in zip(res['products'], products):
                combination_info = product._get_combination_info(only_template=True)
                res_product.update(combination_info)
                res_product['list_price'] = FieldMonetary.value_to_html(res_product['list_price'], monetary_options)
                res_product['price'] = FieldMonetary.value_to_html(res_product['price'], monetary_options)

        return res
