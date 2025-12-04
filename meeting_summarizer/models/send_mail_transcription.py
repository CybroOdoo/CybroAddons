# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
"""
This module defines a transient model for sending transcription files via email in Odoo.

The `SendMailTranscription` model facilitates the creation of a wizard where users can:
- Specify the recipient's email address.
- Enter the subject and body of the email.
- Choose whether to attach a transcription file.

This module also includes the necessary logic for sending the email, potentially
using predefined email templates.
"""
from odoo import fields, models


class SendMailTranscription(models.TransientModel):
    """Created a new transient model for send mail"""
    _name = 'send.mail.transcription'
    _description = "Display send mail transcription wizard details"

    partner_ids = fields.Many2many('res.partner', string='Recipients',
                                   help="Select multiple recipients")
    subject = fields.Char(string='Subject', required=True,
                          help="Subject of the email")
    email_body = fields.Html(required=True, String="Content",
                             help="Body of the email")
    transcription_attachment_ids = fields.Many2many(
        'ir.attachment','transcription_attachment_rel', string='Transcription', readonly=True,
        help="Transcription attachment ")
    summary_attachment_ids = fields.Many2many(
        'ir.attachment','summary_attachment_rel', string='Summary', readonly=True,
        help="Summary attachment ")

    def action_send_transcription(self):
        """Button action to send mail to the corresponding users that select in recipient mail"""
        transcription_id = self.id
        email_list = [','.join(self.partner_ids.mapped(
            'email'))]  # Collect emails from all partners
        from_mail = self.env.user.email
        mail_template = (self.env.ref(
            'meeting_summarizer.email_template_transcription'))
        attachment_ids = []

        for attachment in self.transcription_attachment_ids:
            attachment_ids.append(
                (4, attachment.id))

        # Loop through summary attachments and add them
        for attachment in self.summary_attachment_ids:
            attachment_ids.append(
                (4, attachment.id))  # (4, attachment_id) adds attachment

        email_values = {
            'email_from': from_mail,
            'email_to': ','.join(email_list),
            'subject': self.subject,
            'body_html': self.email_body,
            'attachment_ids': attachment_ids,  # Attach the files here
        }
        # Send the email using the template
        mail_template.send_mail(transcription_id, email_values=email_values,
                                force_send=True)
