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


class SaleOrder(models.Model):
    """This class inherits from the 'sale.order' model and adds a
     method to create a corresponding purchase order based on specific
    conditions during order confirmation."""
    _inherit = 'sale.order'

    def _create_purchase_order(self):
        """Create a purchase order based on the current sale order."""
        company_id = self.env['res.company'].search(
            [('name', '=', self.partner_id.name)])
        purchase_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company_id.id,
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
            [('active', '=', True), ('usage', '=', 'transit')])
        res_config_settings = self.env['res.config.settings'].search([])
        if (transit_locations and res_config_settings[-1].sale_purchase_sync and
                not self.client_order_ref):
            self._create_purchase_order()
        return res
