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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOraCallHistory(TransactionCase):
    """Unit tests for voice assistant call logs and audit records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Voice Caller',
            'email': 'voice_caller@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Voice Microphone Pro',
            'list_price': 120.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
        })

    def test_01_create_call_history_record(self):
        """Test creating and inspecting call history audit fields."""
        history = self.env['ora.call.history'].create({
            'name': 'VAPI-CALL-TEST-001',
            'vapi_call_id': 'call_vapi_abc_123',
            'duration': 125,
            'cost': 0.045,
            'recording_url': 'https://vapi.ai/recordings/call_vapi_abc_123.mp3',
            'transcript': 'Agent: Hello! Customer: I would like to order one microphone.',
            'partner_id': self.partner.id,
            'created_partner_id': self.partner.id,
            'order_id': self.sale_order.id,
            'invoice_id': self.invoice.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
        })

        self.assertEqual(history.name, 'VAPI-CALL-TEST-001')
        self.assertEqual(history.vapi_call_id, 'call_vapi_abc_123')
        self.assertEqual(history.duration, 125)
        self.assertEqual(history.cost, 0.045)
        self.assertEqual(history.order_id, self.sale_order)
        self.assertEqual(history.invoice_id, self.invoice)
        self.assertEqual(history.partner_id, self.partner)
        self.assertEqual(history.created_partner_id, self.partner)
        self.assertEqual(history.product_tmpl_id, self.product.product_tmpl_id)

    def test_02_smart_button_navigation_actions(self):
        """Test smart button actions returning valid act_window dictionaries."""
        history = self.env['ora.call.history'].create({
            'name': 'VAPI-CALL-TEST-002',
            'vapi_call_id': 'call_vapi_nav_789',
            'partner_id': self.partner.id,
            'created_partner_id': self.partner.id,
            'order_id': self.sale_order.id,
            'invoice_id': self.invoice.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
        })

        action_so = history.action_view_sale_order()
        self.assertEqual(action_so.get('res_model'), 'sale.order')
        self.assertEqual(action_so.get('res_id'), self.sale_order.id)

        action_inv = history.action_view_invoice()
        self.assertEqual(action_inv.get('res_model'), 'account.move')
        self.assertEqual(action_inv.get('res_id'), self.invoice.id)

        action_pt = history.action_view_created_partner()
        self.assertEqual(action_pt.get('res_model'), 'res.partner')
        self.assertEqual(action_pt.get('res_id'), self.partner.id)

        action_prod = history.action_view_product()
        self.assertEqual(action_prod.get('res_model'), 'product.template')
        self.assertEqual(action_prod.get('res_id'), self.product.product_tmpl_id.id)

    def test_03_log_call_status(self):
        """Test status parsing from webhook payload."""
        payload = {
            'call_id': 'call_webhook_log_001',
            'duration': 45,
            'cost': 0.015,
            'recording_url': 'https://vapi.ai/recordings/test.wav',
            'transcript': 'Customer placed an order',
            'started_at': '2026-11-09T10:00:00Z',
            'ended_at': '2026-11-09T10:00:45Z',
            'ended_reason': 'customer-ended-call',
            'type': 'end-of-call-report',
            'partner_id': self.partner.id,
            'order_id': self.sale_order.id,
        }
        res = self.env['ora.call.history'].log_call_status(payload)
        self.assertTrue(res)
        self.assertEqual(res.status, 'completed')

        record = self.env['ora.call.history'].search([('vapi_call_id', '=', 'call_webhook_log_001')], limit=1)
        self.assertTrue(record)
        self.assertEqual(record.status, 'completed')
        self.assertEqual(record.vapi_call_id, 'call_webhook_log_001')

    def test_04_navigation_actions_empty_records(self):
        """Test smart button actions when records are not linked return False."""
        empty_history = self.env['ora.call.history'].create({
            'name': 'EMPTY-NAV-TEST',
            'vapi_call_id': 'call_empty_nav_001',
        })
        self.assertFalse(empty_history.action_view_sale_order())
        self.assertFalse(empty_history.action_view_invoice())
        self.assertFalse(empty_history.action_view_created_partner())
        self.assertFalse(empty_history.action_view_product())

    def test_05_log_call_status_edge_cases_and_payloads(self):
        """Test various webhook payload structures and fallback duration/transcript logic."""
        CallHistory = self.env['ora.call.history']

        # 1. Empty payload
        self.assertFalse(CallHistory.log_call_status({}))

        # 2. Ignored msg_type
        self.assertFalse(CallHistory.log_call_status({'message': {'type': 'speech-update'}}))

        # 3. Missing call ID
        self.assertFalse(CallHistory.log_call_status({'type': 'status-update'}))

        # 4. Status update in-progress with existing record returns existing record
        rec = CallHistory.create({
            'name': 'EXISTING-001',
            'vapi_call_id': 'call_existing_progress_001',
        })
        res_progress = CallHistory.log_call_status({
            'message': {
                'type': 'status-update',
                'status': 'in-progress',
                'call': {'id': 'call_existing_progress_001'},
            }
        })
        self.assertEqual(res_progress.id, rec.id)

        # 5. Payload with durationMs and conversation list and salesperson metadata
        admin_user = self.env.ref('base.user_admin')
        payload_ms = {
            'message': {
                'type': 'end-of-call-report',
                'call': {
                    'id': 'call_ms_conv_001',
                    'durationMs': 12000,
                    'cost': 0.05,
                    'conversation': [
                        {'role': 'system', 'content': 'You are a bot'},
                        {'role': 'assistant', 'content': 'Hello, how can I assist?'},
                        {'role': 'user', 'content': 'I want a quote'},
                    ],
                    'metadata': {'salesperson_id': str(admin_user.id)},
                },
                'endedReason': 'normal',
            }
        }
        res_ms = CallHistory.log_call_status(payload_ms)
        self.assertTrue(res_ms)
        self.assertEqual(res_ms.duration, 12)
        self.assertIn("Hello, how can I assist?", res_ms.transcript)
        self.assertEqual(res_ms.user_id, admin_user)

        # 6. Payload with startedAt and endedAt ISO dates
        payload_iso = {
            'type': 'end-of-call-report',
            'call_id': 'call_iso_001',
            'startedAt': '2026-11-09T10:00:00Z',
            'endedAt': '2026-11-09T10:00:30Z',
            'duration': 0,
        }
        res_iso = CallHistory.log_call_status(payload_iso)
        self.assertTrue(res_iso)
        self.assertEqual(res_iso.duration, 30)

        # 7. Updating existing record on end-of-call report
        update_payload = {
            'type': 'end-of-call-report',
            'call_id': 'call_existing_progress_001',
            'duration': 65,
            'cost': 0.10,
        }
        res_updated = CallHistory.log_call_status(update_payload)
        self.assertEqual(res_updated.id, rec.id)
        self.assertEqual(res_updated.duration, 65)
        self.assertEqual(res_updated.cost, 0.10)

        # 8. Auto-linking sale order and invoice matching call_id[:8]
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'origin': "Voice Assistant (call_lin)",
        })
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_origin': "Voice Assistant (call_lin)",
        })
        res_linked = CallHistory.log_call_status({
            'type': 'end-of-call-report',
            'call_id': 'call_link_9999',
            'duration': 10,
        })
        self.assertEqual(res_linked.order_id, so)
        self.assertEqual(res_linked.invoice_id, inv)

