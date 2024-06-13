# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
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

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'state')
    def _compute_qty_to_invoice(self):
        """Over-write the _compute_qty_to_invoice function
        to look weather order is subscriptions"""
        for line in self:
            if (line.order_id.subscription_id and not
                line.order_id.subscription_id.is_closed
                    and line.order_id.is_subscription):
                if line.product_template_id.is_subscription:
                    line.qty_to_invoice = line.product_uom_qty
            else:
                if line.state == 'sale' and not line.display_type:
                    if line.product_id.invoice_policy == 'order':
                        line.qty_to_invoice = (
                                line.product_uom_qty - line.qty_invoiced)
                    else:
                        line.qty_to_invoice = (
                                line.qty_delivered - line.qty_invoiced)
                else:
                    line.qty_to_invoice = 0
