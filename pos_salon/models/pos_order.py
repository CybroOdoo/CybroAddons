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


class PosOrder(models.Model):
    _inherit = 'pos.order'

    salon_booking_ref = fields.Integer(
        string='Salon Booking ID', copy=False, index=True,
        help='ID of the salon.booking paid by this order.')

    def action_pos_order_paid(self):
        res = super().action_pos_order_paid()
        for order in self.filtered('salon_booking_ref'):
            booking = self.env['salon.booking'].sudo().browse(order.salon_booking_ref).exists()
            if booking:
                booking._mark_paid(order)
        return res