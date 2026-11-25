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
import json
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.ora_ai_base.controllers.ora_ai_base import VapiAssistant, JsonResponse


@tagged('post_install', '-at_install')
class TestOraControllers(TransactionCase):
    """End-to-end integration tests for voice assistant webhook controller methods and standard models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = VapiAssistant()
        cls.webhook_secret = 'super_secret_webhook_token_12345'
        cls.env['ir.config_parameter'].sudo().set_str(
            'ora_ai_base.vapi_webhook_secret', cls.webhook_secret)

        cls.partner = cls.env['res.partner'].create({
            'name': 'Alice Wonder',
            'email': 'alice@example.com',
            'phone': '+1234567890',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Acoustic Desk Lamp',
            'list_price': 85.0,
        })
        cls.provider_model = cls.env['provider.model'].search([('provider', '=', 'openai')], limit=1)
        if not cls.provider_model:
            cls.provider_model = cls.env['provider.model'].create({
                'name': 'gpt-4o-mini',
                'provider': 'openai',
            })
        cls.transcriber_model = cls.env['transcriber.model'].search([('provider', '=', 'deepgram')], limit=1)
        if not cls.transcriber_model:
            cls.transcriber_model = cls.env['transcriber.model'].create({
                'name': 'nova-2',
                'provider': 'deepgram',
            })
        cls.language = cls.env['ora.language'].search([('code', '=', 'en')], limit=1)
        if not cls.language:
            cls.language = cls.env['ora.language'].create({
                'name': 'English',
                'code': 'en',
            })
        cls.assistant = cls.env['ora.ai'].create({
            'name': 'Sales Support Assistant',
            'provider': 'openai',
            'provider_model_id': cls.provider_model.id,
            'transcriber_provider': 'deepgram',
            'transcriber_model_id': cls.transcriber_model.id,
            'language_id': cls.language.id,
        })

    def _mock_request(self, payload=None, headers=None, query_args=None):
        """Builds a standardized mock Odoo HTTP request for controller integration tests."""
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.params = {}
        mock_headers = headers if headers is not None else {'x-vapi-secret': self.webhook_secret}
        mock_req.httprequest.headers = mock_headers
        mock_req.httprequest.args = query_args or {}

        body_payload = payload or {}
        mock_req.httprequest.get_json.return_value = body_payload
        mock_req.get_json_data.return_value = body_payload
        mock_req.httprequest.data = json.dumps(body_payload).encode('utf-8')
        return mock_req

    def test_01_json_response_wrapper(self):
        """Test JsonResponse structure and content serialization."""
        data = {'status': 'success', 'code': 200}
        resp = JsonResponse(data, status=200)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['status'], 'success')
        self.assertEqual(resp.get('status'), 'success')
        self.assertIn('status', resp)

    def test_02_make_tool_response(self):
        """Test tool response formatting conforming to Vapi spec."""
        resp = self.controller._make_tool_response(
            tool_call_id='call_tool_xyz',
            result_str='Order SO001 successfully placed'
        )
        parsed = json.loads(resp.data.decode('utf-8'))
        self.assertIn('results', parsed)
        self.assertEqual(parsed['results'][0]['toolCallId'], 'call_tool_xyz')
        self.assertEqual(parsed['results'][0]['result'], 'Order SO001 successfully placed')

    def test_03_extract_tool_call(self):
        """Test extraction of toolCallId and arguments from nested webhook data."""
        data_nested = {
            'message': {
                'toolCalls': [{
                    'id': 'call_123',
                    'function': {
                        'arguments': {'customer_name': 'Alice Wonder'}
                    }
                }]
            }
        }
        tool_id, args = self.controller._extract_tool_call(data_nested)
        self.assertEqual(tool_id, 'call_123')
        self.assertEqual(args.get('customer_name'), 'Alice Wonder')

    def test_04_find_customer_by_name(self):
        """Test flexible customer name resolution in company context."""
        found = self.controller._find_customer_by_name('Alice Wonder', env=self.env)
        self.assertEqual(found, self.partner)

        found_partial = self.controller._find_customer_by_name('Alice Cooper', env=self.env)
        self.assertEqual(found_partial, self.partner)

        empty = self.controller._find_customer_by_name('', env=self.env)
        self.assertFalse(empty)

    def test_05_webhook_secret_strict_verification(self):
        """Verify constant-time secret comparison and strict rejection of unauthorized requests."""
        # 1. No secret configured in system -> MUST reject
        self.env['ir.config_parameter'].sudo().set_str('ora_ai_base.vapi_webhook_secret', '')
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(headers={'x-vapi-secret': 'any_token'})):
            self.assertFalse(self.controller._verify_webhook_secret())

        # Restore secret
        self.env['ir.config_parameter'].sudo().set_str(
            'ora_ai_base.vapi_webhook_secret', self.webhook_secret)

        # 2. Secret configured, but request headers missing secret -> MUST reject
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(headers={})):
            self.assertFalse(self.controller._verify_webhook_secret())

        # 3. Secret configured, but header has wrong secret -> MUST reject
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(headers={'x-vapi-secret': 'wrong_invalid_secret'})):
            self.assertFalse(self.controller._verify_webhook_secret())

        # 4. Valid secret via x-vapi-secret header -> MUST accept
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(headers={'x-vapi-secret': self.webhook_secret})):
            self.assertTrue(self.controller._verify_webhook_secret())

        # 5. Valid secret via Authorization Bearer header -> MUST accept
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(headers={'Authorization': f'Bearer {self.webhook_secret}'})):
            self.assertTrue(self.controller._verify_webhook_secret())

    def test_06_unauthorized_endpoints_return_401(self):
        """Verify all endpoints return 401 Unauthorized when secret is invalid."""
        endpoints = [
            self.controller.final_details,
            self.controller.check_customer,
            self.controller.create_customer,
            self.controller.create_product,
            self.controller.create_invoice,
            self.controller.get_status,
            self.controller.get_language_details,
        ]
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(headers={'x-vapi-secret': 'invalid_hacker_token'})):
            for endpoint in endpoints:
                resp = endpoint()
                self.assertEqual(resp.status_code, 401)
                parsed = json.loads(resp.data.decode('utf-8'))
                self.assertEqual(parsed.get('error'), 'Unauthorized')

    def test_07_create_sale_order_via_voice_details(self):
        """End-to-end test of /vapi_voice_assistant/details creating sale.order and call history."""
        self.env['ir.config_parameter'].sudo().set_str('ora_ai_base.voice_order_auto_confirm', 'True')
        payload = {
            'message': {
                'call': {
                    'id': 'vapi_call_order_9988',
                    'type': 'webCall',
                },
                'toolCalls': [{
                    'id': 'tool_order_1',
                    'function': {
                        'name': 'GetFinalOrderDetails',
                        'arguments': {
                            'OrderDetails': {
                                'Customer': 'Bob Voice Buyer',
                                'Products': [{
                                    'Product': 'Acoustic Desk Lamp',
                                    'productId': self.product.id,
                                    'Quantity': 2,
                                    'Variant': '-'
                                }]
                            }
                        }
                    }
                }]
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload)):
            resp = self.controller.final_details()
            self.assertEqual(resp.status_code, 200)

            # Verify sale order created
            order = self.env['sale.order'].search([('partner_id.name', '=', 'Bob Voice Buyer')], limit=1)
            self.assertTrue(order)
            self.assertEqual(len(order.order_line), 1)
            self.assertEqual(order.order_line[0].product_id, self.product)
            self.assertEqual(order.order_line[0].product_uom_qty, 2)
            self.assertEqual(order.state, 'sale')

            # Verify call history linked to order
            call = self.env['ora.call.history'].search([('vapi_call_id', '=', 'vapi_call_order_9988')], limit=1)
            self.assertTrue(call)
            self.assertEqual(call.order_id, order)
            self.assertEqual(call.partner_id, order.partner_id)

            # Test Smart Button on Sale Order
            self.assertEqual(order.voice_call_count, 1)
            action = order.action_view_voice_calls()
            self.assertEqual(action.get('res_model'), 'ora.call.history')

    def test_08_check_and_create_customer(self):
        """Test /check_customer and /create_customer endpoints."""
        # Check existing customer
        payload_check = {
            'message': {
                'toolCalls': [{
                    'id': 'tool_check_1',
                    'function': {
                        'arguments': {'customer_name': 'Alice Wonder', 'phone': '+1234567890'}
                    }
                }]
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload_check)):
            resp = self.controller.check_customer()
            self.assertEqual(resp.status_code, 200)
            parsed = json.loads(resp.data.decode('utf-8'))
            self.assertIn('Alice Wonder', parsed['results'][0]['result'])

        # Create new customer
        payload_create = {
            'message': {
                'toolCalls': [{
                    'id': 'tool_create_cust_1',
                    'function': {
                        'arguments': {
                            'name': 'Charlie Chaplin',
                            'phone': '+1122334455',
                            'email': 'charlie@example.com',
                            'street': '123 Hollywood Blvd'
                        }
                    }
                }]
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload_create)):
            resp = self.controller.create_customer()
            self.assertEqual(resp.status_code, 200)
            cust = self.env['res.partner'].search([('name', '=', 'Charlie Chaplin')], limit=1)
            self.assertTrue(cust)
            self.assertEqual(cust.phone, '+1122334455')
            self.assertEqual(cust.email, 'charlie@example.com')

    def test_09_create_product_via_voice(self):
        """Test /create_product endpoint creating product.template."""
        payload = {
            'message': {
                'toolCalls': [{
                    'id': 'tool_prod_1',
                    'function': {
                        'arguments': {
                            'product_name': 'Smart Wireless Earbuds',
                            'price': 129.99,
                            'description': 'High fidelity earbuds with ANC'
                        }
                    }
                }]
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload)):
            resp = self.controller.create_product()
            self.assertEqual(resp.status_code, 200)
            prod = self.env['product.template'].search([('name', '=', 'Smart Wireless Earbuds')], limit=1)
            self.assertTrue(prod)
            self.assertEqual(prod.list_price, 129.99)

    def test_10_create_invoice_via_voice(self):
        """Test /create_invoice endpoint creating customer account.move."""
        payload = {
            'message': {
                'call': {'id': 'vapi_call_inv_7766'},
                'toolCalls': [{
                    'id': 'tool_inv_1',
                    'function': {
                        'arguments': {
                            'customer_name': 'Alice Wonder',
                            'invoice_lines': [{
                                'product_name': 'Acoustic Desk Lamp',
                                'quantity': 1,
                                'price': 85.0
                            }]
                        }
                    }
                }]
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload)):
            resp = self.controller.create_invoice()
            self.assertEqual(resp.status_code, 200)
            invoice = self.env['account.move'].search([('partner_id', '=', self.partner.id), ('move_type', '=', 'out_invoice')], limit=1)
            self.assertTrue(invoice)
            self.assertEqual(len(invoice.invoice_line_ids), 1)

            # Test Smart Button on Account Move
            call = self.env['ora.call.history'].search([('vapi_call_id', '=', 'vapi_call_inv_7766')], limit=1)
            self.assertTrue(call)
            self.assertEqual(call.invoice_id, invoice)
            self.assertEqual(invoice.voice_call_count, 1)
            action = invoice.action_view_voice_calls()
            self.assertEqual(action.get('res_model'), 'ora.call.history')

    def test_11_status_webhook_and_language_details(self):
        """Test /status end-of-call report updating call history and /language_details."""
        # Pre-create started call history
        call = self.env['ora.call.history'].create({
            'name': 'Call Status Test',
            'vapi_call_id': 'vapi_call_status_5544',
            'status': 'started',
        })
        payload_status = {
            'message': {
                'type': 'end-of-call-report',
                'call': {
                    'id': 'vapi_call_status_5544',
                    'duration': 142,
                    'cost': 0.085,
                },
                'recordingUrl': 'https://api.vapi.ai/recordings/rec_5544.wav',
                'transcript': 'Customer inquired about headphones.',
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload_status)):
            resp = self.controller.get_status()
            self.assertEqual(resp.status_code, 200)
            call.invalidate_recordset()
            self.assertEqual(call.status, 'completed')
            self.assertEqual(call.duration, 142)
            self.assertEqual(call.cost, 0.085)
            self.assertEqual(call.recording_url, 'https://api.vapi.ai/recordings/rec_5544.wav')

        # Language details endpoint
        payload_lang = {
            'message': {
                'toolCalls': [{
                    'id': 'tool_lang_1',
                    'function': {
                        'arguments': {'language': 'Spanish'}
                    }
                }]
            }
        }
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request(payload_lang)):
            resp = self.controller.get_language_details()
            self.assertEqual(resp.status_code, 200)

        # Smart button on partner
        call.write({'partner_id': self.partner.id})
        self.assertGreaterEqual(self.partner.voice_call_count, 1)
        action_partner = self.partner.action_view_voice_calls()
        self.assertEqual(action_partner.get('res_model'), 'ora.call.history')

    def test_12_targeted_bus_notification_security(self):
        """Verify that bus notifications are strictly dispatched to the initiating user record,
        preventing unauthorized public websocket interception."""
        with patch('odoo.addons.ora_ai_base.controllers.ora_ai_base.request', new=self._mock_request({})):
            # 1. Target user resolution from variableValues
            target = self.controller._get_target_user(call={'variableValues': {'user_id': str(self.env.user.id)}})
            self.assertEqual(target, self.env.user)

            # 2. Target user resolution from assistant creator fallback
            target_creator = self.controller._get_target_user(assistant=self.assistant)
            self.assertTrue(target_creator.exists())
            self.assertFalse(target_creator._is_public())

            # 3. Notification dispatch verification
            with patch.object(type(self.env['bus.bus']), '_sendone') as mock_send:
                self.controller._send_bus_notification(self.env.user, {'operation': 'test', 'data': 123})
                mock_send.assert_called_once()
                called_target = mock_send.call_args[0][0]
                called_type = mock_send.call_args[0][1]
                called_payload = mock_send.call_args[0][2]

                self.assertEqual(called_target, self.env.user)
                self.assertEqual(called_type, "ora_ai_base/voice_notification")
                self.assertEqual(called_payload.get('operation'), 'test')

