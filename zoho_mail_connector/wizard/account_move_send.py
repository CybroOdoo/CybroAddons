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
import base64
import datetime
from odoo import models, _
from odoo.exceptions import UserError


class AccountMoveSend(models.TransientModel):
    """Inherit Account Move Send wizard to send invoices via Zoho Mail"""
    _inherit = "account.move.send"

    def action_send_via_zoho(self):
        """Send invoice email and attachments via Zoho Mail account"""
        self.ensure_one()
        account = self.env['zoho.mail.account'].search(
            [('state', '=', 'connected')], limit=1)
        if not account:
            raise UserError(_("No connected Zoho account found."))

        recipient_emails = [
            email for email in self.mail_partner_ids.mapped('email') if email
        ]
        if not recipient_emails:
            raise UserError(_("No recipient email address specified."))

        to_address = ', '.join(recipient_emails)
        subject = self.mail_subject or _("Invoice")
        body = self.mail_body or ""

        # Collect attachments
        attachments = self.env['ir.attachment']

        if self.mail_attachments_widget:
            att_ids = []
            for att in self.mail_attachments_widget:
                if isinstance(att, dict) and att.get('id') and not att.get('skip'):
                    try:
                        att_ids.append(int(att['id']))
                    except (ValueError, TypeError):
                        continue
            if att_ids:
                attachments |= self.env['ir.attachment'].browse(att_ids).exists()

        for move in self.move_ids:
            if move.invoice_pdf_report_id:
                attachments |= move.invoice_pdf_report_id
            else:
                try:
                    content, _format = self.env['ir.actions.report'].sudo()._render(
                        'account.account_invoices', move.ids
                    )
                    pdf_attachment = self.env['ir.attachment'].create({
                        'name': move._get_invoice_report_filename(),
                        'type': 'binary',
                        'datas': base64.b64encode(content),
                        'res_model': 'account.move',
                        'res_id': move.id,
                        'mimetype': 'application/pdf',
                    })
                    attachments |= pdf_attachment
                except Exception:
                    pass

        mail_record = account.send_mail(
            to_address=to_address,
            subject=subject,
            body=body,
            attachments=attachments
        )

        self.env['zoho.mail.message'].create({
            'message_id': mail_record['data']['messageId'],
            'subject': mail_record['data']['subject'],
            'sender': mail_record['data']['fromAddress'],
            'recipients': mail_record['data']['toAddress'],
            'body': mail_record['data']['content'],
            'date': datetime.datetime.now(),
            'mail_type': 'sent',
            'attachment_ids': [(6, 0, attachments.ids)] if attachments else False,
        })

        for move in self.move_ids:
            move.message_post(
                body=body,
                subject=subject,
                attachment_ids=attachments.ids,
            )
            if hasattr(move, 'is_move_sent'):
                move.is_move_sent = True

        return {
            'type': 'ir.actions.act_window_close'
        }
