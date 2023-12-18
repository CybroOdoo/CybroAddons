# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class SalonOrderLine(models.Model):
    """Creates salon_order_line model to store salon orders"""
    _name = 'salon.order.line'
    _description = 'Salon Order Lines'

    service_id = fields.Many2one('salon.service', string="Service",
                                 help="Select salon services")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="Default currency")
    price = fields.Monetary(string="Price", help="Price of service")
    salon_order_id = fields.Many2one(
        'salon.order', string="Salon Order", required=True, ondelete='cascade',
        index=True, copy=False, help="select Salon order")
    price_subtotal = fields.Monetary(string='Subtotal', help="Total price")
    time_taken = fields.Float(string='Time Taken', help="Time taken for "
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
