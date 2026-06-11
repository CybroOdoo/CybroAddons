# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCalendarEvent(TransactionCase):
    """Test calendar.event Zoom meeting integration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.write({
            'zoom_client': 'test_client_id',
            'zoom_client_secret': 'test_client_secret',
            'zoom_redirect_uri': 'http://localhost:8069/zoom_meet_authentication',
            'zoom_company_access_token': 'test_access_token',
            'zoom_company_refresh_token': 'test_refresh_token',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Zoom Test Partner',
            'email': 'zoom@test.com',
        })

    def test_calendar_event_default_fields(self):
        """Test calendar event has Zoom fields with defaults."""
        event = self.env['calendar.event'].create({
            'name': 'Test Meeting',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
        })

        self.assertFalse(
            event.is_zoom_meet,
            "is_zoom_meet should be False by default."
        )

        self.assertFalse(
            event.zoom_meet_url,
            "zoom_meet_url should be empty by default."
        )

        self.assertFalse(
            event.zoom_meet_code,
            "zoom_meet_code should be empty by default."
        )

        self.assertFalse(
            event.zoom_event,
            "zoom_event should be empty by default."
        )

    def test_compute_description(self):
        """Test description is computed from Zoom URL and code."""
        event = self.env['calendar.event'].create({
            'name': 'Zoom Description Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
        })

        event.write({
            'zoom_meet_url': 'https://zoom.us/j/123456',
            'zoom_meet_code': '123456',
        })

        self.assertIn(
            'https://zoom.us/j/123456',
            event.description,
            "Description should contain the Zoom URL."
        )

        self.assertIn(
            '123456',
            event.description,
            "Description should contain the Zoom code."
        )

    def test_action_zoom_meet_url_with_url(self):
        """Test action_zoom_meet_url returns the meeting URL."""
        event = self.env['calendar.event'].create({
            'name': 'URL Action Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'zoom_meet_url': 'https://zoom.us/j/999999',
        })

        action = event.action_zoom_meet_url()

        self.assertEqual(
            action['type'],
            'ir.actions.act_url',
            "Action type should be ir.actions.act_url."
        )

        self.assertEqual(
            action['url'],
            'https://zoom.us/j/999999',
            "Action URL should match the zoom_meet_url."
        )

        self.assertEqual(
            action['target'],
            'new',
            "Action target should be 'new'."
        )

    def test_action_zoom_meet_url_without_url(self):
        """Test action_zoom_meet_url fallback when no URL is set."""
        event = self.env['calendar.event'].create({
            'name': 'No URL Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
        })

        action = event.action_zoom_meet_url()

        self.assertEqual(
            action['url'],
            'https://api.zoom.us/v2/',
            "Should fallback to Zoom API base URL."
        )

    @patch('odoo.addons.odoo_zoom_meet_integration.models'
           '.calendar_event.requests.request')
    def test_create_zoom_meet_success(self, mock_request):
        """Test creating a calendar event with Zoom meeting enabled."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': '88888888888',
            'join_url': 'https://zoom.us/j/88888888888',
            'start_url': 'https://zoom.us/s/88888888888',
        }
        mock_request.return_value = mock_response

        event = self.env['calendar.event'].create({
            'name': 'Zoom Create Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'is_zoom_meet': True,
        })

        self.assertEqual(
            event.zoom_event,
            '88888888888',
            "zoom_event should be set from API response."
        )

        self.assertEqual(
            event.zoom_meet_url,
            'https://zoom.us/j/88888888888',
            "zoom_meet_url should be set from API response."
        )

        self.assertEqual(
            event.zoom_meet_code,
            '88888888888',
            "zoom_meet_code should be set from API response."
        )

    @patch('odoo.addons.odoo_zoom_meet_integration.models'
           '.calendar_event.requests.request')
    def test_create_zoom_meet_token_expired(self, mock_request):
        """Test creating Zoom meeting raises error on expired token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 124}
        mock_request.return_value = mock_response

        with self.assertRaises(UserError):
            self.env['calendar.event'].create({
                'name': 'Token Expired Test',
                'start': datetime.now(),
                'stop': datetime.now() + timedelta(hours=1),
                'is_zoom_meet': True,
            })

    @patch('odoo.addons.odoo_zoom_meet_integration.models'
           '.calendar_event.requests.request')
    def test_create_zoom_meet_failure(self, mock_request):
        """Test creating Zoom meeting raises ValidationError on failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': 'invalid'}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.env['calendar.event'].create({
                'name': 'Create Fail Test',
                'start': datetime.now(),
                'stop': datetime.now() + timedelta(hours=1),
                'is_zoom_meet': True,
            })

    @patch(
        'odoo.addons.odoo_zoom_meet_integration.models.'
        'calendar_event.requests.request'
    )
    @patch(
        'odoo.addons.odoo_zoom_meet_integration.models.'
        'calendar_event.requests.delete'
    )
    def test_unlink_zoom_event(self, mock_delete, mock_request):
        """Test unlinking a Zoom event calls the Zoom delete API."""

        mock_create_response = MagicMock()
        mock_create_response.json.return_value = {
            'id': '77777777777',
            'join_url': 'https://zoom.us/j/77777777777',
            'start_url': 'https://zoom.us/s/77777777777',
        }

        mock_request.return_value = mock_create_response
        mock_delete.return_value = MagicMock(status_code=204)

        event = self.env['calendar.event'].create({
            'name': 'Unlink Zoom Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'is_zoom_meet': True,
        })

        event.unlink()

        mock_request.assert_called_once()
        mock_delete.assert_called_once()

    def test_video_call_location_related(self):
        """Test video_call_location is related to zoom_meet_url."""
        event = self.env['calendar.event'].create({
            'name': 'Related Field Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'zoom_meet_url': 'https://zoom.us/j/555555',
        })

        self.assertEqual(
            event.video_call_location,
            'https://zoom.us/j/555555',
            "video_call_location should mirror zoom_meet_url."
        )
