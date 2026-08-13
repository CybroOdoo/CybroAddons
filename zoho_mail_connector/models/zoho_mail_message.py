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
from odoo import fields, models


class ZohoMailMessage(models.Model):
    """Model for storing and managing Zoho Mail messages.

        Stores email details such as message ID, subject, sender, recipients,
        date, message type, body, CC addresses, and associated attachments
        synchronized from Zoho Mail.
        """
    _name = 'zoho.mail.message'
    _description = 'Zoho Mail Message'
    _rec_name = 'subject'

    message_id = fields.Char(
        string='Mail Message', required=True,
        unique=True, index=True,
        help="The unique message identifier assigned by Zoho Mail.")
    subject = fields.Char(string='Subject', help="The subject line of the email.")
    sender = fields.Char(string='Sender', help="The email address of the sender.")
    recipients = fields.Text(string='Recipients',
                             help="The email address of the primary recipients.")
    date = fields.Datetime(string='Date',
                           help="The date the message was sent or received.")
    mail_type = fields.Selection([
        ('inbox', 'Inbox'),
        ('sent', 'Sent')], string='Mail Type',
        help="Indicates whether the email is from the Inbox or Sent folder.")
    body = fields.Html(string='Body', help="The subject line of the email.")
    has_attachments = fields.Boolean(
        string='Has Attachments',
        help="Indicates whether the email contains one or more attachments.")
    cc_address = fields.Text(
        string='CC',
        help="The email addresses included in the CC field.")
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Attachments associated with this email.")
    has_attachment = fields.Boolean(
        string='Has Attachment',
        help="Indicates whether the email has any linked attachment records."
    )
