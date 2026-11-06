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
import json
import logging
from urllib.parse import quote, urlsplit

import requests

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Config parameter that holds the support endpoint URL. Falls back to
# DEFAULT_SUPPORT_ENDPOINT when unset, so a domain change is a config edit
# rather than a code release.
SUPPORT_ENDPOINT_PARAM = 'cybrosys_support_client.endpoint_url'
DEFAULT_SUPPORT_ENDPOINT = 'https://support.cybrosys.com/help/request'
SUPPORT_TIMEOUT = (5, 20)  # (connect, read) seconds

_logger = logging.getLogger(__name__)


class ClientSupport(models.TransientModel):
    _name = 'client.support'
    _description = 'Client Support'

    name = fields.Char(
        string='Customer Name',
        default=lambda self: self.env.user.name,
        help='Enter your name.')
    email = fields.Char(
        required=True, default=lambda self: self.env.user.email,
        help='Enter your email address.')
    phone = fields.Char(
        default=lambda self: self.env.user.partner_id.phone,
        help='Contact number for follow-up (optional).')
    subject = fields.Char(
        required=True,
        help='Short summary of the issue.')
    description = fields.Text(
        help='Specify your problem in detail.')
    attachment_ids = fields.Many2many('ir.attachment',
                                      help='Attach files related to your problem.')
    support_type = fields.Selection([
        ('functional', 'Functional Support'),
        ('technical', 'Technical Support'), ],
        default="technical", help='Select the support type.')
    category = fields.Selection([
        ('installation', 'Installation'),
        ('configuration', 'Configuration'),
        ('bug', 'Bug'),
        ('feature_request', 'Feature Request'),
        ('performance', 'Performance'),
        ('other', 'Other'),
    ], default='bug', help='What kind of issue is this?')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Blocker'),
    ], default='2',
        help='How urgent is this issue?')
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
            if not attachment.raw:
                continue
            payload.append({
                'data': attachment.raw.to_base64(),
                'name': attachment.name,
            })
        return payload

    def _build_payload(self, redact_attachments=False):
        self.ensure_one()
        if redact_attachments:
            count = sum(1 for a in self.attachment_ids if a.raw)
            attachments_value = (
                self.env._('%d attachment', count) if count == 1
                else self.env._('%d attachments', count)
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
                    indent=2, ensure_ascii=False,
                )
            else:
                record.payload_preview = False

    @api.model
    def _get_support_endpoint(self):
        """Return the support endpoint URL from config, or the default."""
        endpoint = self.env['ir.config_parameter'].sudo().get_str(
            SUPPORT_ENDPOINT_PARAM)
        return (endpoint or '').strip() or DEFAULT_SUPPORT_ENDPOINT

    @api.model
    def _get_tracking_url(self):
        """Public /track-ticket URL on the same host as the support endpoint."""
        parts = urlsplit(self._get_support_endpoint())
        if parts.scheme and parts.netloc:
            return '%s://%s/track-ticket' % (parts.scheme, parts.netloc)
        return 'https://support.cybrosys.com/track-ticket'

    def _submit_support_request(self):
        self.ensure_one()
        response = requests.post(
            self._get_support_endpoint(),
            json=self._build_payload(),
            timeout=SUPPORT_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def confirm_button(self):
        """Submit the ticket to Cybrosys support."""
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
                raise ValidationError(self.env._(
                    "Your attachments are too large. "
                    "Please reduce their size and try again."
                )) from None
            if status_code >= 500:
                raise ValidationError(self.env._(
                    "The support service is having issues. "
                    "Please try again in a few minutes."
                )) from None
            raise ValidationError(self.env._(
                "The ticket submission was rejected. "
                "Please check your inputs and try again."
            )) from None
        except (requests.ConnectionError, requests.Timeout):
            _logger.exception(
                "Support submission failed due to a network error")
            raise ValidationError(self.env._(
                "Could not reach the support service. "
                "Please check your network and try again."
            )) from None
        except (json.JSONDecodeError, ValueError):
            _logger.exception(
                "Support service returned an invalid response")
            raise ValidationError(self.env._(
                "The support service returned an unexpected response. "
                "Please try again later."
            )) from None

        if response_status.get('result', {}).get('message') == 'success':
            result = response_status.get('result', {})
            ticket_id = result.get('ticket_id') or ''
            support_type_label = dict(
                self._fields['support_type'].selection
            ).get(self.support_type, '')
            priority_label = dict(
                self._fields['priority'].selection
            ).get(self.priority, '')

            # Newlines render as line breaks because the matching CSS rule
            # applies white-space: pre-line. The final "%s" is replaced by a
            # clickable tracking link by the display_notification action.
            track_url = self._get_tracking_url()
            lines = [
                self.env._("Your ticket has been created successfully."), '']
            if ticket_id:
                lines.append(self.env._("Ticket Reference: %s", ticket_id))
            lines.extend([
                '',
                self.env._("Save this reference to follow up with Cybrosys."),
                '',
                self.env._("Track your ticket status here: %s"),
            ])
            message = '\n'.join(lines)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'links': [{'label': track_url, 'url': track_url}],
                    'type': 'success',
                    'sticky': True,
                    'className': 'o_cybrosys_ticket_notification',
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        raise ValidationError(
            self.env._(
                "The ticket submission did not go through. Please try again.")
        )

    def whatsapp_button(self):
        """Open a WhatsApp chat with the support details."""
        self.ensure_one()
        message = "{name}\n{email}\n{description}".format(
            name=self.name or '',
            email=self.email or '',
            description=self.description or '',
        )
        # wa.me requires the number in full international format with digits
        # only — no '+', spaces or dashes.
        phone_number = '919074270811'
        return {
            'type': 'ir.actions.act_url',
            'url': f"https://wa.me/{phone_number}?text={quote(message)}",
            'target': 'new',
        }
