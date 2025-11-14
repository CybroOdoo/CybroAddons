# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class ProductWishlist(models.Model):
    """Inherited product_wishlist to overwrite a function"""
    _inherit = 'product.wishlist'

    @api.model
    def _add_to_wishlist(self, pricelist_id, currency_id, website_id, price,
                         product_id, partner_id=False):
        """Over-writing the function to check conditions"""
        existing_product = self.env['product.wishlist'].search_count([
            ('product_id', '=', product_id)])
        if existing_product == 1:
            return False
        else:
            wish = self.env['product.wishlist'].create({
                'partner_id': partner_id,
                'product_id': product_id,
                'currency_id': currency_id,
                'pricelist_id': pricelist_id,
                'price': price,
                'website_id': website_id,
            })
            total_wish = self.env['product.wishlist'].search_count([])
            return wish, total_wish
