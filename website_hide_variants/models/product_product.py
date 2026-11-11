# -*- coding: utf-8 -*-
#################################################################################
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
################################################################################

from odoo import fields, models


class ProductProduct(models.Model):
    """Inherit product model to add a new field to hide variants in website."""
    _inherit = 'product.product'

    is_website_hide_variants = fields.Boolean(
        string="Hide on Website",
        default=False,
        help="Check this if you want to hide the variant on your website shop. "
             "The variant will remain active for internal use but won't be "
             "visible or selectable on the eCommerce storefront."
    )

    def _is_variant_possible(self):
        """Override to exclude hidden variants from website combination checks."""
        res = super()._is_variant_possible()
        if res and self.env.context.get('website_id') and self.is_website_hide_variants:
            return False
        return res

    def _is_add_to_cart_allowed(self):
        """Prevent hidden variants from being added to the cart, even when the
        add to cart request is sent directly to the server."""
        return (super()._is_add_to_cart_allowed()
                and not self.is_website_hide_variants)
