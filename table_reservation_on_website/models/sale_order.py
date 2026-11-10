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
"""Sale order and sale order line models for table reservations."""
from odoo import api, fields, models


class SaleOrder(models.Model):
    """ Inherit sale order for adding new fields """
    _inherit = 'sale.order'

    table_reservation_id = fields.Many2one(
        comodel_name='table.reservation',
        help="Can view the table reservation", readonly=True)
    tables_ids = fields.Many2many("restaurant.table",
                                  help="Booked Tables")
    floors = fields.Integer(string="Floor Number", help="Number of the Floor")
    date = fields.Date(help="Date of reservation")
    starting_at = fields.Char(help="starting time of reservation")
    ending_at = fields.Char(help="Ending time of reservation")
    booking_amount = fields.Float(help="Booking Charge")


class SaleOrderLine(models.Model):
    """ Inherit sale order line to preserve reservation pricing per order """
    _inherit = 'sale.order.line'

    @api.depends('order_id.booking_amount', 'order_id.tables_ids')
    def _compute_price_unit(self):
        res = super()._compute_price_unit()
        booking_product = self.env.ref(
            'table_reservation_on_website.product_product_table_booking',
            raise_if_not_found=False)
        if booking_product:
            for line in self:
                if line.product_id == booking_product and line.order_id.booking_amount:
                    line.price_unit = line.order_id.booking_amount
        return res
