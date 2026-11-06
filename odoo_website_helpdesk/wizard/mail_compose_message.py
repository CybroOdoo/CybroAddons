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


class MailComposeMessage(models.TransientModel):
    """Save the date of the replies sent from the helpdesk tickets"""
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """Save the reply date on the tickets"""
        for composer in self.filtered(
                lambda wizard: wizard.model == 'ticket.helpdesk'):
            self.env['ticket.helpdesk'].browse(
                composer._evaluate_res_ids()).replied_date = (
                fields.Datetime.now())
        return super()._action_send_mail(auto_commit=auto_commit)
