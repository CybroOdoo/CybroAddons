# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


@tagged('post_install', '-at_install')
class TestCalendarEventZoom(TransactionCase):

    def setUp(self):
        super(TestCalendarEventZoom, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Zoom Test Company',
            'zoom_company_access_token': 'test_token',
        })
        self.env.user.company_id = self.company
        
        self.event_data = {
            'name': 'Test Event',
            'start': datetime.now(),
            'stop': datetime.now(),
        }

    def test_compute_description(self):
        """Test compute description logic."""
        event = self.env['calendar.event'].create(self.event_data)
        event.write({
            'zoom_meet_code': '12345',
            'zoom_meet_url': 'http://zoom.us/j/12345'
        })
        self.assertIn('Join the Zoom Meeting at', event.description)
        self.assertIn('http://zoom.us/j/12345', event.description)
        self.assertIn('12345', event.description)

    def test_action_zoom_meet_url_with_url(self):
        """Test url action when url is present."""
        event = self.env['calendar.event'].create(self.event_data)
        event.zoom_meet_url = 'http://zoom.us/j/12345'
        res = event.action_zoom_meet_url()
        self.assertEqual(res.get('url'), 'http://zoom.us/j/12345')

    def test_action_zoom_meet_url_without_url(self):
        """Test url action when no url is present."""
        event = self.env['calendar.event'].create(self.event_data)
        res = event.action_zoom_meet_url()
        self.assertEqual(res.get('url'), 'https://api.zoom.us/v2/')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_create_zoom_meet_success(self, mock_request):
        """Test creating a zoom event sets correct fields."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'zoom123',
            'join_url': 'http://zoom.us/j/zoom123',
            'start_url': 'url'
        }
        mock_request.return_value = mock_response

        # Create triggers _create_zoom_meet
        event = self.env['calendar.event'].create(dict(self.event_data, is_zoom_meet=True))
        
        self.assertEqual(event.zoom_event, 'zoom123')
        self.assertEqual(event.zoom_meet_url, 'http://zoom.us/j/zoom123')
        self.assertEqual(event.zoom_meet_code, 'zoom123')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_create_zoom_meet_token_expired(self, mock_request):
        """Test create raises error when token expires."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 124}
        mock_request.return_value = mock_response

        with self.assertRaises(UserError):
            self.env['calendar.event'].create(dict(self.event_data, is_zoom_meet=True))

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_create_zoom_meet_failure(self, mock_request):
        """Test create raises error when creation fails."""
        mock_response = MagicMock()
        mock_response.json.return_value = {} # Missing start_url
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.env['calendar.event'].create(dict(self.event_data, is_zoom_meet=True))

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_write_creates_zoom_meet(self, mock_request):
        """Test writing is_zoom_meet creates the zoom meeting."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'zoom123',
            'join_url': 'http://zoom.us/j/zoom123',
            'start_url': 'url'
        }
        mock_request.return_value = mock_response

        event = self.env['calendar.event'].create(self.event_data)
        self.assertFalse(event.zoom_event)

        event.write({'is_zoom_meet': True})
        
        self.assertEqual(event.zoom_event, 'zoom123')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete')
    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_onchange_is_zoom_meet_deletes(self, mock_request, mock_delete):
        """Test turning off is_zoom_meet deletes the event from zoom."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'zoom123', 'join_url': 'url', 'start_url': 'url'}
        mock_request.return_value = mock_response
        
        event = self.env['calendar.event'].create(dict(self.event_data, is_zoom_meet=True))
        
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_delete.return_value = mock_delete_response

        event.is_zoom_meet = False
        event._onchange_is_zoom_meet()

        self.assertFalse(event.zoom_event)
        self.assertFalse(event.zoom_meet_url)
        self.assertFalse(event.zoom_meet_code)

    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.delete')
    @patch('odoo.addons.odoo_zoom_meet_integration.models.calendar_event.requests.request')
    def test_unlink_deletes_zoom_meet(self, mock_request, mock_delete):
        """Test unlinking event deletes the event from zoom."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'zoom123', 'join_url': 'url', 'start_url': 'url'}
        mock_request.return_value = mock_response
        
        event = self.env['calendar.event'].create(dict(self.event_data, is_zoom_meet=True))
        
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_delete.return_value = mock_delete_response

        event.unlink()
        
        # Verify delete was called
        mock_delete.assert_called_once()
