# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """ Inherits the Sale order Line model to include
        product dimension fields."""
    _inherit = 'sale.order.line'

    length_mm = fields.Float(
        string="Length (mm)",
        help="The length of the product in millimeters."
    )
    width_mm = fields.Float(
        string="Width (mm)",
        help="The width of the product in millimeters."
    )
    area_m2 = fields.Float(
        string="Area (m²)",
        compute="_compute_area",
        store=True,
        help="The area of the product in square meters, "
             "calculated based on length and width."
    )
    price_per_m2 = fields.Float(
        string="Price / m²",
        help="The price of the product per square meter."
    )


    @api.depends('length_mm', 'width_mm')
    def _compute_area(self):
        """Compute the area in square meters based on length and width."""
        for line in self:
            if line.length_mm and line.width_mm:
                line.area_m2 = (line.length_mm * line.width_mm) / 1000000.0
            else:
                line.area_m2 = 0.0

    @api.onchange('area_m2', 'price_per_m2', 'product_uom_qty')
    def _onchange_area_price_qty(self):
        """Recalculate unit price dynamically based on area (m²) and price per m²."""
        for line in self:
        # unit price per product = area * price_per_m2
            if line.area_m2 and line.price_per_m2:
                line.price_unit = line.area_m2 * line.price_per_m2


    def _prepare_invoice_line(self, **optional_values):
        """Include product dimension fields (length, width, area, price/m²) in the invoice line."""
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        values.update({
            'length_mm': self.length_mm,
            'width_mm': self.width_mm,
            'area_m2': self.area_m2,
            'price_per_m2': self.price_per_m2,
        })
        return values
