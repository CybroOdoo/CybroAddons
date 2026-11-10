# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal

SEARCH_LIMIT = 50


class CustomerPortal(portal.CustomerPortal):
    """Extend the portal controller with the product availability page."""

    def _prepare_home_portal_values(self, counters):
        """Extend the portal home values with the product counter.

        The product availability card has no counter, so the value is
        set to None.

        :param list counters: names of the counters requested by the portal
        :return: the portal home values
        :rtype: dict
        """
        values = super()._prepare_home_portal_values(counters)
        if 'p_count' in counters:
            values['p_count'] = None
        return values

    @http.route('/my/product-availability', type='http', auth='user',
                website=True)
    def portal_products(self, **_kw):
        """Render the product availability page in the portal."""
        return request.render('portal_stock_check.portal_product_availability')

    @http.route('/product/search', type='jsonrpc', auth='user', website=True)
    def search_product(self, args):
        """Return the published products matching the given name.

        :param dict args: dictionary containing the product name to search
            for, under the key ``product``
        :return: list of dictionaries with the ``id``, ``display_name`` and
            ``qty_available`` of each matching product, or an empty list
            if the name is empty
        :rtype: list
        """
        product = (args.get('product') or '').strip()
        if not product:
            return []
        domain = [('name', 'ilike', product), ('is_published', '=', True)]
        return request.env['product.product'].sudo().search_read(
            domain=domain,
            fields=['id', 'display_name', 'qty_available'],
            limit=SEARCH_LIMIT,
        )
