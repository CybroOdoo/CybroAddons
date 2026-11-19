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
from odoo import models


class AccountMoveLine(models.Model):
    """Inherits the model account.move.line for making the payment
    from the action menu"""
    _inherit = 'account.move.line'

    def action_register_payment(self, ctx=None):
        """Open the account.payment.register wizard for the invoices of the
        selected journal items.
        :param ctx: Extra context values to pass to the wizard.
        :return: An action opening the account.payment.register wizard.
        """
        action = super().action_register_payment(ctx=ctx)
        action['name'] = self.env._('Register Payment')
        action['context'].update({
            'active_model': 'account.move',
            'active_ids': self.move_id.ids,
            'dont_redirect_to_payments': True,
            **(ctx or {}),
        })
        return action
