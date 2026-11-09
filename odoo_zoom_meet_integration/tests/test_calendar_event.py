# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestCalendarEventZoom(common.TransactionCase):
    """Test suite for Zoom Meet integration on calendar.event."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'zoom_company_access_token': 'dummy_access_token_12345',
        })
        cls.user = cls.env.user

    def _create_mocked_zoom_event(self, zoom_id='mock_event_123', **kwargs):
        """Helper to create a calendar event with is_zoom_meet=True while mocking Zoom creation."""
        vals = {
            'name': 'Test Zoom Event',
            'start': '2026-11-10 14:00:00',
            'stop': '2026-11-10 15:00:00',
            'duration': 1.0,
            'is_zoom_meet': True,
        }
        vals.update(kwargs)
        with patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request') as mock_req:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                'id': zoom_id,
                'join_url': f'https://zoom.us/j/{zoom_id}',
                'start_url': f'https://zoom.us/s/{zoom_id}',
            }
            mock_req.return_value = mock_resp
            return self.env['calendar.event'].with_context(uid=self.user.id).create(vals)

    def test_01_compute_description(self):
        """Test computed description when zoom_meet_code and zoom_meet_url are set."""
        event = self.env['calendar.event'].create({
            'name': 'Test Zoom Description',
            'start': '2026-11-10 09:00:00',
            'stop': '2026-11-10 10:00:00',
            'zoom_meet_url': 'https://zoom.us/j/123456789',
            'zoom_meet_code': '123456789',
        })
        event._compute_description()
        expected_desc = (
            "Join the Zoom Meeting at https://zoom.us/j/123456789"
            "using the Meeting Code 123456789"
        )
        self.assertEqual(event.description, expected_desc)

    def test_02_compute_description_empty_when_missing_code_or_url(self):
        """Test compute_description does nothing if code or url is missing."""
        event = self.env['calendar.event'].create({
            'name': 'Test Non-Zoom Event',
            'start': '2026-11-10 09:00:00',
            'stop': '2026-11-10 10:00:00',
        })
        event.description = False
        event._compute_description()
        self.assertFalse(event.description)

        # Only URL set, no code
        event.zoom_meet_url = 'https://zoom.us/j/123456789'
        event.zoom_meet_code = False
        event.description = False
        event._compute_description()
        self.assertFalse(event.description)

    def test_03_action_zoom_meet_url_with_url(self):
        """Test action_zoom_meet_url returns action pointing to event's zoom_meet_url."""
        event = self.env['calendar.event'].create({
            'name': 'Action URL Event',
            'start': '2026-11-10 09:00:00',
            'stop': '2026-11-10 10:00:00',
            'zoom_meet_url': 'https://zoom.us/j/99887766',
        })
        action = event.action_zoom_meet_url()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('url'), 'https://zoom.us/j/99887766')

    def test_04_action_zoom_meet_url_without_url(self):
        """Test action_zoom_meet_url falls back to Zoom base API URL when no URL is set."""
        event = self.env['calendar.event'].create({
            'name': 'Action URL Fallback Event',
            'start': '2026-11-10 09:00:00',
            'stop': '2026-11-10 10:00:00',
            'zoom_meet_url': False,
        })
        action = event.action_zoom_meet_url()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('url'), 'https://api.zoom.us/v2/')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_05_create_zoom_meet_success(self, mock_request):
        """Test creating calendar.event with is_zoom_meet=True triggers Zoom meeting creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': '987654321',
            'join_url': 'https://zoom.us/j/987654321',
            'start_url': 'https://zoom.us/s/987654321',
        }
        mock_request.return_value = mock_response

        event = self.env['calendar.event'].with_context(uid=self.user.id).create({
            'name': 'Zoom Meeting Create Success',
            'start': '2026-11-10 14:00:00',
            'stop': '2026-11-10 15:00:00',
            'duration': 1.0,
            'is_zoom_meet': True,
        })

        mock_request.assert_called_once()
        self.assertEqual(event.zoom_event, '987654321')
        self.assertEqual(event.zoom_meet_url, 'https://zoom.us/j/987654321')
        self.assertEqual(event.zoom_meet_code, '987654321')
        self.assertEqual(event.videocall_location, 'https://zoom.us/j/987654321')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_06_create_zoom_meet_token_expired(self, mock_request):
        """Test create raises UserError when Zoom returns code 124 (Token Expired)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': 124,
            'message': 'Access token is expired.',
        }
        mock_request.return_value = mock_response

        with self.assertRaises(UserError) as cm:
            self.env['calendar.event'].with_context(uid=self.user.id).create({
                'name': 'Zoom Meeting Expired Token',
                'start': '2026-11-10 14:00:00',
                'stop': '2026-11-10 15:00:00',
                'duration': 1.0,
                'is_zoom_meet': True,
            })
        self.assertIn("Token Expired, please refresh token", str(cm.exception))

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_07_create_zoom_meet_validation_error(self, mock_request):
        """Test create raises ValidationError when Zoom returns error without start_url."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': 300,
            'message': 'Validation failed or connection refused',
        }
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError) as cm:
            self.env['calendar.event'].with_context(uid=self.user.id).create({
                'name': 'Zoom Meeting Bad Connection',
                'start': '2026-11-10 14:00:00',
                'stop': '2026-11-10 15:00:00',
                'duration': 1.0,
                'is_zoom_meet': True,
            })
        self.assertIn("Failed to create Zoom event", str(cm.exception))

    def test_08_create_non_zoom_meet(self):
        """Test create does not invoke Zoom API when is_zoom_meet is False."""
        with patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request') as mock_req:
            event = self.env['calendar.event'].with_context(uid=self.user.id).create({
                'name': 'Standard Meeting',
                'start': '2026-11-10 14:00:00',
                'stop': '2026-11-10 15:00:00',
                'is_zoom_meet': False,
            })
            mock_req.assert_not_called()
            self.assertFalse(event.zoom_event)

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_09_write_enabling_zoom_meet(self, mock_request):
        """Test write toggling is_zoom_meet to True invokes Zoom creation if zoom_event is False."""
        event = self.env['calendar.event'].with_context(uid=self.user.id).create({
            'name': 'Meeting Later Zoom',
            'start': '2026-11-10 14:00:00',
            'stop': '2026-11-10 15:00:00',
            'is_zoom_meet': False,
        })
        self.assertFalse(event.zoom_event)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': '77889911',
            'join_url': 'https://zoom.us/j/77889911',
            'start_url': 'https://zoom.us/s/77889911',
        }
        mock_request.return_value = mock_response

        event.with_context(uid=self.user.id).write({'is_zoom_meet': True})
        self.assertEqual(event.zoom_event, '77889911')
        self.assertEqual(event.zoom_meet_url, 'https://zoom.us/j/77889911')

    def test_10_write_existing_zoom_meet_no_recreation(self):
        """Test write does not re-create zoom meet if zoom_event is already populated."""
        event = self._create_mocked_zoom_event(zoom_id='existing_event_id_123')

        with patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request') as mock_req:
            event.with_context(uid=self.user.id).write({'name': 'Updated Event Name'})
            mock_req.assert_not_called()

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete')
    def test_11_onchange_is_zoom_meet_delete_zoom(self, mock_delete):
        """Test onchange unchecking is_zoom_meet calls Zoom delete API and clears fields."""
        event = self._create_mocked_zoom_event(zoom_id='554433')
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        event.is_zoom_meet = False
        event.with_context(uid=self.user.id)._onchange_is_zoom_meet()

        mock_delete.assert_called_once()
        self.assertEqual(event.zoom_meet_url, '')
        self.assertEqual(event.zoom_meet_code, '')
        self.assertEqual(event.zoom_event, '')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete')
    def test_12_onchange_is_zoom_meet_token_expired(self, mock_delete):
        """Test onchange raises UserError when Zoom returns 401 Unauthorized."""
        event = self._create_mocked_zoom_event(zoom_id='554433')
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_delete.return_value = mock_response

        event.is_zoom_meet = False
        with self.assertRaises(UserError) as cm:
            event.with_context(uid=self.user.id)._onchange_is_zoom_meet()
        self.assertIn("Token Expired, please refresh token", str(cm.exception))

    def test_13_onchange_is_zoom_meet_noop(self):
        """Test onchange does not delete when is_zoom_meet is True or zoom_event is missing."""
        event = self._create_mocked_zoom_event(zoom_id='667788')
        with patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete') as mock_del:
            # is_zoom_meet is True
            event._onchange_is_zoom_meet()
            mock_del.assert_not_called()

            # is_zoom_meet is False but no zoom_event
            event.is_zoom_meet = False
            event.zoom_event = False
            event._onchange_is_zoom_meet()
            mock_del.assert_not_called()

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete')
    def test_14_unlink_zoom_meet_success(self, mock_delete):
        """Test unlink calls Zoom delete API and deletes the calendar.event record."""
        event = self._create_mocked_zoom_event(zoom_id='unlink_zoom_id_101')
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        event_id = event.id
        event.with_context(uid=self.user.id).unlink()

        mock_delete.assert_called_once()
        self.assertFalse(self.env['calendar.event'].browse(event_id).exists())

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete')
    def test_15_unlink_zoom_meet_token_expired(self, mock_delete):
        """Test unlink raises UserError when Zoom returns 401 Unauthorized."""
        event = self._create_mocked_zoom_event(zoom_id='unlink_zoom_id_102')
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_delete.return_value = mock_response

        with self.assertRaises(UserError) as cm:
            event.with_context(uid=self.user.id).unlink()
        self.assertIn("Token Expired, Please refresh token", str(cm.exception))

    def test_16_unlink_non_zoom_meet(self):
        """Test unlink on non-zoom meeting proceeds without calling Zoom delete API."""
        event = self.env['calendar.event'].with_context(uid=self.user.id).create({
            'name': 'Unlink Regular Event',
            'start': '2026-11-10 14:00:00',
            'stop': '2026-11-10 15:00:00',
            'is_zoom_meet': False,
        })
        with patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete') as mock_del:
            event_id = event.id
            event.with_context(uid=self.user.id).unlink()
            mock_del.assert_not_called()
            self.assertFalse(self.env['calendar.event'].browse(event_id).exists())

    def test_17_calendar_event_get_views(self):
        """Verify calendar.event form and calendar views with inherited Zoom fields render without error."""
        res = self.env['calendar.event'].get_views([(False, 'form'), (False, 'calendar')])
        self.assertIsInstance(res, dict)
        self.assertIn('views', res)
