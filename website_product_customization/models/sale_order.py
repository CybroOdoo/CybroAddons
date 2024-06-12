# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gaytahri V @ cybrosys,(odoo@cybrosys.com)
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
#############################################################################
from odoo import models


class SaleOrder(models.Model):
    """Inherited the class sale.order to match the order line."""
    _inherit = "sale.order"

    def _cart_find_product_line(self, product_id, line_id=None, **kwargs):
        """Find the cart line matching the given parameters.

        If a product_id is given, the line will match the product only if the
        line also has the same special attributes: `no_variant` attributes and
        `is_custom` values.
        """
        self.ensure_one()
        SaleOrderLine = self.env["sale.order.line"]
        if not self.order_line:
            return SaleOrderLine
        product = self.env["product.product"].browse(product_id)
        if not line_id and (
            product.product_tmpl_id.has_dynamic_attributes()
            or product.product_tmpl_id._has_no_variant_attributes()
        ):
            return SaleOrderLine
        if kwargs["design_image"]:
            return SaleOrderLine
        else:
            domain = [("order_id", "=", self.id), ("product_id", "=", product_id)]
            if line_id:
                domain += [("id", "=", line_id)]
            else:
                domain += [
                    ("product_custom_attribute_value_ids", "=", False),
                    ("is_customized_product", "=", False),
                ]
        return SaleOrderLine.search(domain)
