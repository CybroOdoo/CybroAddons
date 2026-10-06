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
import json
import logging
import urllib.request
import urllib.error

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SmartLeadCapture(models.Model):
    """Extends ``crm.lead`` with Smart Lead Capture behaviour.

    Adds a ``lead_source_channel`` tracking field and, on every
    create/write, fires an outbound webhook so external systems (Zapier,
    Google Apps Script, custom dashboards, etc.) can stay in sync with
    Odoo CRM leads. Also provides the email and WhatsApp notification
    helpers used by the inbound Google Form webhook controller.
    """
    _inherit = 'crm.lead'

    lead_source_channel = fields.Char(
        string='Lead Source Channel',
        default='manual',
        help='Identifies how this lead was created: google_form, webhook, manual',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create lead(s) and trigger the ``lead.created`` outbound webhook.

        Args:
            vals_list (list[dict]): List of value dictionaries for the
                lead(s) being created.

        Returns:
            crm.lead: The newly created lead record(s).
        """
        records = super().create(vals_list)
        for record in records:
            record._trigger_outbound_webhook(event="lead.created")
        return records

    def write(self, vals):
        """Update lead(s) and trigger the ``lead.updated`` outbound webhook.

        Args:
            vals (dict): Values to write to the lead(s).

        Returns:
            bool: Result of the underlying ``write()`` call.
        """
        result = super().write(vals)
        for record in self:
            record._trigger_outbound_webhook(event="lead.updated")
        return result

    def send_lead_email_notification(self):
        """Notify the assigned salesperson by email that a lead is theirs.

        Builds an HTML summary of the lead and sends it via
        ``message_notify()``. Skips silently (with a warning logged) for
        any lead that has no assigned salesperson or no email on file.
        """
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

            # FIX: removed message_type — not supported in Odoo 18 message_notify()
            lead.message_notify(
                partner_ids=[salesperson.partner_id.id],
                subject=subject,
                body=body,
            )

    def send_whatsapp_notification(self):
        """Notify a configured WhatsApp number about newly captured leads.

        Reads Twilio credentials from ``ir.config_parameter``. If any
        credential is missing, the notification is skipped with a warning
        logged. Otherwise, builds a formatted WhatsApp message per lead and
        sends it via the Twilio API.
        """
        ICP = self.env['ir.config_parameter'].sudo()

        account_sid = ICP.get_param('smart_lead_capture.twilio_account_sid', '')
        auth_token  = ICP.get_param('smart_lead_capture.twilio_auth_token', '')
        from_number = ICP.get_param('smart_lead_capture.twilio_whatsapp_from', '')
        to_number   = ICP.get_param('smart_lead_capture.whatsapp_notify_number', '')

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
        """Send a single WhatsApp message through the Twilio REST API.

        Args:
            account_sid (str): Twilio Account SID.
            auth_token (str): Twilio Auth Token.
            from_number (str): Twilio WhatsApp sender, e.g.
                ``whatsapp:+14155238886``.
            to_number (str): Destination WhatsApp number, e.g.
                ``whatsapp:+919876543210``.
            message (str): Message body to send.
            lead (crm.lead): Lead the notification relates to, used for
                logging context.
        """
        import base64
        import urllib.parse

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
                json.loads(response.read().decode('utf-8'))

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
        """Build the outbound webhook payload for each lead and send it.

        Reads the target URL from ``ir.config_parameter``
        (``smart_lead_capture.outbound_webhook_url``) and skips sending
        when it is unconfigured, still set to the placeholder value, or
        points at localhost (self-loop guard).

        Args:
            event (str): Event name to include in the payload, e.g.
                ``"lead.created"`` or ``"lead.updated"``.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('smart_lead_capture.outbound_webhook_url', '')

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
        """POST a JSON payload to the configured outbound webhook URL.

        Args:
            url (str): Destination webhook URL.
            payload (dict): JSON-serializable payload to send.
            lead_id (int): ID of the lead the payload relates to, used for
                logging context.
        """
        try:
            data = json.dumps(payload, default=str).encode('utf-8')
            req = urllib.request.Request(
                url, data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent'  : 'SmartLeadCapture/17.0',
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