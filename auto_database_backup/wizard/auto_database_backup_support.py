# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
import json
import logging
from urllib.parse import quote
import requests
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

SUPPORT_ENDPOINT = 'https://cybrosys.easyinstance.com/help/request'
SUPPORT_TIMEOUT = (5, 20)

_logger = logging.getLogger(__name__)


class AutoDatabaseBackupSupport(models.TransientModel):
    _name = 'auto.database.backup.support'
    _description = 'Automatic Database Backup Support'

    name = fields.Char(
        string='Customer Name',
        default=lambda self: self.env.user.name,
        help='Enter name')
    email = fields.Char(
        string='Email', required=True, default=lambda self: self.env.user.email,
        help='Enter your Email')
    phone = fields.Char(
        string='Phone',
        default=lambda self: self.env.user.partner_id.phone,
        help='Contact number for follow-up (optional).')
    subject = fields.Char(
        string='Subject', required=True,
        default='Automatic Database Backup Support',
        help='Short summary of the issue.')
    description = fields.Text(
        string='Description',
        help='Specify your problem in detail.')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Attach files related to your problem.')
    support_type = fields.Selection([
        ('functional', 'Functional Support'),
        ('technical', 'Technical Support'),
    ], string='Support Type', default='technical', help='Select support type')
    category = fields.Selection([
        ('installation', 'Installation'),
        ('configuration', 'Configuration'),
        ('bug', 'Bug'),
        ('feature_request', 'Feature Request'),
        ('performance', 'Performance'),
        ('other', 'Other'),
    ], string='Category', default='bug', help='What kind of issue is this?')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Blocker'),
    ], string='Priority', default='2', help='How urgent is this issue?')
    show_payload = fields.Boolean(
        string='Show what will be sent',
        help='Preview the exact data sent to Cybrosys before submitting.')
    payload_preview = fields.Text(
        string='Payload preview',
        compute='_compute_payload_preview',
        help='Read-only JSON of what will be sent on Submit. '
             'Attachment bytes are redacted to keep the preview readable.')

    def _prepare_attachment_payload(self):
        payload = []
        for attachment in self.attachment_ids:
            if not attachment.datas:
                continue
            data = attachment.datas
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            payload.append({
                'data': data,
                'name': attachment.name,
            })
        return payload

    def _build_payload(self, redact_attachments=False):
        self.ensure_one()
        if redact_attachments:
            count = sum(1 for attachment in self.attachment_ids if attachment.datas)
            attachments_value = (
                _('%d attachment') % count if count == 1
                else _('%d attachments') % count
            )
        else:
            attachments_value = self._prepare_attachment_payload()
        return {
            'params': {
                'customer_name': self.name or '',
                'email': self.email or '',
                'phone': self.phone or '',
                'subject': self.subject or '',
                'description': self.description or '',
                'support_type': self.support_type or '',
                'category': dict(self._fields['category'].selection).get(
                    self.category, ''),
                'priority': dict(self._fields['priority'].selection).get(
                    self.priority, ''),
                'attachments': attachments_value,
            }
        }

    @api.depends('name', 'email', 'phone', 'subject', 'description',
                 'support_type', 'category', 'priority', 'attachment_ids',
                 'show_payload')
    def _compute_payload_preview(self):
        for record in self:
            if record.show_payload:
                record.payload_preview = json.dumps(
                    record._build_payload(redact_attachments=True),
                    indent=2,
                    ensure_ascii=False,
                )
            else:
                record.payload_preview = False

    def _submit_support_request(self):
        self.ensure_one()
        response = requests.post(
            SUPPORT_ENDPOINT,
            json=self._build_payload(),
            timeout=SUPPORT_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def confirm_button(self):
        self.ensure_one()
        try:
            response_status = self._submit_support_request()
        except requests.HTTPError as error:
            status_code = (
                error.response.status_code if error.response is not None else 0
            )
            _logger.exception(
                "Support submission rejected by server (HTTP %s)", status_code)
            if status_code == 413:
                raise ValidationError(_(
                    "Your attachments are too large. "
                    "Please reduce their size and try again."
                )) from None
            if status_code >= 500:
                raise ValidationError(_(
                    "The support service is having issues. "
                    "Please try again in a few minutes."
                )) from None
            raise ValidationError(_(
                "The ticket submission was rejected. "
                "Please check your inputs and try again."
            )) from None
        except (requests.ConnectionError, requests.Timeout):
            _logger.exception(
                "Support submission failed due to a network error")
            raise ValidationError(_(
                "Could not reach the support service. "
                "Please check your network and try again."
            )) from None
        except (json.JSONDecodeError, ValueError):
            _logger.exception(
                "Support service returned an invalid response")
            raise ValidationError(_(
                "The support service returned an unexpected response. "
                "Please try again later."
            )) from None

        if response_status.get('result', {}).get('message') == 'success':
            result = response_status.get('result', {})
            ticket_id = result.get('ticket_id') or ''
            lines = [_("Your Ticket Created Successfully"), '']
            if ticket_id:
                lines.append(_("Ticket Reference : %s") % ticket_id)
            lines.extend(['', _("Save this reference to follow up with Cybrosys.")])
            message = '\n'.join(lines)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success',
                    'sticky': True,
                    'className': 'o_auto_database_backup_ticket_notification',
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        raise ValidationError(
            _("The ticket submission did not go through. Please try again.")
        )

    def whatsapp_button(self):
        self.ensure_one()
        message = "{name}\n{email}\n{description}".format(
            name=self.name,
            email=self.email,
            description=self.description,
        )
        phone_number = '+91 90742 70811'
        return {
            'type': 'ir.actions.act_url',
            'url': f"https://wa.me/{phone_number}?text={quote(message)}",
            'target': 'new',
            'res_id': self.id,
        }
