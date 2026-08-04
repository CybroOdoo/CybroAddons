# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, Command


class SaleOrder(models.Model):
    """This class inherits from the 'sale.order' model and adds a
     method to create a corresponding purchase order based on specific
    conditions during order confirmation."""
    _inherit = 'sale.order'

    def _get_po_line_vals(self, line):
        """Return purchase order line values for a single sale order line.
        Handles section/note lines (display_type set) and regular product lines."""
        if line.display_type:
            # Section or note line — product_qty and price_unit must be 0
            # per the purchase.order.line DB constraint; product_qty=0 also
            # satisfies the ORM-level required=True on that field.
            return {
                'display_type': line.display_type,
                'name': line.name,
                'product_qty': 0.0,
                'price_unit': 0.0,
            }
        return {
            'product_id': line.product_id.id,
            'name': line.name or line.product_id.name,
            'product_qty': line.product_uom_qty,
            'product_uom_id': line.product_uom_id.id,
            'price_unit': line.price_unit,
        }

    def _create_purchase_order(self):
        """Create a purchase order based on the current sale order."""
        self.ensure_one()
        company = self.env['res.company'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not company:
            return False

        po_lines = [
            Command.create(self._get_po_line_vals(line))
            for line in self.order_line
            if line.display_type or line.product_id
        ]

        purchase_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company.id,
            'origin': self.name,
            'order_line': po_lines,
        }

        return self.env['purchase.order'].create(purchase_order_vals)

    def action_confirm(self):
        """Confirm the sale order and create a purchase order if
        conditions are met."""
        res = super(SaleOrder, self).action_confirm()
        transit_locations = self.env['stock.location'].search(
            [('active', '=', True), ('usage', '=', 'transit')], limit=1)
        if (transit_locations and self.env[
            'ir.config_parameter'].sudo().get_param(
                'inter_company_synchronization.sale_purchase_sync')):
            for order in self:
                if not order.client_order_ref:
                    order._create_purchase_order()
        return res

