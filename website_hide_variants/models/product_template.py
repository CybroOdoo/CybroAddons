# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: AYANA KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##########################################################################
from odoo import models


class ProductTemplate(models.Model):
    """Inherit product model to add a new filed to hide variants in website."""
    _inherit = 'product.template'

    def _get_combination_info(
        self, combination=False, product_id=False, add_qty=1,uom_id=False,
        only_template=False
    ):
        """
        Extend combination info to include is_website_hide_variants so the
        frontend JavaScript can react and show the unavailability notice.
        """
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            uom_id=uom_id,
            only_template=only_template,
        )

        is_hidden = False
        product = self.env['product.product'].browse(
            combination_info.get('product_id')
        )
        if product.exists():
            is_hidden = bool(product.is_website_hide_variants)

        combination_info['is_website_hide_variants'] = is_hidden

        # Also mark the combination as impossible so it can never be added to cart
        if is_hidden:
            combination_info['is_combination_possible'] = False

        return combination_info

    def _get_website_accessory_product(self):
        """Filter hidden variants from accessory products on website."""
        products = super()._get_website_accessory_product()
        if self.env.context.get('website_id'):
            products = products.filtered(
                lambda p: not p.is_website_hide_variants
            )
        return products

