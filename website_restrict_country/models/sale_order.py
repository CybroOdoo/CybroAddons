# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from functools import reduce
from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
        This class inherits to add a function to the sale.order
        for fetching the common country list.
    """
    _inherit = 'sale.order'

    @property
    def get_common_country_list(self):
        """
            This function is added for fetching the common country list.
        """
        country_lists = [
            line.product_id.product_tmpl_id.country_selection_ids.mapped(
                'country_id.id')
            for line in self.order_line
            if line.product_id.product_tmpl_id.country_availability != 'all'
        ]
        try:
            country_list = list(
                reduce(lambda i, j: i & j, (set(x) for x in country_lists)))
        except Exception as error:
            _logger.info(f'Country list has been made empty list due to {error}')
            country_list = []
        return country_list

    def _get_country_restricted_products(self):
        """
            Return the product templates in the cart that are not available in
            the website's currently selected country.
        """
        self.ensure_one()
        country = self.website_id.default_country_id
        restricted = self.env['product.template']
        for line in self.order_line:
            template = line.product_id.product_tmpl_id
            if template.country_availability != 'selected':
                continue
            allowed_countries = template.country_selection_ids.mapped(
                'country_id')
            if country not in allowed_countries:
                restricted |= template
        return restricted

    def _is_cart_fully_restricted(self):
        """
            Return True when every product in the cart is unavailable in the
            website's currently selected country (so there is nothing the
            customer can actually buy).
        """
        self.ensure_one()
        products = self.order_line.product_id.product_tmpl_id
        if not products:
            return False
        return all(
            product in self._get_country_restricted_products()
            for product in products)

    def _check_cart_is_ready_to_be_paid(self):
        """
            Prevent paying for a cart that holds a product which is not
            available in the selected country, regardless of which payment
            path (checkout button, express checkout, ...) is used.
        """
        restricted = self._get_country_restricted_products()
        if restricted:
            raise ValidationError(_(
                "The following product(s) are not available in the selected "
                "country and cannot be ordered: %s",
                ", ".join(restricted.mapped('name'))))
        return super()._check_cart_is_ready_to_be_paid()

    def _allow_express_checkout(self):
        """
            Hide the express checkout buttons (e.g. "Pay with ...") when the
            whole cart is restricted to the selected country.
        """
        if self._is_cart_fully_restricted():
            return False
        return super()._allow_express_checkout()
