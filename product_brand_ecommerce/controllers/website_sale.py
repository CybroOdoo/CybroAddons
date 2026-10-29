# -*- coding: utf-8 -*-
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
import itertools
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.exceptions import NotFound
from odoo import fields
from odoo.fields import Domain
from odoo.http import request, route
from odoo.tools import SQL, float_round, lazy
from odoo.tools.translate import LazyTranslate
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.const import SHOP_PATH
from odoo.addons.website_sale.controllers.main import (
    MAX_EXPANDED_FILTER_SECTIONS,
    TableCompute,
    WebsiteSale,
    _get_category_routes,
)
from odoo.addons.website_sale.models.website import (
    PRICELIST_SESSION_CACHE_KEY,
)
_lt = LazyTranslate(__name__)

class WebsiteSales(WebsiteSale):
    """Extend the website shop controller with product brand filtering."""

    def sitemap_shop(env, _rule, qs):
        """Generate sitemap entries for shop, category, and brand pages."""
        if env.website and env.website.ecommerce_access == "logged_in" and not qs:
            return
        if not qs or qs.lower() in SHOP_PATH:
            yield {"loc": SHOP_PATH}
        Category = env["product.public.category"]
        dom = sitemap_qs2dom(qs, f"{SHOP_PATH}/category", Category._rec_name)
        dom &= env.website.website_domain()
        for category in Category.search(dom):
            loc = category.website_url
            if not qs or qs.lower() in loc:
                yield {"loc": loc}
        Brand = env["product.brand"]
        dom = sitemap_qs2dom(qs, f"{SHOP_PATH}/brand", Brand._rec_name)
        for brand in Brand.search(dom):
            loc = f"{SHOP_PATH}/brand/{env['ir.http']._slug(brand)}"
            if not qs or qs.lower() in loc:
                yield {"loc": loc}

    @route(
        [
            SHOP_PATH,
            f'{SHOP_PATH}/page/<int:page>',
            *_get_category_routes(),
            *_get_category_routes('/page/<int:page>'),
            f'{SHOP_PATH}/brand/<model("product.brand"):brand>',
            f'{SHOP_PATH}/brand/<model("product.brand"):brand>/page/<int:page>',
        ],
        type='http',
        auth='public',
        website=True,
        list_as_website_content=_lt("Shop"),
        sitemap=sitemap_shop,
        handle_params_access_error=lambda e, **_kwargs: NotFound.code,
    )
    def shop(
        self,
        page=0,
        category=None,
        search='',
        min_price=0.0,
        max_price=0.0,
        tags='',
        on_sale=None,
        in_stock=None,
        brand=None,
        **post,
    ):
        """Display the shop page with product brand filtering."""

        not_reload_request = request.httprequest.path != "/shop/reload"
        website = self.env.website
        if not_reload_request and not website.has_ecommerce_access():
            return request.redirect(f"/web/login?redirect={request.httprequest.path}")
        post = {k: v for k, v in post.items() if not k.startswith("_")}
        category = self._validate_and_get_category(category)
        if category:
            path = category.website_url + (f"/page/{page}" if page else "")
            if not_reload_request and path != request.httprequest.path:
                url = urlparse(request.httprequest.url)
                return request.redirect(url._replace(path=path).geturl(), code=301)
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0
        website_domain = website.website_domain()
        ppg = website.shop_ppg or 21
        ppr = website.shop_ppr or 4
        gap = website.shop_gap or "16px"
        attribute_value_params = self._get_attribute_value_params(post)
        if not attribute_value_params and (
            attribute_values := request.httprequest.args.getlist("attribute_values")
        ):
            attribute_value_params = dict([
                pair.split("-") for pair in attribute_values if pair and pair.count("-") == 1
            ])
        attribute_value_dict = self._get_attribute_value_dict(attribute_value_params)
        attribute_value_ids = set(itertools.chain.from_iterable(attribute_value_dict.values()))
        grouped_attributes_values = (
            self
            .env["product.attribute.value"]
            .browse(attribute_value_ids)
            .exists()
            .sorted()
            .grouped("attribute_id")
        )
        if not_reload_request and request.httprequest.args.getlist("attribute_values"):
            redirect_url = self._get_url_with_attribute_values(grouped_attributes_values)
            return request.redirect(redirect_url, code=301)
        if attribute_value_params:
            request.session["attribute_value_params"] = attribute_value_params
        else:
            request.session.pop("attribute_value_params", None)
        filter_by_tags_enabled = website.is_view_active("website_sale.filter_products_tags")
        if filter_by_tags_enabled:
            if tags:
                post["tags"] = tags
                unslug = self.env["ir.http"]._unslug
                tags = {tag_id for tag in tags.split(",") if (tag_id := unslug(tag)[1])}
            else:
                post["tags"] = None
                tags = {}
        if brand:
            url = f"{SHOP_PATH}/brand/{self.env['ir.http']._slug(brand)}"
        else:
            url = category.website_url if category else SHOP_PATH
        keep = QueryURL(
            url,
            **self._shop_get_query_url_kwargs(
                search, min_price, max_price, on_sale=on_sale, in_stock=in_stock, **post
            ),
        )
        now = datetime.timestamp(datetime.now())
        if "website_sale_pricelist_time" in request.session:
            pricelist_save_time = request.session["website_sale_pricelist_time"]
            if pricelist_save_time < now - 60 * 60:
                request.session.pop(PRICELIST_SESSION_CACHE_KEY, None)
                request.session["website_sale_pricelist_time"] = now
        filter_by_price_enabled = website.is_view_active("website_sale.filter_products_price")
        if filter_by_price_enabled:
            company_currency = website.company_id.sudo().currency_id
            conversion_rate = self.env["res.currency"]._get_conversion_rate(
                company_currency, website.currency_id, website.company_id, fields.Date.today()
            )
        else:
            conversion_rate = 1
        if search:
            post["search"] = search
        tax_display = website.show_line_subtotals_tax_selection
        sale_tax = request.fiscal_position.map_tax(website.company_id.sudo().account_sale_tax_id)
        if tax_display == "tax_included" and sale_tax:
            min_price_tax_excluded = sale_tax.with_context(force_price_include=True).compute_all(
                min_price, website.currency_id
            )["total_excluded"]
            max_price_tax_excluded = sale_tax.with_context(force_price_include=True).compute_all(
                max_price, website.currency_id
            )["total_excluded"]
        else:
            min_price_tax_excluded = min_price
            max_price_tax_excluded = max_price
        extra_domain = Domain([])
        if not (category or search):
            extra_domain &= Domain.OR([
                Domain("public_categ_ids", "=", False),
                Domain("public_categ_ids.not_in_shop", "=", False),
            ])
        if brand:
            extra_domain &= Domain("brand_id", "=", brand.id)

        options = self._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            min_price=min_price_tax_excluded,
            max_price=max_price_tax_excluded,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
            extra_domain=extra_domain if extra_domain else None,
            **post,
        )
        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(
            options, post, search, website
        )
        search_term = fuzzy_search_term if fuzzy_search_term else search
        shop_domain = self._get_shop_domain(
            search_term,
            category,
            attribute_value_dict,
            tags=tags if filter_by_tags_enabled else None,
        )
        if brand:
            shop_domain &= Domain("brand_id", "=", brand.id)
        shop_query = request.env["product.template"]._search(shop_domain)
        filters_domain = self._get_shop_domain(search_term, category, attribute_value_dict={})
        if brand:
            filters_domain &= Domain("brand_id", "=", brand.id)
        filters_query = request.env["product.template"]._search(filters_domain)
        if filter_by_price_enabled:
            sql = shop_query.select(
                SQL(
                    "COALESCE(MIN(list_price), 0) * %(conversion_rate)s, COALESCE(MAX(list_price), 0) * %(conversion_rate)s",
                    conversion_rate=conversion_rate,
                )
            )
            available_min_price, available_max_price = self.env.execute_query(sql)[0]
            if tax_display == "tax_included" and sale_tax:
                available_min_price = sale_tax.with_context(force_price_include=False).compute_all(
                    available_min_price, website.currency_id
                )["total_included"]
                available_max_price = sale_tax.with_context(force_price_include=False).compute_all(
                    available_max_price, website.currency_id
                )["total_included"]

            if min_price or max_price:
                if min_price:
                    min_price = (
                        min_price if min_price <= available_max_price else available_min_price
                    )
                    post["min_price"] = min_price
                if max_price:
                    max_price = (
                        max_price if max_price >= available_min_price else available_max_price
                    )
                    post["max_price"] = max_price
        if filter_by_price_enabled and (min_price or max_price):
            price_domain = Domain.AND([
                Domain("list_price", ">=", (min_price or available_min_price) / conversion_rate),
                Domain("list_price", "<=", (max_price or available_max_price) / conversion_rate),
            ])
            filters_query = request.env["product.template"]._search(
                Domain.AND([filters_domain, price_domain])
            )
        on_sale_active = on_sale == "1"
        in_stock_active = in_stock == "1"
        auto_assign_ribbons = self.env["product.ribbon"].sudo().search([("assign", "!=", "manual")])
        ribbon_assign_values = set(auto_assign_ribbons.mapped("assign"))
        on_sale_ids = set()
        sold_out_ids = set()
        if "sale" in ribbon_assign_values:
            sales_prices = search_product._get_sales_prices(
                request.pricelist.with_context(self.env.context),
                request.fiscal_position.with_context(self.env.context),
                website.with_context(self.env.context),
            )
            on_sale_ids = {pid for pid, prices in sales_prices.items() if "base_price" in prices}
        if "out_of_stock" in ribbon_assign_values:
            sold_out_ids = {p.id for p in search_product if p._is_sold_out()}

        show_on_sale_filter = bool(on_sale_ids) or (
            on_sale_active and "sale" in ribbon_assign_values
        )
        show_in_stock_filter = bool(sold_out_ids) or (
            in_stock_active and "out_of_stock" in ribbon_assign_values
        )
        if on_sale_active and "sale" in ribbon_assign_values:
            search_product = search_product.filtered(lambda p: p.id in on_sale_ids)
        if in_stock_active and "out_of_stock" in ribbon_assign_values:
            search_product = search_product.filtered(lambda p: p.id not in sold_out_ids)
        if on_sale_active or in_stock_active:
            product_count = len(search_product)
        ProductTag = self.env["product.tag"]
        if filter_by_tags_enabled:
            all_tags = ProductTag.search_fetch(
                Domain.AND([
                    Domain("visible_to_customers", "=", True),
                    Domain.OR([
                        Domain("product_template_ids", "in", filters_query),
                        Domain("product_product_ids.product_tmpl_id", "in", filters_query),
                    ]),
                    website_domain,
                ])
            )
        else:
            all_tags = ProductTag
        Category = self.env["product.public.category"]
        categs_domain = (
            Domain("parent_id", "=", False) & Domain("not_in_shop", "=", False) & website_domain
        )
        if search:
            search_categories = Category.search(
                Domain("product_tmpl_ids", "in", shop_query)
            ).parents_and_self
            categs_domain &= Domain("id", "in", search_categories.ids)
        else:
            search_categories = Category
        categs = Category.search_fetch(categs_domain)
        category_entries = Category
        if category:
            available_categories = category.child_id.filtered(
                lambda c: c.website_id.id in (website.id, False)
            )
            category_entries = (
                not search and available_categories
            ) or available_categories.filtered(lambda c: c.id in search_categories.ids)
            if not category_entries:
                parent = category.parent_id
                available_categories = parent.child_id.filtered(
                    lambda c: c.website_id.id in (website.id, False)
                )
                category_entries = (
                    not search and available_categories
                ) or available_categories.filtered(lambda c: c.id in search_categories.ids)
            if not search and not self.env.user._is_internal():
                category_entries = category_entries.filtered("has_published_products")
        else:
            category_entries = categs

        pager = website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=5, url_args=post
        )
        offset = pager["offset"]
        products = search_product[offset : offset + ppg].with_prefetch()
        products.fetch()
        Product = self.env["product.product"]
        product_variant_ids = [product._get_first_possible_variant_id() for product in products]
        variants = Product.sudo().browse(vid for vid in product_variant_ids if vid)
        variants.fetch()
        variant_by_id = {v.id: v for v in variants}
        product_variants = dict(
            zip(products, (variant_by_id.get(vid, Product) for vid in product_variant_ids))
        )
        ProductAttribute = self.env["product.attribute"]
        ProductAttributeValue = self.env["product.attribute.value"]
        pavs_per_attribute = defaultdict(lambda: ProductAttributeValue)
        grouped_pavs = ProductAttributeValue._read_group(
            domain=[
                ("pav_attribute_line_ids.product_tmpl_id", "in", filters_query),
                ("attribute_id.visibility", "=", "visible"),
            ],
            groupby=["attribute_id"],
            order="attribute_id",
            aggregates=["id:recordset"],
        )
        pavs_per_attribute.update({attribute: pavs.sorted() for attribute, pavs in grouped_pavs})
        attributes = ProductAttribute.union(pavs_per_attribute.keys())
        products_prices = products._get_sales_prices(
            request.pricelist.with_context(self.env.context),
            request.fiscal_position.with_context(self.env.context),
            website.with_context(self.env.context),
        )
        product_query_params = self._get_product_query_params(**post)
        reset_attribute_value_params, reset_filters = self._get_shop_filter_reset_params()
        values = {
            'brand': brand,
            'brands': request.env['product.brand'].search([]),
            "auto_assign_ribbons": auto_assign_ribbons,
            "show_on_sale_filter": show_on_sale_filter,
            "show_in_stock_filter": show_in_stock_filter,
            "on_sale_active": on_sale_active,
            "in_stock_active": in_stock_active,
            "search": fuzzy_search_term or search,
            "original_search": fuzzy_search_term and search,
            "order": post.get("order", ""),
            "category": category,
            "attrib_values": attribute_value_dict,
            "attrib_set": attribute_value_ids,
            "pager": pager,
            "products": products,
            "product_variants": product_variants,
            "search_product": search_product,
            "search_count": product_count,
            "bins": TableCompute().process(products, ppg, ppr),
            "ppg": ppg,
            "ppr": ppr,
            "gap": gap,
            "categories": categs,
            "category_entries": category_entries,
            "attributes": attributes,
            "keep": keep,
            "search_categories_ids": search_categories.ids,
            "get_product_prices": lambda product: products_prices[product.id],
            "float_round": float_round,
            "shop_path": SHOP_PATH,
            "reset_attribute_value_params": reset_attribute_value_params,
            "reset_filters": reset_filters,
            "product_query_params": product_query_params,
            "grouped_attributes_values": grouped_attributes_values,
            "previewed_attribute_values": lazy(
                lambda: products._get_previewed_attribute_values(product_query_params)
            ),
            "pavs_per_attribute": pavs_per_attribute,
        }
        nb_filter_sections = len(attributes)
        if filter_by_price_enabled:
            values["min_price"] = min_price or available_min_price
            values["max_price"] = max_price or available_max_price
            values["available_min_price"] = float_round(available_min_price, 2)
            values["available_max_price"] = float_round(available_max_price, 2)
            if available_min_price != available_max_price:
                nb_filter_sections += 1
        if filter_by_tags_enabled:
            values.update({"all_tags": all_tags, "tags": tags})
            if all_tags:
                nb_filter_sections += 1
        if category:
            values["main_object"] = category
        values["structured_data"] = products.with_context(
            shop_category_id=category.id if category else False
        )._render_jsonld()
        if website.google_analytics_key:
            if category:
                item_list_name = category.with_context(lang=False).name
            elif fuzzy_search_term or search:
                item_list_name = "Search Results"
            else:
                item_list_name = "Shop"
            values["product_tracking_infos"] = products._get_google_analytics_list_data_batch(
                products_prices, website, item_list_name
            )
        values.update(self._get_additional_shop_values(values, **post))
        values["default_expand_filter_sections"] = nb_filter_sections < MAX_EXPANDED_FILTER_SECTIONS
        return request.render("website_sale.products", values)
