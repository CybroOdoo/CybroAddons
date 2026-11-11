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


class SalonOrderLine(models.Model):
    """Creates salon_order_line model to store salon orders"""
    _name = 'salon.order.line'
    _description = 'Salon Order Lines'

    service_id = fields.Many2one('salon.service',
                                 help="Select salon services")
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.company.currency_id.id,
        help="Default currency")
    price = fields.Monetary(help="Price of service")
    salon_order_id = fields.Many2one(
        'salon.order', required=True, ondelete='cascade',
        index=True, copy=False, help="select Salon order")
    price_subtotal = fields.Monetary(string='Subtotal', help="Total price")
    time_taken = fields.Float(help="Time taken for "
                                                        "service")

    @api.onchange('service_id')
    def _onchange_service_id(self):
        """Onchange function of service_id field"""
        self.price = self.service_id.price
        self.price_subtotal = self.service_id.price
        self.time_taken = self.service_id.time_taken

    @api.onchange('price')
    def _onchange_price(self):
        """Onchange function of price field"""
        self.price_subtotal = self.price

    @api.onchange('price_subtotal')
    def _onchange_price_subtotal(self):
        """Onchange function of price_subtotal field"""
        self.price = self.price_subtotal
