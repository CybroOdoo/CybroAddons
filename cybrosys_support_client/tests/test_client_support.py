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
import base64
import json
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger

from odoo.addons.cybrosys_support_client.wizard.client_support import (
    DEFAULT_SUPPORT_ENDPOINT,
    SUPPORT_ENDPOINT_PARAM,
)

POST_PATH = (
    'odoo.addons.cybrosys_support_client.wizard.client_support.requests.post'
)
LOGGER_NAME = 'odoo.addons.cybrosys_support_client.wizard.client_support'


@tagged('post_install', '-at_install')
class TestClientSupport(TransactionCase):
    """Tests for the Cybrosys support wizard (client.support)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='support_internal_user',
            groups='base.group_user', email='internal@example.com')
        cls.wizard = cls.env['client.support'].with_user(cls.user).create({
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+911234567890',
            'subject': 'Cannot print invoice',
            'description': 'Printing fails with an error.',
            'support_type': 'functional',
            'category': 'bug',
            'priority': '3',
        })
        cls.params = cls.env['ir.config_parameter'].sudo()

    def _set_endpoint(self, value):
        """Set the endpoint config parameter through the ORM."""
        param = self.params.search([('key', '=', SUPPORT_ENDPOINT_PARAM)])
        if param:
            param.value = value
        else:
            self.params.create(
                {'key': SUPPORT_ENDPOINT_PARAM, 'value': value})

    def _create_attachment(self, name, raw=None):
        """Create an attachment owned by the wizard user."""
        vals = {'name': name}
        if raw is not None:
            vals['raw'] = raw
        return self.env['ir.attachment'].with_user(self.user).create(vals)

    @staticmethod
    def _mock_response(json_data=None, json_error=None):
        response = MagicMock()
        response.raise_for_status.return_value = None
        if json_error:
            response.json.side_effect = json_error
        else:
            response.json.return_value = json_data
        return response

    @staticmethod
    def _http_error(status_code):
        response = requests.Response()
        response.status_code = status_code
        return requests.HTTPError(response=response)

    # ------------------------------------------------------------------
    # Defaults and access rights
    # ------------------------------------------------------------------
    def test_default_values(self):
        wizard = self.env['client.support'].with_user(self.user).create({
            'subject': 'Defaults', 'email': 'a@example.com'})
        self.assertEqual(wizard.name, self.user.name)
        self.assertEqual(wizard.support_type, 'technical')
        self.assertEqual(wizard.category, 'bug')
        self.assertEqual(wizard.priority, '2')
        self.assertFalse(wizard.show_payload)

    def test_default_email_and_phone_from_user(self):
        wizard = self.env['client.support'].with_user(self.user).create({
            'subject': 'Defaults'})
        self.assertEqual(wizard.email, self.user.email)
        self.assertEqual(wizard.phone, self.user.partner_id.phone)

    def test_internal_user_can_use_wizard(self):
        self.assertTrue(self.wizard.exists())
        self.wizard.with_user(self.user).write({'subject': 'Updated'})
        self.assertEqual(self.wizard.subject, 'Updated')

    def test_portal_user_has_no_access(self):
        portal_user = new_test_user(
            self.env, login='support_portal_user', groups='base.group_portal')
        with self.assertRaises(AccessError):
            self.env['client.support'].with_user(portal_user).create({
                'subject': 'Portal', 'email': 'portal@example.com'})

    # ------------------------------------------------------------------
    # Endpoint configuration
    # ------------------------------------------------------------------
    def test_endpoint_default_from_data_file(self):
        param = self.params.search([('key', '=', SUPPORT_ENDPOINT_PARAM)])
        self.assertEqual(param.value, DEFAULT_SUPPORT_ENDPOINT)

    def test_endpoint_uses_config_parameter(self):
        self._set_endpoint('https://help.example.com/api/request')
        self.assertEqual(
            self.wizard._get_support_endpoint(),
            'https://help.example.com/api/request')

    def test_endpoint_falls_back_when_blank(self):
        self._set_endpoint('   ')
        self.assertEqual(
            self.wizard._get_support_endpoint(), DEFAULT_SUPPORT_ENDPOINT)

    def test_tracking_url_uses_endpoint_host(self):
        self._set_endpoint('https://help.example.com/api/request')
        self.assertEqual(
            self.wizard._get_tracking_url(),
            'https://help.example.com/track-ticket')

    def test_tracking_url_falls_back_for_invalid_endpoint(self):
        self._set_endpoint('not-a-valid-url')
        self.assertEqual(
            self.wizard._get_tracking_url(),
            'https://support.cybrosys.com/track-ticket')

    # ------------------------------------------------------------------
    # Payload
    # ------------------------------------------------------------------
    def test_build_payload_fields(self):
        params = self.wizard._build_payload(
            redact_attachments=True)['params']
        self.assertEqual(params['customer_name'], 'Test User')
        self.assertEqual(params['email'], 'test@example.com')
        self.assertEqual(params['phone'], '+911234567890')
        self.assertEqual(params['subject'], 'Cannot print invoice')
        self.assertEqual(params['description'], 'Printing fails with an error.')
        self.assertEqual(params['support_type'], 'functional')
        self.assertEqual(params['category'], 'Bug')
        self.assertEqual(params['priority'], 'Blocker')

    def test_build_payload_empty_values(self):
        wizard = self.env['client.support'].with_user(self.user).create({
            'name': False, 'email': 'a@example.com', 'phone': False,
            'subject': 'Empty'})
        params = wizard._build_payload(redact_attachments=True)['params']
        self.assertEqual(params['customer_name'], '')
        self.assertEqual(params['phone'], '')
        self.assertEqual(params['description'], '')

    def test_prepare_attachment_payload(self):
        attachment = self._create_attachment('log.txt', b'hello world')
        empty = self._create_attachment('empty.txt')
        self.wizard.attachment_ids = attachment | empty
        payload = self.wizard._prepare_attachment_payload()
        # Attachments without content are skipped.
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['name'], 'log.txt')
        data = payload[0]['data']
        if isinstance(data, bytes):
            data = data.decode()
        self.assertEqual(data, base64.b64encode(b'hello world').decode())

    def test_build_payload_redacted_attachment_count(self):
        params = self.wizard._build_payload(
            redact_attachments=True)['params']
        self.assertEqual(params['attachments'], '0 attachments')
        attachment = self._create_attachment('one.txt', b'one')
        self.wizard.attachment_ids = attachment
        params = self.wizard._build_payload(
            redact_attachments=True)['params']
        self.assertEqual(params['attachments'], '1 attachment')
        second = self._create_attachment('two.txt', b'two')
        self.wizard.attachment_ids |= second
        params = self.wizard._build_payload(
            redact_attachments=True)['params']
        self.assertEqual(params['attachments'], '2 attachments')

    def test_build_payload_with_attachments_is_a_list(self):
        attachment = self._create_attachment('one.txt', b'one')
        self.wizard.attachment_ids = attachment
        params = self.wizard._build_payload()['params']
        self.assertIsInstance(params['attachments'], list)
        self.assertEqual(params['attachments'][0]['name'], 'one.txt')

    def test_payload_preview_hidden_by_default(self):
        self.assertFalse(self.wizard.payload_preview)

    def test_payload_preview_when_enabled(self):
        self.wizard.show_payload = True
        preview = json.loads(self.wizard.payload_preview)
        self.assertEqual(
            preview['params']['subject'], 'Cannot print invoice')
        self.assertEqual(preview['params']['attachments'], '0 attachments')
        self.wizard.show_payload = False
        self.assertFalse(self.wizard.payload_preview)

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
    def test_submit_success_returns_notification(self):
        reply = {'result': {'message': 'success', 'ticket_id': 'CYB-1001'}}
        with patch(POST_PATH, return_value=self._mock_response(reply)) as post:
            action = self.wizard.confirm_button()
        post.assert_called_once()
        self.assertEqual(
            post.call_args.args[0], self.wizard._get_support_endpoint())
        self.assertEqual(
            post.call_args.kwargs['json'], self.wizard._build_payload())
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        params = action['params']
        self.assertEqual(params['type'], 'success')
        self.assertTrue(params['sticky'])
        self.assertIn('Ticket Reference: CYB-1001', params['message'])
        self.assertTrue(params['message'].endswith('%s'))
        tracking_url = self.wizard._get_tracking_url()
        self.assertEqual(
            params['links'], [{'label': tracking_url, 'url': tracking_url}])
        self.assertEqual(
            params['next'], {'type': 'ir.actions.act_window_close'})

    def test_submit_success_without_ticket_id(self):
        reply = {'result': {'message': 'success'}}
        with patch(POST_PATH, return_value=self._mock_response(reply)):
            action = self.wizard.confirm_button()
        self.assertNotIn('Ticket Reference', action['params']['message'])

    def test_submit_unsuccessful_reply_raises(self):
        for reply in ({'result': {'message': 'error'}}, {}):
            with patch(POST_PATH, return_value=self._mock_response(reply)):
                with self.assertRaisesRegex(ValidationError, 'did not go through'):
                    self.wizard.confirm_button()

    @mute_logger(LOGGER_NAME)
    def test_submit_http_413(self):
        with patch(POST_PATH, side_effect=self._http_error(413)):
            with self.assertRaisesRegex(ValidationError, 'too large'):
                self.wizard.confirm_button()

    @mute_logger(LOGGER_NAME)
    def test_submit_http_server_error(self):
        for status_code in (500, 503):
            with patch(POST_PATH, side_effect=self._http_error(status_code)):
                with self.assertRaisesRegex(ValidationError, 'having issues'):
                    self.wizard.confirm_button()

    @mute_logger(LOGGER_NAME)
    def test_submit_http_client_error(self):
        with patch(POST_PATH, side_effect=self._http_error(400)):
            with self.assertRaisesRegex(ValidationError, 'was rejected'):
                self.wizard.confirm_button()

    @mute_logger(LOGGER_NAME)
    def test_submit_http_error_without_response(self):
        with patch(POST_PATH, side_effect=requests.HTTPError()):
            with self.assertRaisesRegex(ValidationError, 'was rejected'):
                self.wizard.confirm_button()

    @mute_logger(LOGGER_NAME)
    def test_submit_network_errors(self):
        for error in (requests.ConnectionError(), requests.Timeout()):
            with patch(POST_PATH, side_effect=error):
                with self.assertRaisesRegex(
                        ValidationError, 'Could not reach the support service'):
                    self.wizard.confirm_button()

    @mute_logger(LOGGER_NAME)
    def test_submit_invalid_json_response(self):
        response = self._mock_response(
            json_error=json.JSONDecodeError('Invalid', '', 0))
        with patch(POST_PATH, return_value=response):
            with self.assertRaisesRegex(ValidationError, 'unexpected response'):
                self.wizard.confirm_button()

    # ------------------------------------------------------------------
    # WhatsApp
    # ------------------------------------------------------------------
    def test_whatsapp_button_action(self):
        action = self.wizard.whatsapp_button()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['target'], 'new')
        self.assertTrue(action['url'].startswith('https://wa.me/919074270811?text='))
        self.assertIn('Test%20User', action['url'])
        self.assertIn('test%40example.com', action['url'])
        self.assertIn('Printing%20fails', action['url'])

    def test_whatsapp_button_without_optional_values(self):
        wizard = self.env['client.support'].with_user(self.user).create({
            'name': False, 'email': 'a@example.com', 'subject': 'Hi'})
        action = wizard.whatsapp_button()
        self.assertIn('a%40example.com', action['url'])
