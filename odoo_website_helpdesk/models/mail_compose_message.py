# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class MailComposeMessage(models.TransientModel):
    """ This class extends the functionality of the 'mail.compose.message'
    model to include custom behavior for sending emails related to help tickets.
   """
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """Override of the base '_action_send_mail' method to include additional
        logic when sending emails related to help tickets.

        If the model associated with the mail is 'help.ticket', update the
        'replied_date' field of the associated help ticket to the current date.
        """
        if self.model == 'help.ticket':
            ticket_id = self.env['help.ticket'].browse(self.res_id)
            ticket_id.replied_date = fields.Date.today()
        return super(MailComposeMessage, self)._action_send_mail(
            auto_commit=auto_commit)
