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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import hashlib
import hmac
import json
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestDocusignWebhookController(HttpCase):
    """Unit and HTTP tests for DocusignWebhookController in controllers/main.py."""

    def test_01_webhook_get(self):
        """Test GET request to /docusign/webhook returns 405 Method Not Allowed."""
        response = self.url_open('/docusign/webhook')
        self.assertEqual(response.status_code, 405)

    def test_02_webhook_missing_envelope_id(self):
        """Test POST request without envelope ID returns 400 Bad Request."""
        response = self.url_open(
            '/docusign/webhook',
            data=b'{}',
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No envelope_id found", response.text)

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_03_webhook_post_json_connect(self, mock_process_webhook):
        """Test POST request with DocuSign Connect 2.1 JSON payload."""
        payload = {
            'event': 'envelope-completed',
            'data': {
                'envelopeId': 'ENV-JSON-12345',
                'envelopeSummary': {
                    'status': 'completed',
                }
            }
        }
        response = self.url_open(
            '/docusign/webhook',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "OK")
        mock_process_webhook.assert_called_once_with('ENV-JSON-12345', 'completed')

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_04_webhook_post_xml_connect(self, mock_process_webhook):
        """Test POST request with classic DocuSign XML webhook payload."""
        xml_payload = """<?xml version="1.0" encoding="utf-8"?>
        <DocuSignEnvelopeInformation>
            <EnvelopeStatus>
                <EnvelopeID>ENV-XML-67890</EnvelopeID>
                <Status>Completed</Status>
            </EnvelopeStatus>
        </DocuSignEnvelopeInformation>
        """.encode('utf-8')

        response = self.url_open(
            '/docusign/webhook',
            data=xml_payload,
            headers={'Content-Type': 'text/xml'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "OK")
        mock_process_webhook.assert_called_once_with('ENV-XML-67890', 'completed')

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_05_webhook_hmac_verification(self, mock_process_webhook):
        """Test HMAC verification on incoming webhook."""
        secret = "secret-connect-key-123"
        self.env['docusign.credentials'].create({
            'name': 'Test Credentials with Secret',
            'company_id': self.env.company.id,
            'integrator_key': 'key-123',
            'user_id_data': 'user-123',
            'account_id_data': 'acc-123',
            'webhook_secret': secret,
            'private_key_ids': [(0, 0, {'name': 'rsa.key', 'raw': b'test'})],
        })

        payload = json.dumps({
            'event': 'envelope-completed',
            'data': {'envelopeId': 'ENV-HMAC-999', 'envelopeSummary': {'status': 'completed'}}
        }).encode('utf-8')

        # 1. Without HMAC header -> 401 Unauthorized
        res_unauth = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res_unauth.status_code, 401)

        # 2. With invalid HMAC header -> 401 Unauthorized
        res_invalid = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-DocuSign-Signature-1': 'invalid-signature'
            }
        )
        self.assertEqual(res_invalid.status_code, 401)

        # 3. With valid HMAC header -> 200 OK
        computed_hash = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).digest()
        valid_sig = base64.b64encode(computed_hash).decode('utf-8')
        res_valid = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-DocuSign-Signature-1': valid_sig
            }
        )
        self.assertEqual(res_valid.status_code, 200)
        mock_process_webhook.assert_called_with('ENV-HMAC-999', 'completed')

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_06_verify_webhook_signature_bearer_and_custom_token(self, mock_process_webhook):
        """Test webhook authorization via Authorization Bearer token and X-DocuSign-Token."""
        secret = "bearer-secret-789"
        self.env['docusign.credentials'].create({
            'name': 'Credentials with Bearer',
            'company_id': self.env.company.id,
            'integrator_key': 'key-bearer',
            'user_id_data': 'user-bearer',
            'account_id_data': 'acc-bearer',
            'webhook_secret': secret,
            'private_key_ids': [(0, 0, {'name': 'rsa.key', 'raw': b'test'})],
        })

        payload = json.dumps({
            'event': 'envelope-completed',
            'data': {'envelopeId': 'ENV-BEARER-1', 'envelopeSummary': {'status': 'completed'}}
        }).encode('utf-8')

        # 1. Authorization: Bearer <secret>
        res_bearer = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {secret}'
            }
        )
        self.assertEqual(res_bearer.status_code, 200)

        # 2. X-DocuSign-Token: <secret>
        res_token = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-DocuSign-Token': secret
            }
        )
        self.assertEqual(res_token.status_code, 200)

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_07_verify_webhook_signature_url_params(self, mock_process_webhook):
        """Test webhook authorization via query parameter token/secret."""
        secret = "param-secret-456"
        self.env['docusign.credentials'].create({
            'name': 'Credentials with URL Param Secret',
            'company_id': self.env.company.id,
            'integrator_key': 'key-param',
            'user_id_data': 'user-param',
            'account_id_data': 'acc-param',
            'webhook_secret': secret,
            'private_key_ids': [(0, 0, {'name': 'rsa.key', 'raw': b'test'})],
        })

        payload = json.dumps({
            'event': 'envelope-completed',
            'data': {'envelopeId': 'ENV-PARAM-1', 'envelopeSummary': {'status': 'completed'}}
        }).encode('utf-8')

        res = self.url_open(
            f'/docusign/webhook?token={secret}',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 200)

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_08_webhook_ir_config_parameter_secret(self, mock_process_webhook):
        """Test webhook authorization fallback using ir.config_parameter secret."""
        # Clear any credentials with secrets
        self.env['docusign.credentials'].search([]).write({'webhook_secret': False})
        secret = "sysparam-secret-999"
        self.env['ir.config_parameter'].set_str('docusign.webhook_secret', secret)

        payload = json.dumps({
            'event': 'envelope-completed',
            'data': {'envelopeId': 'ENV-SYSPARAM-1', 'envelopeSummary': {'status': 'completed'}}
        }).encode('utf-8')

        # Invalid token -> 401
        res_invalid = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={'Content-Type': 'application/json', 'X-DocuSign-Token': 'wrong'}
        )
        self.assertEqual(res_invalid.status_code, 401)

        # Valid token -> 200
        res_valid = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={'Content-Type': 'application/json', 'X-DocuSign-Token': secret}
        )
        self.assertEqual(res_valid.status_code, 200)

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook')
    def test_09_webhook_malformed_xml_and_post_kwargs_fallback(self, mock_process_webhook):
        """Test webhook handles malformed XML gracefully and falls back to form parameters."""
        # Unset secrets for open access in this fallback test
        self.env['docusign.credentials'].search([]).write({'webhook_secret': False})
        self.env['ir.config_parameter'].search([('key', '=', 'docusign.webhook_secret')]).unlink()

        # Malformed XML but envelope_id provided in query / post form kwargs
        bad_xml = b"<NotValidXML><EnvelopeStatus>"
        res = self.url_open(
            '/docusign/webhook?envelope_id=ENV-KWARGS-1&status=completed',
            data=bad_xml,
            headers={'Content-Type': 'text/xml'}
        )
        self.assertEqual(res.status_code, 200)
        mock_process_webhook.assert_called_with('ENV-KWARGS-1', 'completed')

    @patch('odoo.addons.docusign_odoo_connector.models.docusign_lines.DocusignLines._process_docusign_webhook', side_effect=Exception("Database error"))
    def test_10_webhook_process_exception_returns_200(self, mock_process_webhook):
        """Test webhook logs processing exceptions and still returns HTTP 200 OK to acknowledge DocuSign."""
        self.env['docusign.credentials'].search([]).write({'webhook_secret': False})
        self.env['ir.config_parameter'].search([('key', '=', 'docusign.webhook_secret')]).unlink()

        payload = json.dumps({
            'event': 'envelope-completed',
            'data': {'envelopeId': 'ENV-EXC-1', 'envelopeSummary': {'status': 'completed'}}
        }).encode('utf-8')

        res = self.url_open(
            '/docusign/webhook',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 200)
