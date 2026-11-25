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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import hmac
import json
import logging
import re
from odoo import http
from odoo.fields import Command
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class JsonResponse(Response):
    """HTTP JSON response that also acts like a dict for direct unit test access."""
    def __init__(self, data, status=200):
        self._json_data = data
        super().__init__(
            json.dumps(data),
            status=status,
            content_type='application/json;charset=utf-8'
        )

    def __getitem__(self, key):
        return self._json_data[key]

    def get(self, key, default=None):
        return self._json_data.get(key, default)

    def __contains__(self, key):
        return key in self._json_data


class VapiAssistant(http.Controller):

    def _make_json_response(self, data, status=200):
        """Returns pure JSON HTTP response for Vapi webhooks, compatible with both HTTP runtime and unit test mocks."""
        return JsonResponse(data, status=status)

    def _make_tool_response(self, tool_call_id, result_str, status=200):
        """Constructs and returns a Vapi-compliant tool call result payload."""
        payload = {
            "results": [{
                "toolCallId": tool_call_id or "tool_call",
                "result": result_str,
            }]
        }
        return self._make_json_response(payload, status=status)

    def _verify_webhook_secret(self):
        """Verifies whether the incoming request matches the configured webhook secret."""
        expected_secret = request.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_webhook_secret')
        if not expected_secret or not expected_secret.strip():
            return False
        headers = request.httprequest.headers
        incoming_secret = (
            headers.get('x-vapi-secret') or
            headers.get('X-Vapi-Secret') or
            headers.get('Authorization', '').replace('Bearer ', '').strip() or
            request.httprequest.args.get('token') or
            ''
        ).strip()
        if not incoming_secret:
            return False
        return hmac.compare_digest(incoming_secret, expected_secret.strip())

    def _get_target_user(self, call=None, data=None, assistant=None):
        """Resolves the authorized internal user record that initiated the voice session,
        preventing broadcast over public or unauthenticated bus channels."""
        call = call or {}
        data = data or {}
        assistant_overrides = call.get('assistantOverrides') or {}
        var_values = assistant_overrides.get('variableValues') or call.get('variableValues') or {}
        metadata = call.get('metadata') or data.get('metadata') or {}

        user_id = (
            var_values.get('user_id') or
            var_values.get('salesperson_id') or
            metadata.get('user_id') or
            metadata.get('salesperson_id') or
            request.params.get('user_id') or
            request.params.get('salesperson_id')
        )
        if user_id:
            try:
                user = request.env['res.users'].sudo().browse(int(user_id))
                if user.exists() and not user._is_public():
                    return user
            except (ValueError, TypeError) as err:
                _logger.debug("Unable to parse user_id '%s': %s", user_id, err)

        # Fallback 1: User that created or owns the assistant record
        if assistant and assistant.create_uid and assistant.create_uid.exists() and not assistant.create_uid._is_public():
            return assistant.create_uid

        # Fallback 2: Authenticated request user (if present in session)
        if request.env.user and not request.env.user._is_public() and request.env.user.id != 1:
            return request.env.user

        # Fallback 3: Active system administrator or internal voice assistant user
        admin = request.env.ref('base.user_admin', raise_if_not_found=False)
        if admin and admin.exists():
            return admin
        company_id = assistant.company_id.id if assistant and assistant.company_id else False
        return request.env['res.users'].sudo().search([
            ('share', '=', False),
            ('company_id', 'in', [False, company_id])
        ], limit=1)

    def _send_bus_notification(self, target_user, payload):
        """Safely dispatches a secure bus notification targeted to the specific user record.
        Anonymous visitors and unauthorized users cannot subscribe to or inspect these notifications."""
        if not target_user:
            return
        try:
            request.env["bus.bus"]._sendone(
                target_user,
                "ora_ai_base/voice_notification",
                payload
            )
        except Exception as err:
            _logger.debug("Failed sending secure targeted bus notification: %s", err)


    def _parse_request_data(self):
        """Safely parses JSON payload from http request."""
        parsed = {}
        try:
            parsed = request.httprequest.get_json(silent=True) or request.get_json_data() or {}
        except Exception:
            try:
                raw = request.httprequest.data
                parsed = json.loads(raw) if raw else {}
            except Exception:
                parsed = {}
        if isinstance(parsed, dict) and 'params' in parsed and isinstance(parsed['params'], dict) and 'jsonrpc' in parsed:
            return parsed['params']
        return parsed or request.params or {}

    def _link_call_history(self, vapi_call_id, values, assistant=False, call_type='webCall'):
        """Safely links or updates created records (sale order, invoice, customer, product)
        in the matching ora.call.history record."""
        if not vapi_call_id:
            return False
        try:
            call_record = request.env['ora.call.history'].sudo().search(
                [('vapi_call_id', '=', vapi_call_id)], limit=1)
            history_vals = dict(values)
            if assistant:
                history_vals.setdefault('assistant_id', assistant.id)
            if call_record:
                call_record.write(history_vals)
                return call_record
            else:
                history_vals.update({
                    'name': f"Call-{vapi_call_id[:8]}" if vapi_call_id else "Call",
                    'vapi_call_id': vapi_call_id,
                    'call_type': call_type or 'webCall',
                    'status': 'started',
                })
                return request.env['ora.call.history'].sudo().create(history_vals)
        except Exception as e:
            _logger.warning("Could not link record to ora.call.history (%s): %s", vapi_call_id, e)
            return False

    def _extract_tool_call(self, data, default_id="tool_call"):
        """Extracts tool_call_id and parsed arguments dict from Vapi webhook payload."""
        message = data.get('message', {})
        tool_call_list = message.get('toolCalls') or message.get('toolCallList') or message.get('tool_calls') or data.get('toolCalls') or []
        tool_call = tool_call_list[0] if tool_call_list else {}
        tool_call_id = tool_call.get('id', default_id)
        arguments = tool_call.get('function', {}).get('arguments', {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                arguments = {}
        if not arguments and 'parameters' in tool_call.get('function', {}):
            arguments = tool_call['function']['parameters']
        if not arguments:
            arguments = data.get('arguments') or data.get('parameters') or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception:
                    arguments = {}
        return tool_call_id, arguments or {}

    def _find_customer_by_name(self, clean_name, company_id=False, env=None):
        """Searches for an existing partner by exact or partial name within company scope."""
        if env is None:
            env = request.env
        if not clean_name:
            return env['res.partner']
        Partner = env['res.partner'].sudo()
        domain = [('name', '=ilike', clean_name)]
        if company_id:
            domain += ['|', ('company_id', '=', False), ('company_id', '=', company_id)]
        partner = Partner.search(domain, limit=1)
        if not partner:
            domain[0] = ('name', 'ilike', clean_name)
            partner = Partner.search(domain, limit=1)
        if not partner and len(clean_name.split()) > 1:
            domain[0] = ('name', 'ilike', clean_name.split()[0])
            partner = Partner.search(domain, limit=1)
        return partner

    @http.route('/vapi_voice_assistant/details', type='http',
                auth='public', csrf=False, methods=['POST'])
    def final_details(self, **kwargs):
        """Processes final order details received from the voice assistant
         and creates a Sale Order in Odoo for both telephone and web calls."""
        if not self._verify_webhook_secret():
            _logger.warning("Unauthorized Vapi webhook request: invalid secret")
            return self._make_json_response({"error": "Unauthorized"}, status=401)

        try:
            data = self._parse_request_data()
            message_data = data.get('message', {})
            call = message_data.get('call', {}) or data.get('call', {})
            call_type = call.get('type') or 'webCall'
            vapi_call_id = call.get('id') or data.get('call_id')
            assistant_vapi_id = call.get('assistantId')
            assistant = False
            if assistant_vapi_id:
                assistant = request.env['ora.ai'].sudo().search(
                    [('id_assistant', '=', assistant_vapi_id)], limit=1)

            tool_call_id, arguments = self._extract_tool_call(data, default_id="tool_call_order")

            if assistant and not assistant.is_sale_order_creation:
                return self._make_tool_response(
                    tool_call_id,
                    "Sale Order Creation is currently disabled for this assistant."
                )

            pr_list = []
            customer_name = ""
            order_details = arguments.get('OrderDetails', {}) if isinstance(arguments, dict) else {}
            details = order_details.get('Products', []) if isinstance(order_details, dict) else []
            for rec in details:
                pr_list.append({
                    "customer": rec.get('Customer', ''),
                    "product": rec.get('Product', ''),
                    "id": rec.get('productId'),
                    "qty": rec.get('Quantity', 1),
                    "variant": rec.get('Variant', '-')
                })
                if rec.get('Customer'):
                    customer_name = rec.get('Customer')
            if not customer_name:
                customer_name = order_details.get('Customer') or arguments.get('Customer') or ''

            # Broadcast live order details securely to the initiating user's component
            target_user = self._get_target_user(call=call, data=data, assistant=assistant)
            message = {"operation": "sale", "value": pr_list}
            self._send_bus_notification(target_user, message)

            # Check for Test Mode (Skip order and customer creation in test mode)
            assistant_overrides = call.get('assistantOverrides') or {}
            var_values = assistant_overrides.get('variableValues') or call.get('variableValues') or {}
            metadata = call.get('metadata') or data.get('metadata') or {}
            is_test_mode = (
                var_values.get('test_mode') in ('true', True, '1', 1) or
                metadata.get('test_mode') in ('true', True, '1', 1) or
                data.get('test_mode') in ('true', True, '1', 1) or
                request.params.get('test_mode') in ('true', True, '1', 1)
            )

            if is_test_mode:
                _logger.info("Test Mode Call %s: Order details received for configuration test only. No sale order or partner will be created.", vapi_call_id)
                return self._make_tool_response(
                    tool_call_id,
                    "Configuration verified: Order test acknowledged successfully. No order or customer created in test mode."
                )

            # Idempotency check: if an order was already created for this call, do not duplicate
            if vapi_call_id:
                existing_call = request.env['ora.call.history'].sudo().search(
                    [('vapi_call_id', '=', vapi_call_id)], limit=1)
                if existing_call and existing_call.order_id:
                    _logger.info("Order %s already created for call %s",
                                 existing_call.order_id.name, vapi_call_id)
                    return self._make_tool_response(
                        tool_call_id,
                        f"Order {existing_call.order_id.name} already placed."
                    )

            # Filter and validate products
            valid_lines = []
            for item in pr_list:
                pid = item.get('id')
                qty = float(item.get('qty') or 1)
                if not pid or qty <= 0:
                    continue
                product = request.env['product.product'].sudo().browse(pid)
                if product.exists() and product.sale_ok:
                    valid_lines.append(Command.create({
                        'product_id': product.id,
                        'product_uom_qty': qty,
                    }))

            if valid_lines:
                # Customer Identification
                partner = False
                phone_number = call.get('customer', {}).get('number')
                company_id = assistant.company_id.id if assistant and assistant.company_id else False

                selected_partner_id = (
                    order_details.get('partnerId') or
                    order_details.get('partner_id') or
                    arguments.get('partnerId') or
                    arguments.get('partner_id') or
                    var_values.get('partner_id') or
                    var_values.get('customer_id') or
                    metadata.get('partner_id') or
                    metadata.get('customer_id') or
                    request.params.get('partner_id')
                )

                # Strict requirement: only support sale order creation after customer selection
                clean_name = re.sub(r'^[^\w]+|[^\w]+$', '', customer_name).strip() if customer_name else ""
                has_customer_info = bool(selected_partner_id or clean_name or phone_number)
                if not has_customer_info:
                    _logger.warning("Order creation rejected for call %s: Customer selection is required first.", vapi_call_id)
                    return self._make_tool_response(
                        tool_call_id,
                        "Sale order creation is only supported after the customer has been identified or selected. "
                        "Please ask whether this order is for an existing or new customer and get their name."
                    )

                # 1. Use explicitly selected customer if provided
                if selected_partner_id:
                    try:
                        p = request.env['res.partner'].sudo().browse(int(selected_partner_id))
                        if p.exists():
                            partner = p
                    except (ValueError, TypeError):
                        partner = False

                # 2. Match spoken customer name against existing customers; only create if not found
                if not partner and clean_name:
                    domain = [('type', '!=', 'private'), ('name', '=ilike', clean_name)]
                    if company_id:
                        domain = [('company_id', 'in', [False, company_id])] + domain
                    partner = request.env['res.partner'].sudo().search(domain, limit=1)

                    if not partner:
                        sub_domain = [('type', '!=', 'private'), '|', ('name', 'ilike', clean_name), ('display_name', 'ilike', clean_name)]
                        if company_id:
                            sub_domain = [('company_id', 'in', [False, company_id])] + sub_domain
                        partner = request.env['res.partner'].sudo().search(sub_domain, limit=1)

                    if not partner:
                        tokens = [t for t in re.split(r'\s+', clean_name) if len(t) > 2]
                        if len(tokens) > 1:
                            tok_domain = [('type', '!=', 'private')]
                            for tok in tokens:
                                tok_domain.append(('name', 'ilike', tok))
                            if company_id:
                                tok_domain = [('company_id', 'in', [False, company_id])] + tok_domain
                            partner = request.env['res.partner'].sudo().search(tok_domain, limit=1)

                    if not partner:
                        partner = request.env['res.partner'].sudo().create({
                            'name': clean_name,
                            'company_id': company_id or False,
                        })

                # 3. Match by phone number for phone calls
                if not partner and phone_number:
                    p_domain = ['|', ('phone', '=', phone_number), ('mobile', '=', phone_number)]
                    if company_id:
                        p_domain = [('company_id', 'in', [False, company_id])] + p_domain
                    partner = request.env['res.partner'].sudo().search(p_domain, limit=1)
                    if not partner:
                        partner = request.env['res.partner'].sudo().create({
                            'name': f"Voice Customer {phone_number}",
                            'phone': phone_number,
                            'company_id': company_id or False,
                        })

                # 4. Fallback when neither selected nor spoken
                if not partner:
                    if call_type == 'webCall' and request.env.user and not request.env.user._is_public():
                        partner = request.env.user.partner_id
                    else:
                        fallback_name = 'Web Voice Customer' if call_type == 'webCall' else 'Voice Customer'
                        partner = request.env['res.partner'].sudo().search([('name', '=', fallback_name)], limit=1)
                        if not partner:
                            partner = request.env['res.partner'].sudo().create({
                                'name': fallback_name,
                                'company_id': company_id or False,
                            })

                # Salesperson resolution (logged-in user)
                salesperson_id = (
                    order_details.get('salesperson_id') or
                    order_details.get('salespersonId') or
                    order_details.get('user_id') or
                    order_details.get('userId') or
                    arguments.get('salesperson_id') or
                    arguments.get('salespersonId') or
                    arguments.get('user_id') or
                    arguments.get('userId') or
                    var_values.get('salesperson_id') or
                    var_values.get('user_id') or
                    metadata.get('salesperson_id') or
                    metadata.get('user_id') or
                    request.params.get('salesperson_id') or
                    request.params.get('user_id')
                )

                salesperson = False
                if salesperson_id:
                    try:
                        u = request.env['res.users'].sudo().browse(int(salesperson_id))
                        if u.exists():
                            salesperson = u
                    except (ValueError, TypeError):
                        salesperson = False

                # Fallback 1: Dedicated salesperson assigned to the customer in Odoo contacts
                if not salesperson and partner and partner.user_id:
                    salesperson = partner.user_id

                # Fallback 2: Authenticated user (if not public or root)
                if not salesperson and request.env.user and not request.env.user._is_public() and request.env.user.id != 1:
                    salesperson = request.env.user

                # Fallback 3: Assistant creator / configured user
                if not salesperson and assistant and assistant.create_uid:
                    salesperson = assistant.create_uid

                # Fallback 4: Active sales administrator or internal user
                if not salesperson:
                    admin_u = request.env.ref('base.user_admin', raise_if_not_found=False)
                    if admin_u and admin_u.exists():
                        salesperson = admin_u
                    else:
                        company_id = assistant.company_id.id if assistant and assistant.company_id else False
                        salesperson = request.env['res.users'].sudo().search([
                            ('share', '=', False),
                            ('company_id', 'in', [False, company_id])
                        ], limit=1)

                order_vals = {
                    'partner_id': partner.id,
                    'order_line': valid_lines,
                    'origin': f"Voice Assistant ({vapi_call_id[:8]})" if vapi_call_id else "Voice Assistant",
                }
                if salesperson:
                    order_vals['user_id'] = salesperson.id
                if assistant and assistant.company_id:
                    order_vals['company_id'] = assistant.company_id.id
                elif partner.company_id:
                    order_vals['company_id'] = partner.company_id.id

                sales = request.env['sale.order'].sudo().create(order_vals)

                # Check auto-confirm setting
                auto_confirm = request.env['ir.config_parameter'].sudo().get_str(
                    'ora_ai_base.voice_order_auto_confirm') == 'True'
                if auto_confirm:
                    sales.action_confirm()


                # Link order to call history safely
                if vapi_call_id:
                    link_vals = {
                        'order_id': sales.id,
                        'partner_id': partner.id,
                        'company_id': sales.company_id.id,
                    }
                    if salesperson:
                        link_vals['user_id'] = salesperson.id
                    self._link_call_history(
                        vapi_call_id,
                        link_vals,
                        assistant=assistant,
                        call_type=call_type
                    )

                # Broadcast confirmation notification
                self._send_bus_notification(
                    target_user,
                    {
                        "operation": "sale",
                        "state": "success",
                        "value": pr_list,
                        "order_id": sales.id,
                        "order_name": sales.name
                    }
                )

                return self._make_tool_response(
                    tool_call_id,
                    f"Order {sales.name} successfully created with {len(valid_lines)} items for customer {partner.name}."
                )

        except Exception as e:
            _logger.exception("Error processing Vapi final details: %s", e)
            return self._make_tool_response(
                tool_call_id if 'tool_call_id' in locals() else "tool_call_order",
                f"Internal error creating order: {str(e)}",
                status=500
            )

        return self._make_tool_response("tool_call_order", "No valid products found to order.")

    @http.route('/vapi_voice_assistant/status', type='http',
                auth='public', csrf=False, methods=['POST'])
    def get_status(self, **kwargs):
        """Receives status updates from the voice assistant, records call history,
         and broadcasts updates to the bus."""
        if not self._verify_webhook_secret():
            _logger.warning("Unauthorized Vapi status webhook: invalid secret")
            return self._make_json_response({"error": "Unauthorized"}, status=401)

        try:
            data = self._parse_request_data()
            message = data.get('message', {}) if isinstance(data, dict) else {}
            msg_type = message.get('type')

            # Only persist call status on status-update and end-of-call-report
            if msg_type in ('status-update', 'end-of-call-report'):
                request.env['ora.call.history'].sudo().log_call_status(data)

            # Broadcast status securely to the initiating user's component
            call = message.get('call') or data.get('call') or {}
            target_user = self._get_target_user(call=call, data=data)
            message_payload = {"value": data}
            self._send_bus_notification(target_user, message_payload)
            return self._make_json_response({"status": "ok"})
        except Exception as e:
            _logger.exception("Error processing Vapi status: %s", e)
            return self._make_json_response({"error": str(e)}, status=500)

    @http.route('/vapi_voice_assistant/language_details', type='http',
                auth='public', csrf=False, methods=['POST'])
    def get_language_details(self, **kwargs):
        """Processes user language preferences requested by the voice assistant."""
        if not self._verify_webhook_secret():
            _logger.warning("Unauthorized Vapi language webhook: invalid secret")
            return self._make_json_response({"error": "Unauthorized"}, status=401)

        try:
            data = self._parse_request_data()
            message_data = data.get('message', {})
            tool_call_id, arguments = self._extract_tool_call(data, default_id="tool_call_lang")
            pref = arguments.get('LanguagePreference', {}) if isinstance(arguments, dict) else {}
            lang_code = pref.get('LanguageCode', '') or arguments.get('LanguageCode', '')

            result_msg = f"Language preference received: {lang_code}"
            if lang_code:
                # Find matching language in Odoo
                clean_code = lang_code.replace('-', '_')
                matched_lang = request.env['res.lang'].sudo().search(
                    ['|', ('code', '=', clean_code), ('code', '=ilike', f"{clean_code[:2]}%")],
                    limit=1)
                if matched_lang:
                    result_msg = f"Language successfully set to {matched_lang.name} ({matched_lang.code})"
                    # If caller has an identified partner, update user's language preference
                    call = message_data.get('call', {}) or data.get('call', {})
                    phone_number = call.get('customer', {}).get('number')
                    partner = False
                    if phone_number:
                        partner = request.env['res.partner'].sudo().search(
                            ['|', ('phone', '=', phone_number), ('mobile', '=', phone_number)], limit=1)
                    elif request.env.user and not request.env.user._is_public():
                        partner = request.env.user.partner_id
                    if partner:
                        partner.sudo().write({'lang': matched_lang.code})

            return self._make_tool_response(tool_call_id, result_msg)
        except Exception as e:
            _logger.exception("Error processing Vapi language details: %s", e)
            return self._make_tool_response(
                tool_call_id if 'tool_call_id' in locals() else "tool_call_lang",
                f"Error processing language details: {str(e)}",
                status=500
            )

    @http.route('/vapi_voice_assistant/check_customer', type='http',
                auth='public', csrf=False, methods=['POST'])
    def check_customer(self, **kwargs):
        """Checks if a customer name exists in Odoo res.partner for voice assistant."""
        if not self._verify_webhook_secret():
            _logger.warning("Unauthorized Vapi customer check webhook: invalid secret")
            return self._make_json_response({"error": "Unauthorized"}, status=401)

        try:
            data = self._parse_request_data()
            tool_call_id, arguments = self._extract_tool_call(data, default_id="tool_call_check_customer")
            message_data = data.get('message', {})
            call = message_data.get('call', {}) or data.get('call', {})
            assistant_id = call.get('assistantId') or message_data.get('assistantId')
            assistant = request.env['ora.ai'].sudo().search([('id_assistant', '=', assistant_id)], limit=1) if assistant_id else False


            raw_name = (
                arguments.get('customer_name') or
                arguments.get('customer') or
                arguments.get('name') or
                data.get('customer_name') or ""
            )
            # Robust punctuation and whitespace stripping
            clean_name = re.sub(r'^[^\w]+|[^\w]+$', '', raw_name).strip() if raw_name else ""

            if not clean_name:
                return self._make_tool_response(
                    tool_call_id,
                    "No customer name was provided to check. Please ask the user for the customer's name."
                )

            Partner = request.env['res.partner'].sudo()
            partner = Partner.search([
                ('type', '!=', 'private'),
                ('name', '=ilike', clean_name)
            ], limit=1)

            if not partner:
                partner = Partner.search([
                    ('type', '!=', 'private'),
                    '|', ('name', 'ilike', clean_name),
                    ('display_name', 'ilike', clean_name)
                ], limit=1)

            if not partner:
                tokens = [t for t in re.split(r'\s+', clean_name) if len(t) > 2]
                if len(tokens) > 1:
                    tok_domain = [('type', '!=', 'private')]
                    for tok in tokens:
                        tok_domain.append(('name', 'ilike', tok))
                    partner = Partner.search(tok_domain, limit=1)

            if partner:
                # Live sync with Owl frontend dropdown securely
                target_user = self._get_target_user(call=call, data=data, assistant=assistant)
                self._send_bus_notification(
                    target_user,
                    {
                        "type": "customer_selected",
                        "partner_id": partner.id,
                        "partner_name": partner.display_name or partner.name,
                    }
                )

                return self._make_tool_response(
                    tool_call_id,
                    f"Customer '{partner.name}' was FOUND in the existing customer database (ID: {partner.id}). "
                    f"Inform the caller that {partner.name} is verified and ask what products they want to order."
                )
            else:
                return self._make_tool_response(
                    tool_call_id,
                    f"Customer '{clean_name}' was NOT FOUND in the existing customer database. "
                    f"Inform the caller that no existing account was found for '{clean_name}', and ask: "
                    f"'Would you like me to create a new customer account for {clean_name}, or check with another name?'"
                )

        except Exception as e:
            _logger.exception("Error checking customer in Vapi webhook: %s", e)
            return self._make_tool_response(
                tool_call_id if 'tool_call_id' in locals() else "tool_call_check_customer",
                f"Could not verify customer due to an internal error: {str(e)}",
                status=500
            )

    @http.route('/vapi_voice_assistant/create_customer', type='http',
                auth='public', csrf=False, methods=['POST'])
    def create_customer(self, **kwargs):
        """Creates a new customer / contact in Odoo res.partner via voice assistant."""
        if not self._verify_webhook_secret():
            return self._make_json_response({"error": "Unauthorized"}, status=401)
        try:
            data = self._parse_request_data()
            message_data = data.get('message', {})
            call = message_data.get('call', {}) or data.get('call', {})
            assistant_vapi_id = call.get('assistantId')
            assistant = False
            if assistant_vapi_id:
                assistant = request.env['ora.ai'].sudo().search(
                    [('id_assistant', '=', assistant_vapi_id)], limit=1)

            tool_call_id, arguments = self._extract_tool_call(data, default_id="tool_call_customer")

            if assistant and not assistant.is_customer_creation:
                return self._make_tool_response(tool_call_id, "Customer Creation is currently disabled for this assistant.")

            name = (arguments.get('name') or arguments.get('customer_name') or '').strip()
            if not name:
                return self._make_tool_response(tool_call_id, "Customer name is required to create an account.")

            phone = arguments.get('phone') or ''
            email = arguments.get('email') or ''
            company_name = arguments.get('company_name') or ''
            street = arguments.get('street') or ''
            city = arguments.get('city') or ''
            state_name = arguments.get('state') or ''
            country_name = arguments.get('country') or ''
            is_company = bool(arguments.get('is_company'))

            Partner = request.env['res.partner'].sudo()

            state_id = False
            country_id = False
            if country_name:
                country = request.env['res.country'].sudo().search([('name', '=ilike', country_name)], limit=1)
                if country:
                    country_id = country.id
            if state_name:
                state_domain = [('name', '=ilike', state_name)]
                if country_id:
                    state_domain.append(('country_id', '=', country_id))
                state = request.env['res.country.state'].sudo().search(state_domain, limit=1)
                if state:
                    state_id = state.id
                    if not country_id:
                        country_id = state.country_id.id

            vals = {
                'name': name,
                'is_company': is_company,
                'phone': phone or False,
                'email': email or False,
                'street': street or False,
                'city': city or False,
                'state_id': state_id or False,
                'country_id': country_id or False,
                'customer_rank': 1,
            }
            if assistant and assistant.company_id:
                vals['company_id'] = assistant.company_id.id

            partner = Partner.create(vals)

            # Link created customer to call history
            vapi_call_id = call.get('id') or data.get('call_id')
            if vapi_call_id:
                self._link_call_history(
                    vapi_call_id,
                    {'created_partner_id': partner.id, 'partner_id': partner.id},
                    assistant=assistant,
                    call_type=call.get('type') or 'webCall'
                )

            target_user = self._get_target_user(call=call, data=data, assistant=assistant)
            notification = {
                "operation": "customer",
                "state": "success",
                "data": {
                    "name": partner.name,
                    "phone": partner.phone or "",
                    "email": partner.email or "",
                    "company": company_name or "",
                    "street": partner.street or "",
                    "city": partner.city or "",
                    "state": partner.state_id.name if partner.state_id else "",
                    "country": partner.country_id.name if partner.country_id else "",
                    "type": "Company" if partner.is_company else "Individual",
                },
                "record_id": partner.id,
                "record_name": partner.name,
            }
            self._send_bus_notification(target_user, notification)

            return self._make_tool_response(
                tool_call_id,
                f"Customer '{partner.name}' successfully created in Odoo (ID: {partner.id}). Phone: {partner.phone or 'N/A'}, Email: {partner.email or 'N/A'}."
            )
        except Exception as e:
            _logger.exception("Error in create_customer webhook: %s", e)
            return self._make_tool_response(tool_call_id if 'tool_call_id' in locals() else "tool_call_customer", f"Error creating customer: {str(e)}", status=500)

    @http.route('/vapi_voice_assistant/create_product', type='http',
                auth='public', csrf=False, methods=['POST'])
    def create_product(self, **kwargs):
        """Creates a new product in product.template via voice assistant."""
        if not self._verify_webhook_secret():
            return self._make_json_response({"error": "Unauthorized"}, status=401)
        try:
            data = self._parse_request_data()
            message_data = data.get('message', {})
            call = message_data.get('call', {}) or data.get('call', {})
            assistant_vapi_id = call.get('assistantId')
            assistant = False
            if assistant_vapi_id:
                assistant = request.env['ora.ai'].sudo().search(
                    [('id_assistant', '=', assistant_vapi_id)], limit=1)

            tool_call_id, arguments = self._extract_tool_call(data, default_id="tool_call_product")

            if assistant and not assistant.is_product_creation:
                return self._make_tool_response(tool_call_id, "Product Creation is currently disabled for this assistant.")

            name = (arguments.get('name') or arguments.get('product_name') or '').strip()
            if not name:
                return self._make_tool_response(tool_call_id, "Product name is required.")

            default_code = arguments.get('default_code') or arguments.get('internal_reference') or ''
            p_type = arguments.get('type') or 'consu'
            list_price = float(arguments.get('list_price') or arguments.get('price') or 0.0)
            standard_price = float(arguments.get('standard_price') or arguments.get('cost') or 0.0)
            categ_name = arguments.get('categ_name') or arguments.get('category') or ''
            barcode = arguments.get('barcode') or ''
            sale_ok = arguments.get('sale_ok', True)
            purchase_ok = arguments.get('purchase_ok', True)

            categ = False
            if categ_name:
                categ = request.env['product.category'].sudo().search([('name', '=ilike', categ_name)], limit=1)
            if not categ:
                categ = request.env['product.category'].sudo().search([], limit=1)

            vals = {
                'name': name,
                'default_code': default_code or False,
                'type': p_type if p_type in ('consu', 'service', 'product') else 'consu',
                'list_price': list_price,
                'standard_price': standard_price,
                'categ_id': categ.id if categ else False,
                'barcode': barcode or False,
                'sale_ok': bool(sale_ok),
                'purchase_ok': bool(purchase_ok),
            }
            if assistant and assistant.company_id:
                vals['company_id'] = assistant.company_id.id

            product_template = request.env['product.template'].sudo().create(vals)

            # Link created product to call history
            vapi_call_id = call.get('id') or data.get('call_id')
            if vapi_call_id:
                self._link_call_history(
                    vapi_call_id,
                    {'product_tmpl_id': product_template.id},
                    assistant=assistant,
                    call_type=call.get('type') or 'webCall'
                )

            target_user = self._get_target_user(call=call, data=data, assistant=assistant)
            notification = {
                "operation": "product",
                "state": "success",
                "data": {
                    "name": product_template.name,
                    "default_code": product_template.default_code or "-",
                    "type": "Goods" if product_template.type == 'consu' else "Service",
                    "list_price": product_template.list_price,
                    "standard_price": product_template.standard_price,
                    "categ": product_template.categ_id.name if product_template.categ_id else "All",
                    "uom": product_template.uom_id.name if hasattr(product_template, 'uom_id') and product_template.uom_id else "Units",
                    "barcode": product_template.barcode or "-",
                    "sale_ok": product_template.sale_ok,
                    "purchase_ok": product_template.purchase_ok,
                },
                "record_id": product_template.id,
                "record_name": product_template.name,
            }
            self._send_bus_notification(target_user, notification)

            return self._make_tool_response(
                tool_call_id,
                f"Product '{product_template.name}' successfully created in Odoo (ID: {product_template.id}). Sales Price: {product_template.list_price}."
            )
        except Exception as e:
            _logger.exception("Error in create_product webhook: %s", e)
            return self._make_tool_response(tool_call_id if 'tool_call_id' in locals() else "tool_call_product", f"Error creating product: {str(e)}", status=500)

    @http.route('/vapi_voice_assistant/create_invoice', type='http',
                auth='public', csrf=False, methods=['POST'])
    def create_invoice(self, **kwargs):
        """Creates a customer invoice in account.move via voice assistant."""
        if not self._verify_webhook_secret():
            return self._make_json_response({"error": "Unauthorized"}, status=401)
        try:
            data = self._parse_request_data()
            message_data = data.get('message', {})
            call = message_data.get('call', {}) or data.get('call', {})
            assistant_vapi_id = call.get('assistantId')
            assistant = False
            if assistant_vapi_id:
                assistant = request.env['ora.ai'].sudo().search(
                    [('id_assistant', '=', assistant_vapi_id)], limit=1)

            tool_call_id, arguments = self._extract_tool_call(data, default_id="tool_call_invoice")

            if assistant and not assistant.is_invoice_creation:
                return self._make_tool_response(tool_call_id, "Invoice Creation is currently disabled for this assistant.")

            if 'account.move' not in request.env:
                return self._make_tool_response(tool_call_id, "Accounting module is not installed in Odoo.")

            customer_name = (arguments.get('Customer') or arguments.get('customer') or arguments.get('customer_name') or '').strip()
            invoice_lines_data = arguments.get('InvoiceLines') or arguments.get('invoice_lines') or arguments.get('lines') or []

            if not customer_name:
                return self._make_tool_response(tool_call_id, "Customer name is required to create an invoice.")

            if not invoice_lines_data:
                return self._make_tool_response(tool_call_id, "At least one invoice line is required to create an invoice.")

            Partner = request.env['res.partner'].sudo()
            customer = Partner.search([
                ('type', '!=', 'private'),
                '|', ('name', '=ilike', customer_name), ('display_name', '=ilike', customer_name)
            ], limit=1)
            if not customer:
                customer = Partner.create({
                    'name': customer_name,
                    'customer_rank': 1,
                    'company_id': assistant.company_id.id if assistant and assistant.company_id else False
                })

            invoice_lines = []
            preview_lines = []
            for item in invoice_lines_data:
                p_name = item.get('Product') or item.get('product') or item.get('product_name') or ''
                p_id = item.get('productId') or item.get('product_id') or item.get('id')
                qty = float(item.get('Quantity') or item.get('quantity') or item.get('qty') or 1.0)
                price_unit = float(item.get('UnitPrice') or item.get('price_unit') or item.get('price') or 0.0)

                product = False
                if p_id:
                    try:
                        product = request.env['product.product'].sudo().browse(int(p_id))
                    except Exception:
                        product = False
                if not product or not product.exists():
                    product = request.env['product.product'].sudo().search([
                        '|', ('name', '=ilike', p_name), ('default_code', '=ilike', p_name)
                    ], limit=1)

                if product and product.exists():
                    if price_unit <= 0:
                        price_unit = product.list_price
                    subtotal = qty * price_unit
                    invoice_lines.append(Command.create({
                        'product_id': product.id,
                        'name': product.display_name or product.name,
                        'quantity': qty,
                        'price_unit': price_unit,
                    }))
                    preview_lines.append({
                        'product': product.name,
                        'quantity': qty,
                        'price_unit': price_unit,
                        'tax': item.get('Tax') or 0,
                        'subtotal': subtotal,
                        'product_id': product.id
                    })

            if not invoice_lines:
                return self._make_tool_response(tool_call_id, "No valid products could be matched for this invoice.")

            move_vals = {
                'move_type': 'out_invoice',
                'partner_id': customer.id,
                'invoice_line_ids': invoice_lines,
            }
            if assistant and assistant.company_id:
                move_vals['company_id'] = assistant.company_id.id

            invoice = request.env['account.move'].sudo().create(move_vals)

            # Link created invoice to call history
            vapi_call_id = call.get('id') or data.get('call_id')
            if vapi_call_id:
                self._link_call_history(
                    vapi_call_id,
                    {'invoice_id': invoice.id, 'partner_id': customer.id},
                    assistant=assistant,
                    call_type=call.get('type') or 'webCall'
                )

            target_user = self._get_target_user(call=call, data=data, assistant=assistant)
            notification = {
                "operation": "invoice",
                "state": "success",
                "data": {
                    "customer": customer.name,
                    "lines": preview_lines,
                    "untaxed": invoice.amount_untaxed,
                    "tax": invoice.amount_tax,
                    "total": invoice.amount_total,
                },
                "record_id": invoice.id,
                "record_name": invoice.name or f"Draft #{invoice.id}",
            }
            self._send_bus_notification(target_user, notification)

            return self._make_tool_response(
                tool_call_id,
                f"Customer Invoice '{invoice.name or f'Draft #{invoice.id}'}' successfully created in draft state for {customer.name}. Total: {invoice.amount_total}."
            )
        except Exception as e:
            _logger.exception("Error in create_invoice webhook: %s", e)
            return self._make_tool_response(tool_call_id if 'tool_call_id' in locals() else "tool_call_invoice", f"Error creating invoice: {str(e)}", status=500)
