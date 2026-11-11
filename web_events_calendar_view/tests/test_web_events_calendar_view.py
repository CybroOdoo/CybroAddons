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
from datetime import date, datetime, time, timedelta

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebEventsCalendarViewController(HttpCase):
    """HTTP and JSON-RPC tests for the EventCalendar controller routes."""

    @classmethod
    def setUpClass(cls):
        """Create test user and published, unpublished, upcoming, and past events."""
        super().setUpClass()
        internal_group = cls.env.ref('base.group_user')
        event_manager_group = cls.env.ref('event.group_event_manager')
        cls.event_manager_user = cls.env['res.users'].create({
            'name': 'WECV Event Manager',
            'login': 'wecv_event_manager',
            'password': 'wecv_event_manager',
            'email': 'wecv_event_manager@test.com',
            'group_ids': [(6, 0, [internal_group.id, event_manager_group.id])],
        })
        today = date.today()
        cls.event_published_future = cls.env['event.event'].create({
            'name': 'WECV Published Future Event',
            'date_begin': datetime(2099, 6, 12, 9, 0, 0),
            'date_end': datetime(2099, 6, 14, 17, 0, 0),
            'website_published': True,
        })
        cls.event_unpublished_future = cls.env['event.event'].create({
            'name': 'WECV Unpublished Future Event',
            'date_begin': datetime(2099, 6, 15, 9, 0, 0),
            'date_end': datetime(2099, 6, 16, 17, 0, 0),
            'website_published': False,
        })
        cls.event_today_published = cls.env['event.event'].create({
            'name': 'WECV Today Published Event 1',
            'date_begin': datetime.combine(today, time(0, 0, 0)),
            'date_end': datetime.combine(today + timedelta(days=2), time(23, 59, 0)),
            'website_published': True,
        })
        cls.event_today_published_2 = cls.env['event.event'].create({
            'name': 'WECV Today Published Event 2',
            'date_begin': datetime.combine(today, time(0, 0, 0)),
            'date_end': datetime.combine(today + timedelta(days=3), time(23, 59, 0)),
            'website_published': True,
        })
        cls.event_past = cls.env['event.event'].create({
            'name': 'WECV Past Event',
            'date_begin': datetime.combine(today - timedelta(days=10), time(9, 0, 0)),
            'date_end': datetime.combine(today - timedelta(days=9), time(17, 0, 0)),
            'website_published': True,
        })

    def test_days_with_events(self):
        """Verify days_with_events returns all dates with events inside the range."""
        self.authenticate(None, None)
        days = self.make_jsonrpc_request(
            '/web_events_calendar_view/days_with_events',
            {'start': '2099-06-11', 'end': '2099-06-15'},
        )
        self.assertIn('2099-06-12', days)
        self.assertIn('2099-06-13', days)
        self.assertIn('2099-06-14', days)
        self.assertNotIn('2099-06-11', days)
        # Public user must not see unpublished event dates
        self.assertNotIn('2099-06-15', days)

        # Authenticated internal event manager should also see unpublished event dates
        self.authenticate('wecv_event_manager', 'wecv_event_manager')
        admin_days = self.make_jsonrpc_request(
            '/web_events_calendar_view/days_with_events',
            {'start': '2099-06-11', 'end': '2099-06-16'},
        )
        self.assertIn('2099-06-15', admin_days)
        self.assertIn('2099-06-16', admin_days)

    def test_events_for_day(self):
        """Verify events_for_day filters events by date, handles limit, and respects access."""
        self.authenticate(None, None)
        day_events = self.make_jsonrpc_request(
            '/web_events_calendar_view/events_for_day',
            {'day': '2099-06-13'},
        )
        names = [ev['name'] for ev in day_events]
        self.assertIn(self.event_published_future.name, names)
        self.assertNotIn(self.event_unpublished_future.name, names)
        self.assertNotIn(self.event_past.name, names)

        matched = next(ev for ev in day_events if ev['name'] == self.event_published_future.name)
        self.assertEqual(
            matched['date_begin_pred_located'],
            self.event_published_future.date_begin_pred_located,
        )
        self.assertTrue(matched['website_published'])
        self.assertIn('website_url', matched)
        self.assertIn('event_type_id', matched)

        # Default day=None falls back to today and excludes past events
        upcoming_events = self.make_jsonrpc_request(
            '/web_events_calendar_view/events_for_day',
            {},
        )
        upcoming_names = [ev['name'] for ev in upcoming_events]
        self.assertIn(self.event_today_published.name, upcoming_names)
        self.assertNotIn(self.event_past.name, upcoming_names)

        # Limit parameter caps the returned records
        limited_events = self.make_jsonrpc_request(
            '/web_events_calendar_view/events_for_day',
            {'limit': 1},
        )
        self.assertEqual(len(limited_events), 1)

        # Authenticated internal event manager can view unpublished events for that day
        self.authenticate('wecv_event_manager', 'wecv_event_manager')
        admin_day_events = self.make_jsonrpc_request(
            '/web_events_calendar_view/events_for_day',
            {'day': '2099-06-16'},
        )
        admin_names = [ev['name'] for ev in admin_day_events]
        self.assertIn(self.event_unpublished_future.name, admin_names)

    def test_get_events(self):
        """Verify get_events returns upcoming events formatted for FullCalendar."""
        self.authenticate(None, None)
        events = self.make_jsonrpc_request('/web_events_calendar_view/events', {})
        by_title = {ev['title']: ev for ev in events}

        self.assertIn(self.event_published_future.name, by_title)
        self.assertIn(self.event_unpublished_future.name, by_title)
        self.assertIn(self.event_today_published.name, by_title)
        self.assertNotIn(self.event_past.name, by_title)

        future_entry = by_title[self.event_published_future.name]
        self.assertEqual(future_entry['start'], '2099-06-12')
        self.assertEqual(future_entry['end'], '2099-06-14')
        self.assertEqual(future_entry['display'], 'background')

    def test_calendar_events(self):
        """Verify /calendar_events renders the global events calendar page."""
        self.authenticate(None, None)
        response = self.url_open('/calendar_events')
        self.assertEqual(response.status_code, 200)
        body = response.text
        self.assertIn('s_event_calendar_list', body)
        self.assertIn('s_event_calendar', body)
        self.assertIn('s_event_list', body)
        self.assertIn('Events Calendar', body)

