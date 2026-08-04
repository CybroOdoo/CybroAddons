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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import json
import logging
import urllib.request
import urllib.error
import urllib.parse

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SmartLeadCapture(models.Model):
    """Extend CRM leads with Smart Lead Capture integrations."""
    _inherit = 'crm.lead'

    lead_source_channel = fields.Char(
        string='Lead Source Channel',
        default='manual',
        help='Identifies how this lead was created: google_form, webhook, manual',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create leads and trigger outbound webhook notifications."""
        records = super().create(vals_list)
        for record in records:
            _logger.info("SMART LEAD CAPTURE — lead created: %s (ID: %s)",
                         record.name, record.id)
            record._trigger_outbound_webhook(event="lead.created")
        return records

    def write(self, vals):
        """Update leads and trigger outbound webhook notifications."""
        result = super().write(vals)
        for record in self:
            record._trigger_outbound_webhook(event="lead.updated")
        return result

    def send_lead_email_notification(self):
        """Send lead assignment email notifications to salespersons."""
        for lead in self:
            salesperson = lead.user_id
            if not salesperson or not salesperson.email:
                _logger.warning(
                    "Email notification skipped — no salesperson or email on lead %s",
                    lead.id
                )
                continue

            subject = f"New Lead Assigned: {lead.name}"
            body = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #875A7B;">New Lead Assigned to You</h2>
                    <hr/>
                    <table style="width:100%; border-collapse:collapse;">
                        <tr>
                            <td style="padding:8px; font-weight:bold; width:150px;">Lead Name</td>
                            <td style="padding:8px;">{lead.name or '-'}</td>
                        </tr>
                        <tr style="background:#f9f9f9;">
                            <td style="padding:8px; font-weight:bold;">Contact</td>
                            <td style="padding:8px;">{lead.contact_name or '-'}</td>
                        </tr>
                        <tr>
                            <td style="padding:8px; font-weight:bold;">Email</td>
                            <td style="padding:8px;">{lead.email_from or '-'}</td>
                        </tr>
                        <tr style="background:#f9f9f9;">
                            <td style="padding:8px; font-weight:bold;">Phone</td>
                            <td style="padding:8px;">{lead.phone or '-'}</td>
                        </tr>
                        <tr>
                            <td style="padding:8px; font-weight:bold;">Company</td>
                            <td style="padding:8px;">{lead.partner_name or '-'}</td>
                        </tr>
                        <tr style="background:#f9f9f9;">
                            <td style="padding:8px; font-weight:bold;">Expected Revenue</td>
                            <td style="padding:8px;">${lead.expected_revenue or 0}</td>
                        </tr>
                        <tr>
                            <td style="padding:8px; font-weight:bold;">Source</td>
                            <td style="padding:8px;">{lead.lead_source_channel or 'Unknown'}</td>
                        </tr>
                    </table>
                    <hr/>
                    <p style="color:#666;">
                        This lead was automatically captured via Smart Lead Capture.
                        <br/>
                        Please follow up as soon as possible.
                    </p>
                </div>
            """
            lead.message_notify(
                partner_ids=[salesperson.partner_id.id],
                subject=subject,
                body=body,
            )

            _logger.info(
                "Email notification sent to %s (%s) for lead: %s",
                salesperson.name, salesperson.email, lead.name
            )

    def send_whatsapp_notification(self):
        """Send WhatsApp notifications for newly captured leads."""
        ICP = self.env['ir.config_parameter'].sudo()

        account_sid = ICP.get_param('smart_lead_capture.twilio_account_sid', '')
        auth_token  = ICP.get_param('smart_lead_capture.twilio_auth_token', '')
        from_number = ICP.get_param('smart_lead_capture.twilio_whatsapp_from', '')
        to_number   = ICP.get_param('smart_lead_capture.whatsapp_notify_number', '')

        _logger.info(
            "WhatsApp config — SID: %s | From: %s | To: %s",
            account_sid[:10] + '...' if account_sid else 'NOT SET',
            from_number or 'NOT SET',
            to_number or 'NOT SET',
        )

        if not all([account_sid, auth_token, from_number, to_number]):
            _logger.warning(
                "WhatsApp notification skipped — Twilio credentials not fully configured."
            )
            return

        for lead in self:
            message = (
                f"🔔 *New Lead Captured!*\n\n"
                f"👤 *Name:* {lead.contact_name or lead.name}\n"
                f"📧 *Email:* {lead.email_from or 'N/A'}\n"
                f"📞 *Phone:* {lead.phone or 'N/A'}\n"
                f"🏢 *Company:* {lead.partner_name or 'N/A'}\n"
                f"💰 *Budget:* ${lead.expected_revenue or 0}\n"
                f"👨‍💼 *Assigned to:* {lead.user_id.name if lead.user_id else 'Unassigned'}\n\n"
                f"📋 *Source:* {lead.lead_source_channel or 'Unknown'}"
            )

            self._send_twilio_whatsapp(
                account_sid, auth_token,
                from_number, to_number,
                message, lead
            )

    def _send_twilio_whatsapp(self, account_sid, auth_token,
                               from_number, to_number, message, lead):
        """Send a WhatsApp message using the Twilio API."""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

            data = urllib.parse.urlencode({
                'From': from_number,
                'To'  : to_number,
                'Body': message,
            }).encode('utf-8')

            credentials = base64.b64encode(
                f"{account_sid}:{auth_token}".encode('utf-8')
            ).decode('utf-8')

            req = urllib.request.Request(
                url, data=data,
                headers={
                    'Authorization': f'Basic {credentials}',
                    'Content-Type' : 'application/x-www-form-urlencoded',
                },
                method='POST',
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                _logger.info(
                    "WhatsApp notification sent for lead %s — SID: %s",
                    lead.id, result.get('sid', 'unknown')
                )

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            _logger.error(
                "Twilio HTTP error for lead %s — status: %s | body: %s",
                lead.id, e.code, error_body
            )
        except Exception as e:
            _logger.error(
                "WhatsApp notification failed for lead %s: %s",
                lead.id, e, exc_info=True
            )

    def _trigger_outbound_webhook(self, event="lead.saved"):
        """Send lead data to the configured outbound webhook endpoint."""
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('smart_lead_capture.outbound_webhook_url', '')

        # Skip if not configured or points to localhost/self
        if not url:
            return
        if 'your-unique-id' in url:
            return
        if url.startswith('http://localhost') or url.startswith('http://127'):
            _logger.warning("Outbound webhook URL points to localhost — skipping.")
            return
        if not url.startswith('http'):
            _logger.warning("Outbound webhook URL invalid: %s — skipping.", url)
            return

        for lead in self:
            payload = {
                "event"            : event,
                "lead_id"          : lead.id,
                "name"             : lead.name or "",
                "type"             : lead.type or "lead",
                "stage"            : lead.stage_id.name if lead.stage_id else None,
                "probability"      : lead.probability,
                "expected_revenue" : lead.expected_revenue,
                "contact_name"     : lead.contact_name or "",
                "email_from"       : lead.email_from or "",
                "phone"            : lead.phone or "",
                "partner_name"     : lead.partner_name or "",
                "user_name"        : lead.user_id.name if lead.user_id else None,
                "team_name"        : lead.team_id.name if lead.team_id else None,
                "source_channel"   : lead.lead_source_channel or "",
                "write_date"       : str(lead.write_date) if lead.write_date else None,
            }
            self._post_webhook(url, payload, lead.id)

    def _post_webhook(self, url, payload, lead_id):
        """Post lead payload data to an external webhook URL."""
        try:
            data = json.dumps(payload, default=str).encode('utf-8')
            req = urllib.request.Request(
                url, data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent'  : 'SmartLeadCapture/18.0',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                _logger.info(
                    "Outbound webhook delivered for lead %s — HTTP %s",
                    lead_id, response.status
                )
        except urllib.error.URLError as e:
            _logger.error("Outbound webhook failed for lead %s: %s", lead_id, e.reason)
        except Exception as e:
            _logger.error("Outbound webhook error for lead %s: %s", lead_id, e)
