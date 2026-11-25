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
import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from psycopg2 import errors

from odoo.addons.odoo_jira_connector.controllers.jira_connector import (
    JiraWebhook, valid_signature)

from .common import LOGGER, JiraTestCommon

REQUEST = 'odoo.addons.odoo_jira_connector.controllers.jira_connector.request'


class TestJiraWebhookController(JiraTestCommon):

    def call_webhook(self, body, headers=None, sign=True):
        """Call the /jira_webhook endpoint with a raw body; return
        (answer, status) and the mocked event handler."""
        request_stub = Mock()
        request_stub.env = self.env
        request_stub.httprequest.data = body
        if headers is None and sign:
            secret = self.Param.get_param('odoo_jira_connector.webhook_secret')
            if secret:
                signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
                headers = {'X-Hub-Signature': f'sha256={signature}'}
        request_stub.httprequest.headers = headers or {}
        request_stub.make_json_response.side_effect = lambda data, status=200: (data, status)
        with patch(REQUEST, request_stub), \
                patch.object(type(self.env['project.task']), 'webhook_data_handle') as handler:
            answer = JiraWebhook.import_jira_data.original_endpoint(JiraWebhook())
        return answer, handler

    def test_dispatches_event_when_automatic_enabled(self):
        self.set_jira_config(automatic=True)
        payload = {'webhookEvent': 'jira:issue_created', 'issue': {'key': 'JTP-2'}}
        answer, handler = self.call_webhook(json.dumps(payload).encode())
        self.assertEqual(answer, ({'status': 'received'}, 200))
        handler.assert_called_once_with(payload, 'jira:issue_created')

    def test_ignores_events_when_automatic_disabled(self):
        self.set_jira_config(automatic=False)
        self.Param.set_param('odoo_jira_connector.webhook_secret', 's3cret')
        answer, handler = self.call_webhook(b'{"webhookEvent": "jira:issue_created"}')
        self.assertEqual(answer, ({'status': 'received'}, 200))
        handler.assert_not_called()

    def test_rejects_webhook_when_no_secret_is_set(self):
        self.Param.set_param('odoo_jira_connector.webhook_secret', False)
        body = b'{"webhookEvent": "jira:issue_created"}'
        with self.assertLogs(LOGGER, 'WARNING'):
            answer, handler = self.call_webhook(body, sign=False)
        self.assertEqual(answer[1], 401)
        self.assertEqual(answer[0], {'status': 'unauthorized'})
        handler.assert_not_called()

    def test_signature_is_required_when_a_secret_is_set(self):
        self.set_jira_config(automatic=True)
        self.Param.set_param('odoo_jira_connector.webhook_secret', 's3cret')
        body = b'{"webhookEvent": "jira:issue_deleted", "issue": {"key": "JTP-1"}}'
        with self.assertLogs(LOGGER, 'WARNING'):
            answer, handler = self.call_webhook(body, {'X-Hub-Signature': 'sha256=forged'}, sign=False)
        self.assertEqual(answer[1], 401)
        self.assertEqual(answer[0], {'status': 'invalid signature'})
        handler.assert_not_called()

        signature = hmac.new(b's3cret', body, hashlib.sha256).hexdigest()
        answer, handler = self.call_webhook(body, {'X-Hub-Signature': f'sha256={signature}'})
        self.assertEqual(answer[1], 200)
        handler.assert_called_once()

    def test_valid_signature(self):
        body = b'{}'
        signature = hmac.new(b'key', body, hashlib.sha256).hexdigest()
        self.assertTrue(valid_signature('key', body, 'sha256=' + signature.upper()))
        self.assertFalse(valid_signature('key', body, 'sha1=' + signature))
        self.assertFalse(valid_signature('key', body, None))
        self.assertFalse(valid_signature('other', body, 'sha256=' + signature))

    def test_invalid_body_and_missing_event(self):
        self.set_jira_config(automatic=True)
        with self.assertLogs(LOGGER, 'WARNING'):
            answer, handler = self.call_webhook(b'not json')
        self.assertEqual(answer[1], 400)
        answer, handler = self.call_webhook(b'["no", "event"]')
        self.assertEqual(answer[1], 200)
        handler.assert_not_called()

    def test_handler_errors_are_logged_but_concurrency_errors_retried(self):
        self.set_jira_config(automatic=True)
        body = b'{"webhookEvent": "jira:issue_created"}'
        signature = hmac.new(b's3cret', body, hashlib.sha256).hexdigest()
        request_stub = Mock()
        request_stub.env = self.env
        request_stub.httprequest.data = body
        request_stub.httprequest.headers = {'X-Hub-Signature': f'sha256={signature}'}
        request_stub.make_json_response.side_effect = lambda data, status=200: (data, status)
        Task = type(self.env['project.task'])
        with patch(REQUEST, request_stub):
            with patch.object(Task, 'webhook_data_handle', side_effect=KeyError('issue')), \
                    self.assertLogs(LOGGER, 'ERROR'):
                answer = JiraWebhook.import_jira_data.original_endpoint(JiraWebhook())
            self.assertEqual(answer[1], 200)
            with patch.object(Task, 'webhook_data_handle',
                              side_effect=errors.SerializationFailure()), \
                    self.assertRaises(errors.SerializationFailure):
                JiraWebhook.import_jira_data.original_endpoint(JiraWebhook())
