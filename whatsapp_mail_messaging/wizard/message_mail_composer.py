# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import models, fields
from odoo.exceptions import UserError


class MessageMailComposer(models.TransientModel):
    """Wizard to compose and send emails."""
    _name = 'message.mail.composer'
    _description = 'Message Mail Composer'

    subject = fields.Char(string='Subject', required=True)
    email_from = fields.Char(
        string='From',
        required=True,
        default=lambda self: self._get_default_email_from()
    )
    email_to = fields.Char(string='To', required=True)
    email_cc = fields.Char(string='Cc')
    body = fields.Html(string='Body', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'message_mail_composer_attachment_rel',
        'composer_id',
        'attachment_id',
        string='Attachments'
    )

    def _get_default_email_from(self):
        """Get formatted email with user name"""
        user = self.env.user
        if user.email:
            # Format: "User Name <user@example.com>"
            return f"{user.name} <{user.email}>"
        return user.name

    def action_send_mail(self):
        """Send the email"""
        self.ensure_one()
        if not self.email_to:
            raise UserError('Please specify at least one recipient.')
        # Create mail.mail record
        mail_values = {
            'subject': self.subject,
            'email_from': self.email_from,
            'email_to': self.email_to,
            'email_cc': self.email_cc,
            'body_html': self.body,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
            'auto_delete': True,
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        return {'type': 'ir.actions.act_window_close'}
