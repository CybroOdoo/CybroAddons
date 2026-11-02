# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    """Show the on hand or forecast quantity of the product on order lines,
    following the restriction setting."""
    _inherit = 'sale.order.line'

    qty_available = fields.Float(
        string="On Hand Quantity", compute="_compute_stock_quantities")
    forecast_quantity = fields.Float(compute="_compute_stock_quantities")

    @api.depends('product_id')
    def _compute_stock_quantities(self):
        params = self.env['ir.config_parameter'].sudo()
        restriction = params.get_bool('sale_stock_restrict.product_restriction')
        check_stock = params.get_str('sale_stock_restrict.check_stock')
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
    """Block the confirmation of sale orders with out of stock products."""
    _inherit = 'sale.order'

    check_stock = fields.Boolean(compute="_compute_check_stock")

    def _compute_check_stock(self):
        value = self.env['ir.config_parameter'].sudo().get_str(
            'sale_stock_restrict.check_stock')
        for record in self:
            record.check_stock = value == 'on_hand_quantity'

    def action_confirm(self):
        """Function to restrict the confirming of quotation if the product is
        out of stock."""
        params = self.env['ir.config_parameter'].sudo()
        if params.get_bool('sale_stock_restrict.product_restriction'):
            check_stock = params.get_str('sale_stock_restrict.check_stock')
            low_qty = []
            for rec in self.filtered(lambda o: not o.website_id).order_line:
                if not rec.product_id.is_storable:
                    continue
                # qty_available / forecast_quantity are in the product UoM
                ordered_qty = rec.product_uom_id._compute_quantity(
                    rec.product_uom_qty, rec.product_id.uom_id)
                if check_stock == 'on_hand_quantity':
                    available = rec.qty_available
                elif check_stock == 'forecast_quantity':
                    available = rec.forecast_quantity
                else:
                    continue
                if ordered_qty > available:
                    low_qty.append(self.env._(
                        "You have added %(ordered)s %(ordered_uom)s of "
                        "%(product)s, but you only have %(available)s "
                        "%(uom)s available.",
                        ordered=rec.product_uom_qty,
                        ordered_uom=rec.product_uom_id.name,
                        product=rec.product_id.display_name,
                        available=available,
                        uom=rec.product_id.uom_id.name))
            if low_qty:
                raise ValidationError(
                    self.env._("Can't confirm the sale order due to:")
                    + '\n' + '\n'.join(low_qty))
        return super().action_confirm()
