# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime, timedelta
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestCalendarEvent(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].search([('company_id', '!=', False)], limit=1)
        cls.company = cls.user.company_id
        cls.company.write({
            'hangout_client_id': 'test_client_id',
            'hangout_client_secret': 'test_client_secret',
            'hangout_company_access_token': 'access_token_123',
            'hangout_company_refresh_token': 'refresh_token_abc',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Bob Tester',
            'email': 'bob.tester@example.com',
        })

    def setUp(self):
        super().setUp()
        self.context = {'uid': self.user.id}

    def test_01_action_google_meet_url(self):
        """Test action_google_meet_url redirects properly."""
        event = self.env['calendar.event'].create({
            'name': 'Meeting without URL',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
        })
        res = event.action_google_meet_url()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('url'), 'https://meet.google.com/')

        event.google_meet_url = 'https://meet.google.com/abc-defg-hij'
        res = event.action_google_meet_url()
        self.assertEqual(res.get('url'), 'https://meet.google.com/abc-defg-hij')

    def test_02_create_google_meet_success(self):
        """Test creating calendar event with is_google_meet=True calls API and sets fields."""
        mock_response = {
            'id': 'google_event_999',
            'hangoutLink': 'https://meet.google.com/xyz-pdq-rst',
            'conferenceData': {
                'conferenceId': 'xyz-pdq-rst'
            }
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.status_code = 200

            event = self.env['calendar.event'].with_context(self.context).create({
                'name': 'Google Meet Sync Event',
                'start': datetime.now(),
                'stop': datetime.now() + timedelta(hours=1),
                'is_google_meet': True,
                'partner_ids': [(4, self.partner.id)],
            })

            self.assertEqual(event.google_event_id, 'google_event_999')
            self.assertEqual(event.google_meet_url, 'https://meet.google.com/xyz-pdq-rst')
            self.assertEqual(event.google_meet_code, 'xyz-pdq-rst')

    def test_03_create_google_meet_api_error_retry_success(self):
        """Test API error flow on creation triggers token refresh and retries successfully."""
        mock_response_error = {
            'error': {
                'code': 401,
                'message': 'Invalid Credentials'
            }
        }
        mock_response_success = {
            'id': 'google_event_555',
            'hangoutLink': 'https://meet.google.com/aaa-bbb-ccc',
            'conferenceData': {
                'conferenceId': 'aaa-bbb-ccc'
            }
        }

        with patch.object(self.env['res.company'].__class__, 'google_meet_company_refresh_token',
                          create=True) as mock_refresh, \
                patch('requests.post') as mock_post:
            mock_post.return_value.json.side_effect = [mock_response_error, mock_response_success]
            mock_post.return_value.status_code = 200

            event = self.env['calendar.event'].with_context(self.context).create({
                'name': 'Google Meet Sync Event with error',
                'start': datetime.now(),
                'stop': datetime.now() + timedelta(hours=1),
                'is_google_meet': True,
            })

            mock_refresh.assert_called_once()
            self.assertEqual(event.google_event_id, 'google_event_555')
            self.assertEqual(event.google_meet_url, 'https://meet.google.com/aaa-bbb-ccc')

    def test_04_create_google_meet_failure(self):
        """Test API failure when hangoutLink is missing in response."""
        mock_response_fail = {
            'status': 'error'
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response_fail
            mock_post.return_value.status_code = 400

            with self.assertRaises(ValidationError) as ctx:
                self.env['calendar.event'].with_context(self.context).create({
                    'name': 'Google Meet Failed Event',
                    'start': datetime.now(),
                    'stop': datetime.now() + timedelta(hours=1),
                    'is_google_meet': True,
                })
            self.assertIn("Failed to create event", str(ctx.exception))

    def test_05_write_google_meet_trigger(self):
        """Test write method triggers _create_google_meet when event becomes google meet."""
        event = self.env['calendar.event'].create({
            'name': 'Normal Event',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'is_google_meet': False,
        })

        mock_response = {
            'id': 'google_event_888',
            'hangoutLink': 'https://meet.google.com/qwe-rty-uio',
            'conferenceData': {
                'conferenceId': 'qwe-rty-uio'
            }
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.status_code = 200

            event.with_context(self.context).write({'is_google_meet': True})
            self.assertEqual(event.google_event_id, 'google_event_888')
            self.assertEqual(event.google_meet_url, 'https://meet.google.com/qwe-rty-uio')

    def test_06_onchange_is_google_meet_delete(self):
        """Test deselecting is_google_meet calls DELETE on Google API and clears local fields."""
        event = self.env['calendar.event'].with_context(self.context).create({
            'name': 'Event to Delete Meet',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'is_google_meet': False,
        })

        event.write({
            'is_google_meet': True,
            'google_event_id': 'google_event_123',
            'google_meet_url': 'https://meet.google.com/x-y-z',
            'google_meet_code': 'x-y-z',
        })

        with patch('requests.delete') as mock_delete:
            mock_delete.return_value.status_code = 204

            event.is_google_meet = False
            event.with_context(self.context)._onchange_is_google_meet()

            mock_delete.assert_called_once()
            self.assertFalse(event.google_meet_url)
            self.assertFalse(event.google_meet_code)
            self.assertFalse(event.google_event_id)
