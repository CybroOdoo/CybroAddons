#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    """Inherits WebsiteSale to filter and display sample products in shop."""

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, tags='', **post):
        res = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post,
        )
        shop_type = post.get('type')
        if not shop_type or shop_type != 'sample':
            return res

        if not hasattr(res, 'qcontext'):
            return res

        website = request.env.website
        products = request.env['product.template'].search([
            ('is_sample_product', '=', True),
            ('is_published', '=', True),
        ])
        ppg = res.qcontext.get('ppg') or website.shop_ppg or 21
        ppr = res.qcontext.get('ppr') or website.shop_ppr or 4
        gap = res.qcontext.get('gap') or website.shop_gap or '16px'
        Product = request.env['product.product']
        product_variant_ids = [p._get_first_possible_variant_id() for p in products]
        variants = Product.sudo().browse(vid for vid in product_variant_ids if vid)
        variants.fetch()
        variant_by_id = {v.id: v for v in variants}
        product_variants = dict(
            zip(products, (variant_by_id.get(vid, Product) for vid in product_variant_ids)),
        )
        products_prices = products._get_sales_prices(
            request.pricelist.with_context(**request.env.context),
            request.fiscal_position.with_context(**request.env.context),
            website.with_context(**request.env.context),
        )
        product_query_params = res.qcontext.get('product_query_params') or {}
        previewed_attribute_values = products._get_previewed_attribute_values(product_query_params)
        res.qcontext.update({
            'products': products,
            'product_variants': product_variants,
            'bins': TableCompute().process(products, ppg, ppr),
            'products_prices': products_prices,
            'get_product_prices': lambda product: products_prices.get(
                product.id, {'price_reduce': 0.0, 'raw_pricelist_price': 0.0, 'pricelist_rule_id': False},
            ),
            'previewed_attribute_values': previewed_attribute_values,
            'ppg': ppg,
            'ppr': ppr,
            'gap': gap,
        })
        return request.render(
            "website_sample_product_request.sample_order_template_view",
            res.qcontext,
        )


class CartInherit(Cart):
    """Inherits Cart to update the sample order flag on the cart."""

    @http.route(route='/shop/cart', type='http', auth="public", website=True, sitemap=False)
    def cart(self, id=None, access_token=None, **post):
        """Sets is_sample_order flag on cart based on its order lines."""
        order = request.cart
        if order and order.order_line:
            sample_lines = order.order_line.filtered(
                lambda line: line.product_template_id.is_sample_product,
            )
            order.is_sample_order = bool(len(sample_lines) == len(order.order_line))
        elif order:
            order.is_sample_order = False
        return super().cart(id=id, access_token=access_token, **post)
