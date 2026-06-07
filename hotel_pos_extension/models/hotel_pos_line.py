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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import  fields, models

class HotelPosLine(models.Model):
    """Store and link POS orders with hotel bookings for tracking and billing purposes."""
    _name = "hotel.pos.line"
    _description = "Hotel POS Line"

    booking_id = fields.Many2one("room.booking", string="Booking", ondelete="cascade")
    pos_order_id = fields.Many2one("pos.order", string="POS Order")
    pos_reference = fields.Char(related="pos_order_id.pos_reference", string="POS Ref")
    date_order = fields.Datetime(related="pos_order_id.date_order", string="Date")
    amount_total = fields.Monetary(related="pos_order_id.amount_total", string="Total")
    currency_id = fields.Many2one(related='booking_id.pricelist_id.currency_id', string="Currency")
    state = fields.Selection(related="pos_order_id.state", string="Status")
    session_id = fields.Many2one(related="pos_order_id.session_id", string="Session")
    user_id = fields.Many2one(related="pos_order_id.user_id", string="Cashier")
    partner_id = fields.Many2one(related="pos_order_id.partner_id", string="Customer")
