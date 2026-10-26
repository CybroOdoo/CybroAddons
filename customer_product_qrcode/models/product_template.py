# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class ProductTemplate(models.Model):
    """Extends the product.template model to generate QR codes for all
    related product variants."""
    _inherit = 'product.template'

    def action_generate_sequence(self):
        """Generate QR sequence for all product variants."""
        self.product_variant_ids.action_generate_sequence()

    def generate_sequence(self):
        """Server action alias for action_generate_sequence."""
        return self.action_generate_sequence()

    def action_generate_qr(self):
        """Generate QR codes for all product variants associated with the
        product template."""
        variants = self.product_variant_ids
        if variants:
            return variants.action_generate_qr()
        return False
