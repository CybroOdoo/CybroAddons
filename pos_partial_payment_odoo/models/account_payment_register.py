# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj(odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class AccountPaymentRegister(models.TransientModel):
    """
    Model to inherit 'account.payment.register' for supering the Payment Button
    to change functionality.
    """
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        """
        Override the 'action_create_payments' method to set
        'is_partial_payment' to False for the current order associated with
        the active session.
        """
        res = super(AccountPaymentRegister,self).action_create_payments()
        active_session = self.env['pos.session'].search(
            [('state', '=', 'opened'),
             ('user_id', '=', self.env.user.id)], limit=1)
        if active_session:
            current_order = self.env['pos.order'].search(
                [('session_id', '=', active_session.id),
                 ('state', '=', 'invoiced')], limit=1)
            if current_order:
                current_order.write({'is_partial_payment': False})
        return res
