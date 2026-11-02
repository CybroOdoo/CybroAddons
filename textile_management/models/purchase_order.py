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
from odoo import fields, models
from odoo.fields import Domain


class PurchaseOrder(models.Model):
    """Flag the purchase orders of the textile app."""
    _inherit = 'purchase.order'

    is_textile_purchase_order = fields.Boolean(
        help="The purchase order was created from the Textile app")

    def _get_product_catalog_domain(self):
        """Limit the product catalog of textile orders to textile products."""
        domain = super()._get_product_catalog_domain()
        if self.is_textile_purchase_order:
            domain &= Domain('is_textile_product', '=', True)
        return domain
