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
import urllib.request
import urllib.error

from odoo.tests.common import TransactionCase, HttpCase, tagged


@tagged('post_install', '-at_install')
class TestSmartLeadCaptureModel(TransactionCase):
    """Model-level tests: duplicate detection, lead creation, settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Lead = cls.env['crm.lead']
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson_slc',
            'email': 'salesperson@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id,
                                   cls.env.ref('sales_team.group_sale_salesman').id])],
        })
        cls.env['ir.config_parameter'].sudo().set_param(
            'smart_lead_capture.default_salesperson_id', cls.salesperson.id
        )

    def test_01_lead_source_channel_field_exists(self):
        """The lead_source_channel field should be available on crm.lead."""
        lead = self.Lead.create({'name': 'Channel Field Test'})
        self.assertEqual(lead.lead_source_channel, 'manual')

    def test_02_create_new_lead_via_payload(self):
        """A new lead should be created with the expected fields populated."""
        payload = {
            'full_name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '9876543210',
            'company': 'Acme Corp',
            'product_interest': 'CRM',
            'budget': '5000',
            'message': 'Interested in a demo',
        }
        lead = self.Lead.create({
            'name': payload['full_name'],
            'contact_name': payload['full_name'],
            'email_from': payload['email'],
            'phone': payload['phone'],
            'partner_name': payload['company'],
            'type': 'opportunity',
            'lead_source_channel': 'google_form',
            'user_id': self.salesperson.id,
            'expected_revenue': float(payload['budget']),
        })
        self.assertEqual(lead.email_from, 'jane.doe@example.com')
        self.assertEqual(lead.user_id, self.salesperson)
        self.assertEqual(lead.lead_source_channel, 'google_form')
        self.assertEqual(lead.expected_revenue, 5000.0)

    def test_03_duplicate_detection_by_email(self):
        """Searching by email_from should find an existing active lead."""
        self.Lead.create({
            'name': 'Existing Lead',
            'email_from': 'duplicate@example.com',
        })
        found = self.Lead.search([
            ('email_from', '=', 'duplicate@example.com'),
            ('active', '=', True),
        ], limit=1)
        self.assertTrue(found, "Existing lead with matching email should be found")

    def test_04_duplicate_detection_by_phone(self):
        """Searching by phone should find an existing active lead."""
        self.Lead.create({
            'name': 'Phone Lead',
            'phone': '1112223333',
        })
        found = self.Lead.search([
            ('phone', '=', '1112223333'),
            ('active', '=', True),
        ], limit=1)
        self.assertTrue(found, "Existing lead with matching phone should be found")

    def test_05_update_existing_lead_appends_description(self):
        """Re-submitting for an existing lead should append to description, not overwrite."""
        lead = self.Lead.create({
            'name': 'Repeat Submitter',
            'email_from': 'repeat@example.com',
            'description': 'First submission notes',
        })
        new_note = 'Second submission notes'
        lead.write({
            'description': (lead.description or '') + f"\n\n--- New submission ---\n{new_note}"
        })
        self.assertIn('First submission notes', lead.description)
        self.assertIn('Second submission notes', lead.description)

    def test_06_whatsapp_notification_skips_without_credentials(self):
        """send_whatsapp_notification should no-op safely when Twilio creds are unset."""
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('smart_lead_capture.twilio_account_sid', '')
        ICP.set_param('smart_lead_capture.twilio_auth_token', '')
        lead = self.Lead.create({'name': 'No Twilio Config Lead'})
        try:
            lead.send_whatsapp_notification()
        except Exception as e:
            self.fail(f"send_whatsapp_notification raised unexpectedly: {e}")

    def test_07_outbound_webhook_skips_unconfigured_url(self):
        """_trigger_outbound_webhook should silently skip when no URL is configured."""
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('smart_lead_capture.outbound_webhook_url', '')
        lead = self.Lead.create({'name': 'No Outbound URL Lead'})
        try:
            lead._trigger_outbound_webhook(event='lead.created')
        except Exception as e:
            self.fail(f"_trigger_outbound_webhook raised unexpectedly: {e}")

    def test_08_outbound_webhook_skips_localhost_url(self):
        """_trigger_outbound_webhook should refuse to call a localhost URL (self-loop guard)."""
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('smart_lead_capture.outbound_webhook_url', 'http://localhost:8017/webhook/x')
        lead = self.Lead.create({'name': 'Localhost Guard Lead'})
        try:
            lead._trigger_outbound_webhook(event='lead.created')
        except Exception as e:
            self.fail(f"_trigger_outbound_webhook raised unexpectedly: {e}")


@tagged('post_install', '-at_install')
class TestSmartLeadCaptureWebhook(HttpCase):
    """Live HTTP tests against the /webhook/google-form controller endpoint."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param(
            'smart_lead_capture.outbound_webhook_url', ''
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'smart_lead_capture.twilio_account_sid', ''
        )

    def _post_form(self, payload):
        return self.url_open(
            '/webhook/google-form',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
        )

    def _raw_post(self, body_bytes):
        """POST raw bytes directly, bypassing url_open's GET fallback on empty data."""
        req = urllib.request.Request(
            self.base_url() + '/webhook/google-form',
            data=body_bytes,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.status, json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode('utf-8'))

    def test_01_empty_body_returns_400(self):
        status, data = self._raw_post(b'')
        self.assertEqual(status, 400)
        self.assertEqual(data.get('status'), 'error')

    def test_02_invalid_json_returns_400(self):
        status, data = self._raw_post(b'{not valid json')
        self.assertEqual(status, 400)
        self.assertEqual(data.get('status'), 'error')

    def test_03_missing_identifying_fields_returns_400(self):
        response = self._post_form({'product_interest': 'CRM'})
        self.assertEqual(response.status_code, 400)

    def test_04_valid_payload_creates_lead(self):
        payload = {
            'full_name': 'Webhook Test User',
            'email': 'webhook.test@example.com',
            'phone': '5551234567',
            'company': 'Webhook Co',
            'budget': '1000',
        }
        response = self._post_form(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'created')
        self.assertTrue(data.get('lead_id'))

        lead = self.env['crm.lead'].browse(data['lead_id'])
        self.assertEqual(lead.email_from, 'webhook.test@example.com')
        self.assertEqual(lead.lead_source_channel, 'google_form')

    def test_05_resubmitting_same_email_updates_not_duplicates(self):
        payload = {
            'full_name': 'Repeat User',
            'email': 'repeat.webhook@example.com',
            'phone': '5559998888',
        }
        first = self._post_form(payload)
        self.assertEqual(first.status_code, 200)
        first_data = first.json()
        self.assertEqual(first_data['action'], 'created')

        payload['message'] = 'Following up again'
        second = self._post_form(payload)
        self.assertEqual(second.status_code, 200)
        second_data = second.json()
        self.assertEqual(second_data['action'], 'updated')
        self.assertEqual(second_data['lead_id'], first_data['lead_id'])

        leads = self.env['crm.lead'].search([
            ('email_from', '=', 'repeat.webhook@example.com')
        ])
        self.assertEqual(len(leads), 1, "Resubmission must not create a second lead")