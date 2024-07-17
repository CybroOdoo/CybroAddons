# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
from odoo import models


class AccountMove(models.Model):
    """Inherit the class account_move"""
    _inherit = 'account.move'

    def action_post(self):
        """Super the action_post() to change truck_booking state into invoice"""
        res = super(AccountMove, self).action_post()
        if self:
            booking_id = self.env['truck.booking']\
                .browse(self.env.context.get('active_id'))
            amount = sum(self.search([
                ('invoice_origin', '=', booking_id.reference_no),
                ('state', '!=', 'cancel')]).mapped('amount_untaxed_signed'))
            if booking_id.amount == amount:
                booking_id.write({'state': 'invoice'})
        return res
