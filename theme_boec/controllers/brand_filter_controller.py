# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class ProductBrand(WebsiteSale):
    """Add the theme's brand filtering without replacing Odoo's shop flow."""

    @http.route()
    def shop(self, *args, **kwargs):
        return super().shop(*args, **kwargs)


    def _get_search_options(self, **kwargs):
        res = super()._get_search_options(**kwargs)
        res['brand_ids'] = self._get_brand_ids()
        return res

    def _shop_get_query_url_kwargs(self, *args, **kwargs):
        res = super()._shop_get_query_url_kwargs(*args, **kwargs)
        res['brand'] = self._get_brand_ids()
        return res

    def _get_additional_shop_values(self, values, **kwargs):
        res = super()._get_additional_shop_values(values, **kwargs)
        res['brand_ids'] = self._get_brand_ids()
        return res

    @staticmethod
    def _get_brand_ids():
        """Return valid, selected brand IDs from the multi-value query parameter."""
        brand_ids = []
        for brand_id in request.httprequest.args.getlist('brand'):
            try:
                brand_ids.append(int(brand_id))
            except (TypeError, ValueError):
                continue
        return brand_ids
