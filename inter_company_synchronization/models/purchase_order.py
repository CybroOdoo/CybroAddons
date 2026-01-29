# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    """Inherited this model to create corresponding SO while creating PO"""
    _inherit = 'purchase.order'

    def _create_sale_order(self):
        """Creating sale order values to vendor company."""
        company_id = self.env['res.company'].search(
            [('name', '=', self.partner_id.name)])
        sale_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company_id.id,
            'client_order_ref': self.name,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit,
                'tax_id': [(6, 0, line.taxes_id.ids)],
                'price_subtotal': line.price_subtotal,
            }) for line in self.order_line],
        }
        return self.env['sale.order'].sudo().create(sale_order_vals)

    def button_confirm(self):
        """ Confirm the purchase order and create sale order i
        n another company."""
        res = super(PurchaseOrder, self).button_confirm()
        transit_locations = self.env['stock.location'].search(
            [('active', '=', True), ('usage', '=', 'transit')])
        res_config_settings = self.env['res.config.settings'].search([])
        if (transit_locations and res_config_settings[-1].sale_purchase_sync and
                not self.origin):
            self._create_sale_order()
        return res
