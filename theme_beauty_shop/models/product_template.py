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
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _is_in_wishlist(self):
        """Check if any variant of this product template is in wishlist."""
        if not self:
            return False
        self.ensure_one()
        if 'product.wishlist' in self.env and hasattr(self.env['product.wishlist'], 'current'):
            return self in self.env['product.wishlist'].current().mapped('product_id.product_tmpl_id')
        variant = (
            self.product_variant_id
            or (self.product_variant_ids[:1] if self.product_variant_ids else False)
            or (self._create_first_product_variant() if hasattr(self, '_create_first_product_variant') else False)
        )
        if variant and hasattr(variant, '_is_in_wishlist'):
            return variant._is_in_wishlist()
        return False
