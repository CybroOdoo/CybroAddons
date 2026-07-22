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
import logging
import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
except ImportError:
    from odoo.addons.website_sale.controllers.website_sale import WebsiteSale, TableCompute

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

    # ── Shared helper ────────────────────────────────────────────────────────

    def _velox_get_products_prices(self, products, pricelist, fiscal_position):
        """
        Build a products_prices dict compatible with Odoo 17's shop template.

        Odoo 17's _get_sales_prices requires TWO arguments:
            products._get_sales_prices(pricelist, fiscal_position)

        The pricelist and fiscal_position are extracted from the parent's
        qcontext (the parent shop() puts them there at lines 491-492 of the
        core controller).

        On failure we return a minimal safe dict so the QWeb template never
        throws a KeyError.
        """
        if not products:
            return {}
        if isinstance(products, list):
            products = request.env['product.template'].sudo().browse(products)
        # ── Strategy 1: Odoo 17 two-arg signature ─────────────────────────
        try:
            res = products._get_sales_prices(pricelist, fiscal_position)
            if isinstance(res, dict):
                return res
        except Exception:
            pass
        # ── Strategy 2: one-arg fallback (some older 17.x builds) ─────────
        try:
            res = products._get_sales_prices(pricelist)
            if isinstance(res, dict):
                return res
        except Exception:
            pass
        # ── Safe fallback: minimal dict so the template never KeyErrors ────
        _logger.warning("Velox: _get_sales_prices unavailable; using price fallback.")
        fallback = {}
        for p in products:
            try:
                price = p.lst_price
            except Exception:
                price = 0.0
            fallback[p.id] = {
                'price': price,
                'list_price': price,
                'price_reduce': price,
                'has_discounted_price': False,
                'currency': request.website.currency_id,
            }
        return fallback

    def _velox_build_filtered_response(
            self, result, filtered_products, url, page, post
    ):
        """
        Replace the standard shop qcontext with a filtered product set.

        Key Odoo 17 requirements addressed:
          • _get_sales_prices(pricelist, fiscal_position) — two args,
            both taken from the parent's qcontext where they are always set.
          • 'get_product_prices' lambda must be updated alongside
            'products_prices', otherwise it still references the old
            (unfiltered) prices and the template raises KeyError.
        """
        if not hasattr(result, 'qcontext') or not result.qcontext:
            return result
        # Ensure filtered_products is a proper recordset
        if isinstance(filtered_products, list):
            filtered_products = (
                request.env['product.template'].sudo().browse(filtered_products)
            )
        product_count = len(filtered_products)
        ppg = result.qcontext.get('ppg') or 20
        ppr = result.qcontext.get('ppr') or 4
        website = request.env['website'].get_current_website()
        pager = website.pager(
            url=url,
            total=product_count,
            page=page,
            step=ppg,
            scope=5,
            url_args=post,
        )
        offset = pager['offset']
        products = filtered_products[offset: offset + ppg]
        # ── Odoo 17: get pricelist + fiscal_position from parent qcontext ──
        # The parent shop() always sets these (core controller lines 491-492).
        pricelist = (
                result.qcontext.get('pricelist')
                or request.website.pricelist_id
        )
        fiscal_position = (
                result.qcontext.get('fiscal_position')
                or request.website.fiscal_position_id.sudo()
        )
        # Compute prices lazily for the current page only (mirrors core).
        products_prices = lazy(
            lambda: self._velox_get_products_prices(
                products, pricelist, fiscal_position
            )
        )
        # ── IMPORTANT: update BOTH products_prices AND get_product_prices ──
        # The parent sets 'get_product_prices' as a closure over its own
        # products_prices.  If we replace products_prices but leave
        # get_product_prices pointing at the old one, the template gets
        # KeyError for any product that wasn't in the original page.
        result.qcontext.update({
            'search_product': filtered_products,
            'search_count': product_count,
            'pager': pager,
            'products': products,
            'products_prices': products_prices,
            'get_product_prices': (
                lambda product, pp=products_prices:
                lazy(lambda: pp[product.id])
            ),
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
        })
        # Update attributes sidebar for the filtered set
        if filtered_products:
            try:
                fp_ids = filtered_products.ids  # evaluate once outside the lambda
                result.qcontext['attributes'] = lazy(
                    lambda: request.env['product.attribute'].search([
                        ('product_tmpl_ids', 'in', fp_ids),
                    ])
                )
            except Exception:
                pass
        # Update keep/QueryString path so facet links stay on this URL
        if 'keep' in result.qcontext:
            try:
                result.qcontext['keep'].path = url
            except (AttributeError, TypeError):
                pass
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
        try:
            groups = request.env['sale.order.line'].sudo().read_group(
                domain=[
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', month_start),
                    ('product_id.active', '=', True),
                ],
                fields=['product_id', 'product_uom_qty:sum'],
                groupby=['product_id'],
                orderby='product_uom_qty desc',
                limit=limit,
            )
        except Exception:
            _logger.warning("Velox: Could not query trending products.")
            return []
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
    # ── Ribbon helpers ───────────────────────────────────────────────────────

    def _velox_get_sale_ribbon(self):
        """
        Identify the 'Sale' ribbon record.
        Checks both likely XMLIDs and falls back to a name/HTML search.
        """
        for xmlid in ('website_sale.sale_ribbon', 'website_sale.ribbon_sale'):
            try:
                ribbon = request.env.ref(xmlid, raise_if_not_found=False)
                if ribbon:
                    return ribbon
            except Exception:
                pass
        return request.env['product.ribbon'].sudo().search(
            [('html', 'ilike', 'sale')], limit=1
        )

    def _velox_get_new_ribbon(self):
        """
        Identify the 'New' ribbon record.
        Checks both likely XMLIDs and falls back to a name/HTML search.
        """
        for xmlid in ('website_sale.new_ribbon', 'website_sale.ribbon_new'):
            try:
                ribbon = request.env.ref(xmlid, raise_if_not_found=False)
                if ribbon:
                    return ribbon
            except Exception:
                pass
        # Fallback: search by HTML content
        return request.env['product.ribbon'].sudo().search(
            [('html', 'ilike', 'new')], limit=1
        )

    # ── /shop/sale ───────────────────────────────────────────────────────────
    @http.route(
        ['/shop/sale', '/shop/sale/page/<int:page>'],
        type='http', auth='public', website=True,
        sitemap=True,
    )
    def shop_sale(
            self, page=0, category=None, search='',
            min_price=0.0, max_price=0.0, ppg=False, **post
    ):
        try:
            result = super().shop(
                page=page, category=category, search=search,
                min_price=min_price, max_price=max_price, ppg=ppg, **post
            )
        except Exception as e:
            _logger.exception(
                "Velox: Error calling super().shop() for /shop/sale: %s", e
            )
            return request.redirect('/shop')

        if not hasattr(result, 'qcontext') or not result.qcontext:
            return result

        # ── Direct DB query for Sale ribbon products ──────────────────────
        try:
            sale_ribbon = self._velox_get_sale_ribbon()
            if sale_ribbon:
                filtered = request.env['product.template'].sudo().search([
                    ('is_published', '=', True),
                    ('website_ribbon_id', '=', sale_ribbon.id),
                ])
            else:
                # No ribbon found — fall back to all published products
                _logger.warning(
                    "Velox: No Sale ribbon found; showing unfiltered shop"
                )
                return result

            return self._velox_build_filtered_response(
                result, filtered, '/shop/sale', page, post
            )
        except Exception:
            _logger.exception("Velox: Error filtering /shop/sale")
            return result

    # ── /shop/new-release ────────────────────────────────────────────────────

    @http.route(
        ['/shop/new-release', '/shop/new-release/page/<int:page>'],
        type='http', auth='public', website=True,
        sitemap=True,
    )
    def shop_new_release(
            self, page=0, category=None, search='',
            min_price=0.0, max_price=0.0, ppg=False, **post
    ):
        try:
            result = super().shop(
                page=page, category=category, search=search,
                min_price=min_price, max_price=max_price, ppg=ppg, **post
            )
        except Exception as e:
            _logger.exception(
                "Velox: Error calling super().shop() for /shop/new-release: %s", e
            )
            return request.redirect('/shop')
        if not hasattr(result, 'qcontext') or not result.qcontext:
            return result
        # ── Direct DB query for New ribbon products ───────────────────────
        try:
            new_ribbon = self._velox_get_new_ribbon()
            if new_ribbon:
                filtered = request.env['product.template'].sudo().search([
                    ('is_published', '=', True),
                    ('website_ribbon_id', '=', new_ribbon.id),
                ])
            else:
                _logger.warning(
                    "Velox: No New ribbon found; showing unfiltered shop"
                )
                return result

            return self._velox_build_filtered_response(
                result, filtered, '/shop/new-release', page, post
            )
        except Exception:
            _logger.exception("Velox: Error filtering /shop/new-release")
            return result

    # ── /shop/trending ───────────────────────────────────────────────────────

    @http.route(
        ['/shop/trending', '/shop/trending/page/<int:page>'],
        type='http', auth='public', website=True,
        sitemap=True,
    )
    def shop_trending(
            self, page=0, category=None, search='',
            min_price=0.0, max_price=0.0, ppg=False, **post
    ):
        try:
            result = super().shop(
                page=page, category=category, search=search,
                min_price=min_price, max_price=max_price, ppg=ppg, **post
            )
        except Exception as e:
            _logger.exception(
                "Velox: Error calling super().shop() for /shop/trending: %s", e
            )
            return request.redirect('/shop')
        if not hasattr(result, 'qcontext') or not result.qcontext:
            return result
        try:
            all_published = result.qcontext.get('search_product')
            if not all_published:
                return result
            trending_ids = self._velox_trending_template_ids(min_qty=5, limit=500)
            if trending_ids:
                id_set = set(all_published.ids)
                ordered_ids = [tid for tid in trending_ids if tid in id_set]
                filtered = (
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
        except Exception:
            _logger.exception("Velox: Error filtering /shop/trending")
            return result
