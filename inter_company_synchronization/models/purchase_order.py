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


class PurchaseOrder(models.Model):
    """Inherited this model to create corresponding SO while creating PO"""
    _inherit = 'purchase.order'

    def _get_so_line_vals(self, line):
        """Return sale order line values for a single purchase order line.
        Handles section/note lines (display_type set) and regular product lines."""
        if line.display_type:
            return {
                'display_type': line.display_type,
                'name': line.name,
            }
        return {
            'product_id': line.product_id.id,
            'name': line.name or line.product_id.name,
            'product_uom_qty': line.product_qty,
            'price_unit': line.price_unit,
        }

    def _create_sale_order(self):
        """Creating sale order values to vendor company."""
        self.ensure_one()
        company = self.env['res.company'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not company:
            return False

        so_lines = [
            Command.create(self._get_so_line_vals(line))
            for line in self.order_line
            if line.display_type or line.product_id
        ]

        sale_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company.id,
            'client_order_ref': self.name,
            'order_line': so_lines,
        }
        return self.env['sale.order'].sudo().create(sale_order_vals)

    def button_confirm(self):
        """ Confirm the purchase order and create sale order i
        n another company."""
        res = super(PurchaseOrder, self).button_confirm()
        transit_locations = self.env['stock.location'].search(
            [('active', '=', True), ('usage', '=', 'transit')], limit=1)
        if (transit_locations and self.env['ir.config_parameter'].sudo().get_param(
                  'inter_company_synchronization.sale_purchase_sync')):
            for order in self:
                if not order.origin:
                    order._create_sale_order()
        return res

