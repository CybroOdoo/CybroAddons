# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import datetime
from odoo import models, _
from odoo.exceptions import UserError


class MailComposeMessage(models.TransientModel):
    """inheriting mail compose message"""
    _inherit = "mail.compose.message"

    def action_send_via_zoho(self):
        """Send emails from wizard using Zoho"""
        self.ensure_one()
        account = self.env['zoho.mail.account'].search(
            [('state', '=', 'connected')], limit=1)
        if not account:
            raise UserError(_("No connected Zoho account found."))
        mail_record = account.send_mail(to_address=', '.join(
            self.partner_ids.mapped('email')),
            subject=self.subject, body=self.body,
            attachments=self.attachment_ids)
        self.env['zoho.mail.message'].create({
            'message_id': mail_record['data']['messageId'],
            'subject': mail_record['data']['subject'],
            'sender': mail_record['data']['fromAddress'],
            'recipients': mail_record['data']['toAddress'],
            'body': mail_record['data']['content'],
            'date': datetime.datetime.now(),
            'mail_type': 'sent',
            'attachment_ids': [(6, 0, self.attachment_ids.ids)]
       })
        return {
            'type': 'ir.actions.act_window_close'
        }
