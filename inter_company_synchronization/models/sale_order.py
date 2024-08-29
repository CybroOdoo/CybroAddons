# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """This class inherits from the 'sale.order' model and adds a
     method to create a corresponding purchase order based on specific
    conditions during order confirmation."""
    _inherit = 'sale.order'

    def _create_purchase_order(self):
        """Create a purchase order based on the current sale order."""
        company = self.env['res.company'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not company:
            return False

        purchase_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company.id,
            'origin': self.name,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
            }) for line in self.order_line],
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
                'inter_company_synchronization.sale_purchase_sync') and
                not self.client_order_ref):
            self._create_purchase_order()
        return res
