# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Extends sale.order.line to add margin and margin_percent"""
    _inherit = "sale.order.line"

    margin = fields.Float(
        "Margin", compute='_compute_margin',
         store=True, inverse='_inverse_margin',readonly=False)

    margin_percent = fields.Float(
        "Margin (%)", compute='_compute_margin',inverse='_inverse_margin_percent', store=True)

    
    def _inverse_margin(self):
        """Calculate and update the unit price based on the total margin.
               This method recomputes the unit price whenever the total margin
               is manually updated. It ensures the price aligns with the
               purchase cost and the quantity sold.
               """
        for line in self:
            if line.product_uom_qty:
                line.price_unit = line.purchase_price + (line.margin / line.product_uom_qty)

    def _inverse_margin_percent(self):
        """Calculate and update the unit price based on the margin percentage.
                This method recomputes the unit price when the margin percentage
                is changed. It prevents division by zero by only running when
                the margin percentage is less than 100% (1.0).
                """
        for line in self:
            if line.margin_percent < 1.0:
                line.price_unit = line.purchase_price / (1.0 - line.margin_percent)

    @api.depends('price_unit', 'purchase_price', 'product_uom_qty')
    def _compute_margin(self):
        """Calculate the total margin amount and the margin percentage.
               This method automatically computes the financial margin metrics
               for each line item whenever the unit price, purchase price,
               or product quantity changes. It includes a fallback to prevent
               division by zero if the subtotal is zero.
               """
        for line in self:
            subtotal = line.price_unit * line.product_uom_qty
            line.margin = (line.price_unit - line.purchase_price) * line.product_uom_qty
            line.margin_percent = (line.margin / subtotal) if subtotal else 0.0


    @api.onchange('margin')
    def _onchange_margin_custom(self):
        """ Trigger dynamic UI updates in form view when margin is edited """
        if self.product_uom_qty and self.purchase_price:
            self.price_unit = self.purchase_price + (self.margin / self.product_uom_qty)
            subtotal = self.price_unit * self.product_uom_qty
            self.margin_percent = (self.margin / subtotal) if subtotal else 0.0

    @api.onchange('margin_percent')
    def _onchange_margin_percent_custom(self):
        """ Trigger dynamic UI updates in form view when margin_percent is edited """
        if self.margin_percent < 1.0:
            denom = 1.0 - self.margin_percent
            if denom > 0:
                self.price_unit = self.purchase_price / denom
                self.margin = (self.price_unit - self.purchase_price) * (self.product_uom_qty or 1.0)
