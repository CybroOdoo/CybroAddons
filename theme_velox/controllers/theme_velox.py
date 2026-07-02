# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
import datetime
from odoo import http
from odoo.http import request

try:
    from odoo.addons.website_sale.controllers.main import WebsiteSale
    from odoo.addons.website_sale.controllers.main import TableCompute
except ImportError:
    from odoo.addons.website_sale.controllers.website_sale import WebsiteSale
    from odoo.addons.website_sale.controllers.website_sale import TableCompute
from odoo.tools import lazy


class VeloxWebsiteSale(WebsiteSale):
    """
    Extends the default eCommerce controller with three extra shop routes:
      /shop/sale          — products carrying the "Sale" ribbon
      /shop/new-release   — products carrying the "New" ribbon
      /shop/trending      — products ranked by units sold this month
    All three reuse the standard /shop QWeb template but inject a filtered +
    re-paginated product list into qcontext, keeping facets, sorting and
    pager working exactly like the normal shop.
    """

    def _velox_build_filtered_response(
        self, result, filtered_products, url, page, post
    ):
        """
        Helper to update qcontext with filtered product lists and pagers
        for custom shop routes.
        """
        if not result.qcontext:
            return result

        product_count = len(filtered_products)
        ppg = result.qcontext.get('ppg') or 20
        ppr = result.qcontext.get('ppr') or 4
        website = request.env['website'].get_current_website()
        pager = website.pager(
            url=url,
            total=product_count,
            page=page,
            step=ppg,
            url_args=post,
        )
        offset = pager['offset']
        products = filtered_products[offset: offset + ppg]
        products_prices = lazy(lambda: products._get_sales_prices(website))
        
        result.qcontext.update({
            'search_product': filtered_products,
            'search_count':   product_count,
            'pager':          pager,
            'products':       products,
            'products_prices': products_prices,
            'get_product_prices': lambda product: lazy(lambda: products_prices[product.id]),
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
        })

        if filtered_products:
             result.qcontext['attributes'] = lazy(
                lambda: request.env['product.attribute'].search([
                    ('product_tmpl_ids', 'in', filtered_products.ids),
                    ('visibility', '=', 'visible'),
                ])
            )

        if 'keep' in result.qcontext and hasattr(result.qcontext['keep'], 'path'):
            result.qcontext['keep'].path = url
            
        return result

    def _velox_trending_template_ids(self, min_qty=5, limit=200):
        """
        Returns a list of product.template IDs ordered by total units sold
        in the current calendar month (today back to the 1st).
        Only considers confirmed/done orders and active products.
        """
        month_start = (
            datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
        )
        groups = request.env['sale.order.line'].sudo().read_group(
            domain=[
                ('order_id.state',       'in', ['sale', 'done']),
                ('order_id.date_order',  '>=', month_start),
                ('product_id.active',    '=',  True),
            ],
            fields=['product_id', 'product_uom_qty:sum'],
            groupby=['product_id'],
            orderby='product_uom_qty desc',
            limit=limit,
        )
        variant_ids = [
            g['product_id'][0]
            for g in groups
            if g.get('product_id') and g.get('product_uom_qty', 0) > min_qty
        ]
        if not variant_ids:
            return []

        variants = request.env['product.product'].sudo().browse(variant_ids)
        seen, tmpl_ids = set(), []
        for v in variants:
            tid = v.product_tmpl_id.id
            if tid not in seen:
                seen.add(tid)
                tmpl_ids.append(tid)
        return tmpl_ids

    @http.route(
        ['/shop/sale', '/shop/sale/page/<int:page>'],
        type='http', auth='public', website=True,
        sitemap=WebsiteSale.sitemap_shop,
    )
    def shop_sale(
        self, page=0, category=None, search='',
        min_price=0.0, max_price=0.0, ppg=False, **post
    ):
        """
        Custom shop route providing products specifically marked with
        a Sale ribbon.
        """
        result = super().shop(
            page=page, category=category, search=search,
            min_price=min_price, max_price=max_price, ppg=ppg, **post
        )
        all_published = result.qcontext.get('search_product')
        if all_published is None:
            return result

        sale_ribbon = request.env.ref(
            'website_sale.sale_ribbon', raise_if_not_found=False
        )

        if sale_ribbon:
            filtered = all_published.filtered(
                lambda p: p.website_ribbon_id.id == sale_ribbon.id
            )
        else:
            filtered = all_published.filtered(lambda p: p.website_ribbon_id)
        
        return self._velox_build_filtered_response(
           result, filtered, '/shop/sale', page, post
        )

    @http.route(
        ['/shop/new-release', '/shop/new-release/page/<int:page>'],
        type='http', auth='public', website=True,
        sitemap=WebsiteSale.sitemap_shop,
    )
    def shop_new_release(
        self, page=0, category=None, search='',
        min_price=0.0, max_price=0.0, ppg=False, **post
    ):
        """
        Custom shop route providing products specifically marked with
        a New ribbon.
        """
        result = super().shop(
            page=page, category=category, search=search,
            min_price=min_price, max_price=max_price, ppg=ppg, **post
        )
        all_published = result.qcontext.get('search_product')
        if all_published is None:
            return result

        new_ribbon = request.env.ref(
            'website_sale.new_ribbon', raise_if_not_found=False
        )

        if new_ribbon:
            filtered = all_published.filtered(
                lambda p: p.website_ribbon_id.id == new_ribbon.id
            )
        else:
            filtered = all_published.filtered(
                lambda p: p.website_ribbon_id
                and 'new' in (p.website_ribbon_id.html or '').lower()
            )   

        return self._velox_build_filtered_response(
            result, filtered, '/shop/new-release', page, post
        )

    @http.route(
        ['/shop/trending', '/shop/trending/page/<int:page>'],
        type='http', auth='public', website=True,
        sitemap=WebsiteSale.sitemap_shop,
    )
    def shop_trending(
        self, page=0, category=None, search='',
        min_price=0.0, max_price=0.0, ppg=False, **post
    ):
        """
        Custom shop route providing products ranked by unit sales
        this month.
        """
        result = super().shop(
            page=page, category=category, search=search,
            min_price=min_price, max_price=max_price, ppg=ppg, **post
        )
        all_published = result.qcontext.get('search_product')
        if all_published is None:
            return result

        trending_ids = self._velox_trending_template_ids(
            min_qty=5, limit=500
        )

        if trending_ids:
            id_set      = set(all_published.ids)
            ordered_ids = [tid for tid in trending_ids if tid in id_set]
            filtered    = (
                request.env['product.template']
                .sudo()
                .browse(ordered_ids)
            )
        else:
            filtered = all_published.sorted(
                key=lambda p: p.create_date, reverse=True
            )

        return self._velox_build_filtered_response(
            result, filtered, '/shop/trending', page, post
        )
