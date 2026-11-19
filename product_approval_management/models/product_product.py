# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#############################################################################
from odoo import models


class ProductProduct(models.Model):
    """Approval actions for product variants. The ``approve_state`` field is
    defined on product.template and reached from the variant through the
    ``_inherits`` delegation, so it must not be redefined here."""
    _inherit = 'product.product'

    def action_confirm_product_approval(self):
        """Confirm the products"""
        self.product_tmpl_id.action_confirm_product_approval()

    def action_reset_product_approval(self):
        """Reset the products to draft"""
        self.product_tmpl_id.action_reset_product_approval()

    def action_confirm_products(self):
        """Bulk product approval from the list view action"""
        products = self.browse(self.env.context.get('active_ids', []))
        products.action_confirm_product_approval()
