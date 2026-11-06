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


class PurchaseOrder(models.Model):
    """Inherited this model to create corresponding SO while creating PO"""
    _inherit = 'purchase.order'

    def _create_sale_order(self):
        """Create the counterpart sale order in the vendor company."""
        self.ensure_one()
        company = self.env['res.company'].sudo().search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not company or company == self.company_id:
            return False
        sale_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company.id,
            'client_order_ref': self.name,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit,
            }) for line in self.order_line if not line.display_type],
        }
        return self.env['sale.order'].sudo().with_company(company).create(
            sale_order_vals)

    def button_confirm(self):
        """Confirm the purchase order and create a sale order in the
        vendor company."""
        res = super().button_confirm()
        sync_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'inter_company_synchronization.sale_purchase_sync')
        transit_location = self.env['stock.location'].search(
            [('usage', '=', 'transit')], limit=1)
        if sync_enabled and transit_location:
            for order in self.filtered(lambda o: not o.origin):
                order._create_sale_order()
        return res
