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
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float(
        string="On Hand Quantity", compute="_compute_stock_quantities")
    forecast_quantity = fields.Float(
        string="Forecast Quantity", compute="_compute_stock_quantities")

    @api.depends('product_id')
    def _compute_stock_quantities(self):
        params = self.env['ir.config_parameter'].sudo()
        restriction = params.get_param('sale_stock_restrict.product_restriction')
        check_stock = params.get_param('sale_stock_restrict.check_stock')
        for line in self:
            qty = forecast = 0.0
            if restriction and line.product_id:
                if check_stock == 'on_hand_quantity':
                    qty = line.product_id.qty_available
                elif check_stock == 'forecast_quantity':
                    forecast = line.product_id.virtual_available
            line.qty_available = qty
            line.forecast_quantity = forecast


class SaleOrder(models.Model):
    """Class to add fields in sale order and a function for confirming
    quotation."""
    _inherit = 'sale.order'

    onhand_check = fields.Boolean(
        string='Enable OnHand',
        help='To check whether it is based on on-hand quantity')
    forecast_check = fields.Boolean(
        string='Enable Forecast',
        help='To check whether it is based on forecast quantity')
    check_stock = fields.Boolean(string="Check Stock", compute="_compute_check_stock")

    def _compute_check_stock(self):
        value = self.env['ir.config_parameter'].sudo().get_param('sale_stock_restrict.check_stock')
        for record in self:
            record.check_stock = (value == 'on_hand_quantity')

    def action_confirm(self):
        """Function to restrict the confirming of quotation if the product is
        out of stock."""
        res = super().action_confirm()
        low_qty = ["Can't confirm the sale order due to: \n"]
        for rec in self.order_line:
            product_restriction = self.env[
                'ir.config_parameter'].sudo().get_param(
                'sale_stock_restrict.product_restriction')
            check_stock = self.env[
                'ir.config_parameter'].sudo().get_param(
                'sale_stock_restrict.check_stock')
            if (product_restriction and not self.website_id and
                    rec.product_id.type == 'consu'):
                if (check_stock == 'on_hand_quantity' and
                        rec.product_uom_qty > rec.qty_available):
                    self.onhand_check = True
                    low_qty.append(
                        f"You have added {rec.product_uom_qty} units of "
                        f"{rec.product_id.name}, but you only have "
                        f"{rec.qty_available} units available.")
                if (check_stock == 'forecast_quantity' and
                        rec.product_uom_qty > rec.forecast_quantity):
                    self.forecast_check = True
                    low_qty.append(
                        f"You have added {rec.product_uom_qty} units of "
                        f"{rec.product_id.name}, but you only have "
                        f"{rec.forecast_quantity} units available.")
        message = ' '.join(map(str, low_qty))
        if self.onhand_check:
            raise ValidationError(message)
        if self.forecast_check:
            raise ValidationError(message)
        return res
