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
from odoo import fields, models


class StockReservation(models.TransientModel):
    """ This model for storing wizard order line values."""
    _name = "stock.reservation"
    _description = "Stock Reservation Line"

    stock_reservation_wizard_id = fields.Many2one(
        "sale.stock.reservation", string="Wizard",
        help="Sale stock reservation wizard")
    order_line_name = fields.Char(
        string="Order Line",
        help="Name of order line")
    product_id = fields.Many2one(
        "product.product",
        help="Product to be reserved")
    quantity = fields.Float(help="Product quantity")
    unit_of_measure_id = fields.Many2one(
        "uom.uom", string="UOM", help="Unit of measure")
    reserve_quantity = fields.Float(
        help="Quantity to be reserved")
    move_id = fields.Many2one(
        "stock.move", string="Stock Move", help="Stock move")
