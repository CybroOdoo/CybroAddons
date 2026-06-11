# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class AccountMove(models.Model):
    """Inherit the class account_move"""
    _inherit = 'account.move'

    def action_post(self):
        """Override action_post() to change truck_booking state to 'invoice'
         when the invoice is confirmed"""
        res = super().action_post()
        for move in self:
            booking_id = self.env['truck.booking'].search([
                ('reference_no', '=', move.invoice_origin)
            ], limit=1)
            if booking_id and booking_id.state != 'invoice':
                booking_id.write({'state': 'invoice'})
        return res
