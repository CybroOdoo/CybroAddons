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
import logging
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SmartLeadCaptureController(http.Controller):
    """Smart lead capture controller"""

    @http.route('/webhook/google-form',
                auth='public', csrf=False, methods=['POST'])
    def google_form_webhook(self):
        """
        Receives Google Form data and:
        1. Detects duplicates by email AND phone
        2. Creates new lead or updates existing
        3. Auto-assigns to configured salesperson
        4. Sends email notification to salesperson
        5. Sends WhatsApp notification via Twilio
        """
        try:
            raw_data = request.httprequest.data
            if not raw_data:
                return request.make_json_response(
                    {"status": "error", "message": "Empty request body"},
                    status=400
                )
            payload = json.loads(raw_data.decode('utf-8'))
            _logger.info("Payload: %s", json.dumps(payload, indent=2))
            email     = payload.get('email', '').strip()
            phone     = payload.get('phone', '').strip()
            full_name = payload.get('full_name', '').strip()
            if not email and not phone and not full_name:
                return request.make_json_response(
                    {"status": "error",
                     "message": "At least one of email, phone, or full_name is required"},
                    status=400
                )

            # Step 1 — Duplicate detection
            existing_lead, matched_by = self._find_existing_lead(email, phone)

            if existing_lead:
                # UPDATE existing lead
                self._update_existing_lead(existing_lead, payload)
                _logger.info(
                    "DUPLICATE detected via %s — updated lead ID: %s",
                    matched_by, existing_lead.id
                )
                return request.make_json_response({
                    "status"     : "success",
                    "action"     : "updated",
                    "matched_by" : matched_by,
                    "message"    : f"Existing lead found by {matched_by} and updated",
                    "lead_id"    : existing_lead.id,
                    "lead_name"  : existing_lead.name,
                })

            # Step 2 — Get configured salesperson
            salesperson_id = self._get_default_salesperson_id()

            # Step 3 — Create new lead
            # Odoo's built-in "You have been assigned" email fires
            # automatically — no custom email needed
            new_lead = self._create_new_lead(payload, salesperson_id)

            # Step 4 — Send WhatsApp notification
            new_lead.send_whatsapp_notification()

            _logger.info(
                "NEW LEAD created — ID: %s | Name: %s | Assigned to: %s",
                new_lead.id, new_lead.name,
                new_lead.user_id.name if new_lead.user_id else 'Unassigned'
            )

            return request.make_json_response({
                "status"      : "success",
                "action"      : "created",
                "message"     : "New lead created successfully",
                "lead_id"     : new_lead.id,
                "lead_name"   : new_lead.name,
                "assigned_to" : new_lead.user_id.name if new_lead.user_id else None,
            })

        except json.JSONDecodeError:
            _logger.error("Invalid JSON in Smart Lead Capture request")
            return request.make_json_response(
                {"status": "error", "message": "Invalid JSON format"},
                status=400
            )
        except Exception as e:
            _logger.error("Smart Lead Capture error: %s", e, exc_info=True)
            return request.make_json_response(
                {"status": "error", "message": str(e)},
                status=500
            )

    def _find_existing_lead(self, email, phone):
        """
        Search for existing lead.
        Priority: Email → Phone → None
        Returns (lead, matched_by) or (None, None)
        """
        # Check by email first (most reliable)
        if email:
            lead = request.env['crm.lead'].sudo().search(
                [('email_from', '=', email), ('active', '=', True)],
                limit=1
            )
            if lead:
                _logger.info("Duplicate by EMAIL: %s → Lead ID %s", email, lead.id)
                return lead, 'email'

        # Check by phone
        if phone:
            clean_phone = phone.replace(' ', '').replace('-', '')
            lead = request.env['crm.lead'].sudo().search(
                ['|', ('phone', '=', phone), ('phone', '=', clean_phone),
                 ('active', '=', True)],
                limit=1
            )
            if lead:
                _logger.info("Duplicate by PHONE: %s → Lead ID %s", phone, lead.id)
                return lead, 'phone'

        _logger.info("No duplicate found — will create new lead")
        return None, None

    def _get_default_salesperson_id(self):
        """
            Retrieve the default salesperson configured in system settings.

            Reads the salesperson ID from ir.config_parameter and validates
            that the corresponding user exists.

            Returns:
                int | bool: User ID of the configured salesperson if found,
                otherwise False.
        """
        ICP = request.env['ir.config_parameter'].sudo()
        salesperson_id = ICP.get_param(
            'smart_lead_capture.default_salesperson_id', False
        )
        if salesperson_id:
            try:
                salesperson = request.env['res.users'].sudo().browse(
                    int(salesperson_id)
                )
                if salesperson.exists():
                    _logger.info("Default salesperson: %s", salesperson.name)
                    return salesperson.id
                else:
                    _logger.warning("Configured salesperson ID %s not found", salesperson_id)
            except Exception as e:
                _logger.error("Error getting salesperson: %s", e)
        else:
            _logger.info("No default salesperson configured")
        return False

    def _create_new_lead(self, payload, salesperson_id=False):
        """
            Create a new CRM opportunity from webhook payload data.

            Extracts lead information from the submitted form, builds
            the lead description, links an existing partner if available,
            assigns the configured salesperson, and creates the CRM lead.

            Args:
                payload (dict): Incoming form submission data.
                salesperson_id (int | bool): User ID of the salesperson
                    to assign.

            Returns:
                crm.lead: Newly created CRM lead record.
        """
        full_name = payload.get('full_name', '').strip()
        email     = payload.get('email', '').strip()
        phone     = payload.get('phone', '').strip()
        company   = payload.get('company', '').strip()
        product   = payload.get('product_interest', '').strip()
        budget    = payload.get('budget', '').strip()

        lead_name = full_name if full_name else "New Lead from Google Form"
        if product:
            lead_name += f" — {product}"

        description = self._build_description(payload)

        # Find existing partner by email
        partner_id = False
        if email:
            partner = request.env['res.partner'].sudo().search(
                [('email', '=', email)], limit=1
            )
            if partner:
                partner_id = partner.id

        lead_vals = {
            'name'                : lead_name,
            'contact_name'        : full_name,
            'email_from'          : email,
            'phone'               : phone,
            'partner_name'        : company,
            'description'         : description,
            'type'                : 'opportunity',
            'lead_source_channel' : 'google_form',
        }

        if partner_id:
            lead_vals['partner_id'] = partner_id

        if salesperson_id:
            lead_vals['user_id'] = salesperson_id

        if budget:
            try:
                lead_vals['expected_revenue'] = float(
                    budget.replace(',', '').replace('$', '').replace('€', '').strip()
                )
            except ValueError:
                pass

        return request.env['crm.lead'].sudo().create(lead_vals)

    def _update_existing_lead(self, lead, payload):
        """
            Update an existing lead with information from a new submission.

            Missing lead fields are populated when available, and any new
            message content is appended to the existing description to
            preserve submission history.

            Args:
                lead (crm.lead): Existing lead record.
                payload (dict): Incoming form submission data.

            Returns:
                crm.lead: Updated lead record.
        """
        phone   = payload.get('phone', '').strip()
        company = payload.get('company', '').strip()
        message = payload.get('message', '').strip()
        budget  = payload.get('budget', '').strip()
        email   = payload.get('email', '').strip()

        update_vals = {}

        # Fill missing fields only
        if email and not lead.email_from:
            update_vals['email_from'] = email
        if phone and not lead.phone:
            update_vals['phone'] = phone
        if company and not lead.partner_name:
            update_vals['partner_name'] = company

        # Always append new message
        if message:
            existing = lead.description or ''
            update_vals['description'] = (
                existing + f"\n\n--- New submission ---\n{message}"
            ).strip()

        if budget:
            try:
                update_vals['expected_revenue'] = float(
                    budget.replace(',', '').replace('$', '').replace('€', '').strip()
                )
            except ValueError:
                pass
        if update_vals:
            lead.sudo().write(update_vals)
        return lead

    def _build_description(self, payload):
        """
        Build a styled HTML description for the Internal Notes field.
        Renders as a clean table inside the CRM lead form.
        """
        field_labels = {
            'full_name'        : 'Name',
            'email'            : 'Email',
            'phone'            : 'Phone',
            'company'          : 'Company',
            'product_interest' : 'Product Interest',
            'budget'           : 'Budget',
            'message'          : 'Message',
        }

        rows = ""
        for i, (key, label) in enumerate(field_labels.items()):
            value = payload.get(key, '').strip()
            if not value:
                continue
            bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            rows += f"""
                <tr style="background:{bg};">
                    <td style="padding:8px 12px; font-weight:600; color:#555;
                               width:160px; border:1px solid #e0e0e0;">
                        {label}
                    </td>
                    <td style="padding:8px 12px; color:#333;
                               border:1px solid #e0e0e0;">
                        {value}
                    </td>
                </tr>"""

        # Extra fields Zapier might send
        known = set(field_labels.keys())
        for key, value in payload.items():
            if key not in known and value:
                label = key.replace('_', ' ').title()
                rows += f"""
                <tr style="background:#fff;">
                    <td style="padding:8px 12px; font-weight:600; color:#555;
                               width:160px; border:1px solid #e0e0e0;">
                        {label}
                    </td>
                    <td style="padding:8px 12px; color:#333;
                               border:1px solid #e0e0e0;">
                        {value}
                    </td>
                </tr>"""

        html = f"""
        <div style="font-family:Arial, sans-serif; margin:8px 0;">
            <div style="background:#875A7B; color:#fff; padding:8px 12px;
                        border-radius:4px 4px 0 0; font-weight:bold; font-size:13px;">
                📋 Google Form Submission
            </div>
            <table style="width:100%; border-collapse:collapse;
                          border:1px solid #e0e0e0; border-top:none;">
                {rows}
            </table>
        </div>
        """
        return html

    @http.route(['/webhook/test', '/webhook/receive'],
                auth='public', csrf=False, methods=['POST', 'GET'])
    def webhook_receive(self):
        """
            Generic webhook endpoint for testing and legacy integrations.

            Routes incoming webhook events to their respective handlers
            based on the event type provided in the payload.

            Supported event types:
                - lead.update
                - ai.prediction
                - payment.confirmed

            Returns:
                werkzeug.wrappers.Response: JSON response indicating
                success or failure.
        """
        try:
            raw_data = request.httprequest.data
            payload  = json.loads(raw_data.decode('utf-8')) if raw_data else {}
            event    = payload.get('type', 'unknown')

            _logger.info("WEBHOOK — type: %s", event)

            if event == 'lead.update':
                return self._handle_lead_update(payload)
            elif event == 'ai.prediction':
                return self._handle_ai_prediction(payload)
            elif event == 'payment.confirmed':
                return self._handle_payment(payload)
            else:
                return request.make_json_response({
                    "status": "success",
                    "message": "Webhook received",
                    "type": event,
                    "data": payload,
                })
        except json.JSONDecodeError:
            return request.make_json_response(
                {"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return request.make_json_response(
                {"status": "error", "message": str(e)}, status=500)

    def _handle_lead_update(self, payload):
        """
            Process lead update webhook events.

            Updates selected CRM lead fields such as probability,
            expected revenue, description, name, and priority.

            Args:
                payload (dict): Webhook payload containing lead update data.

            Returns:
                werkzeug.wrappers.Response: JSON response containing the
                update result.
        """
        try:
            lead_id = payload.get('lead_id')
            if not lead_id:
                return request.make_json_response(
                    {"status": "error", "message": "lead_id is required"}, status=400)
            lead = request.env['crm.lead'].sudo().browse(int(lead_id))
            if not lead.exists():
                return request.make_json_response(
                    {"status": "error", "message": f"Lead {lead_id} not found"}, status=404)
            allowed = {
                'probability': float, 'expected_revenue': float,
                'description': str, 'name': str, 'priority': str,
            }
            update_data = {f: cast(payload[f]) for f, cast in allowed.items() if f in payload}
            if update_data:
                lead.write(update_data)
            return request.make_json_response({
                "status": "success",
                "message": "Lead updated",
                "lead_id": lead_id,
                "updated_fields": update_data,
            })
        except Exception as e:
            return request.make_json_response(
                {"status": "error", "message": str(e)}, status=500)

    def _handle_ai_prediction(self, payload):
        """
            Apply AI-generated prediction data to a CRM lead.

            Updates the lead probability and expected revenue using
            values received from an external AI prediction service.

            Args:
                payload (dict): Webhook payload containing prediction data.

            Returns:
                werkzeug.wrappers.Response: JSON response indicating whether
                the prediction was successfully applied.
        """
        try:
            lead_id = payload.get('lead_id')
            if not lead_id:
                return request.make_json_response(
                    {"status": "error", "message": "lead_id is required"}, status=400)
            lead = request.env['crm.lead'].sudo().browse(int(lead_id))
            if not lead.exists():
                return request.make_json_response(
                    {"status": "error", "message": f"Lead {lead_id} not found"}, status=404)
            score = float(payload.get('score', 0))
            predicted = float(payload.get('predicted_value', 0))
            lead.write({'probability': score * 100, 'expected_revenue': predicted})
            return request.make_json_response({
                "status": "success", "message": "AI prediction applied",
                "lead_id": lead_id, "score": score, "predicted_value": predicted,
            })
        except Exception as e:
            return request.make_json_response(
                {"status": "error", "message": str(e)}, status=500)

    def _handle_payment(self, payload):
        """
            Process payment confirmation webhook events.

            Validates the payment reference and returns a confirmation
            response for integrations that notify Odoo about completed
            payments.

            Args:
                payload (dict): Webhook payload containing payment details.

            Returns:
                werkzeug.wrappers.Response: JSON response indicating whether
                the payment notification was processed successfully.
        """
        try:
            reference = payload.get('reference')
            if not reference:
                return request.make_json_response(
                    {"status": "error", "message": "reference is required"}, status=400)
            return request.make_json_response({
                "status": "success", "message": "Payment received",
                "reference": reference, "amount": payload.get('amount'),
            })
        except Exception as e:
            return request.make_json_response(
                {"status": "error", "message": str(e)}, status=500)
