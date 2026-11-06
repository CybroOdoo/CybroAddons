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
from odoo import models


class SaleOrder(models.Model):
    """Inherited this model to create corresponding PO while confirming SO"""
    _inherit = 'sale.order'

    def _create_purchase_order(self):
        """Create the counterpart purchase order in the customer company."""
        self.ensure_one()
        company = self.env['res.company'].sudo().search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not company or company == self.company_id:
            return False
        purchase_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company.id,
            'origin': self.name,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
            }) for line in self.order_line if not line.display_type],
        }
        return self.env['purchase.order'].sudo().with_company(
            company).create(purchase_order_vals)

    def action_confirm(self):
        """Confirm the sale order and create a purchase order in the
        customer company."""
        res = super().action_confirm()
        sync_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'inter_company_synchronization.sale_purchase_sync')
        transit_location = self.env['stock.location'].search(
            [('usage', '=', 'transit')], limit=1)
        if sync_enabled and transit_location:
            for order in self.filtered(lambda o: not o.client_order_ref):
                order._create_purchase_order()
        return res
