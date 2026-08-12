# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
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

from odoo import models, _


class ProductProduct(models.Model):
    """ Class to inherit product_product to add some functionalities """
    _inherit = 'product.product'

    def _update_standard_price(self, extra_value=None, extra_quantity=None):
        # TODO: Add extra value and extra quantity kwargs to avoid total recomputation
        for product in self:
            if product.cost_method == 'standard':
                continue
            elif product.cost_method == 'fifo':
                fifo_price = product.total_value / product.qty_available if product.qty_available else 0
                product.with_context(disable_auto_revaluation=True).standard_price = fifo_price
                continue
            elif product.cost_method == 'average':
                product.with_context(disable_auto_revaluation=True).standard_price = product._run_avco()[0]
            elif product.cost_method == 'last':
                # Step 1: Get last confirmed purchase order line
                last_po_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', product.id),
                    ('state', '=', 'purchase')  # confirmed PO
                ], order="date_order desc", limit=1)
                last_price = 0.0
                if last_po_line:
                    # Step 2: Check if PO has a confirmed vendor bill
                    invoices = last_po_line.order_id.invoice_ids.filtered(
                        lambda inv: inv.state == 'posted' and inv.move_type == 'in_invoice')
                    if invoices:
                        # Take the invoice line price if available
                        inv_line = invoices.mapped('invoice_line_ids').filtered(lambda l: l.product_id == product)
                        if inv_line:
                            # Use unit price from vendor bill
                            last_price = inv_line[0].price_unit
                    # Step 3: If no invoice price, fallback to PO line price
                    if not last_price:
                        last_price = last_po_line.price_unit
                if last_price:
                    product.with_context(disable_auto_revaluation=True).standard_price = last_price
