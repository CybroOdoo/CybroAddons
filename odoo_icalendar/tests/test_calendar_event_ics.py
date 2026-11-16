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
from datetime import date, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import vobject

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCalendarEventIcs(TransactionCase):
    """Test suite for Odoo iCalendar event generation, ICS serialization,
    and attendee email dispatch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organizer_user = cls.env['res.users'].create({
            'name': 'Meeting Organizer',
            'login': 'organizer_user_ics_test',
            'email': 'organizer@example.com',
        })
        cls.organizer_partner = cls.organizer_user.partner_id

        cls.attendee_partner_1 = cls.env['res.partner'].create({
            'name': 'Meeting Attendee 1',
            'email': 'attendee1@example.com',
        })
        cls.attendee_partner_2 = cls.env['res.partner'].create({
            'name': 'Meeting Attendee 2',
            'email': 'attendee2@example.com',
        })
        cls.attendee_no_email = cls.env['res.partner'].create({
            'name': 'Attendee Without Email',
            'email': False,
        })

        cls.alarm_15min = cls.env['calendar.alarm'].create({
            'name': '15 Minutes Before',
            'alarm_type': 'notification',
            'duration': 15,
            'interval': 'minutes',
        })

        start_time = datetime(2026, 11, 15, 10, 0, 0)
        stop_time = datetime(2026, 11, 15, 11, 30, 0)

        cls.meeting_timed = cls.env['calendar.event'].create({
            'name': 'Q4 Strategy Review',
            'start': start_time,
            'stop': stop_time,
            'duration': 1.5,
            'location': 'Conference Room Alpha',
            'description': '<p>Reviewing company goals and milestones.</p>',
            'videocall_location': 'https://meet.jit.si/odoo-q4-strategy',
            'user_id': cls.organizer_user.id,
            'partner_ids': [(6, 0, [cls.organizer_partner.id, cls.attendee_partner_1.id])],
            'alarm_ids': [(6, 0, [cls.alarm_15min.id])],
        })

        cls.meeting_allday = cls.env['calendar.event'].create({
            'name': 'Annual Company Summit',
            'allday': True,
            'start_date': date(2026, 11, 20),
            'stop_date': date(2026, 11, 20),
            'user_id': cls.organizer_user.id,
            'partner_ids': [(6, 0, [cls.organizer_partner.id, cls.attendee_partner_1.id])],
        })

        cls.meeting_recurrent = cls.env['calendar.event'].create({
            'name': 'Weekly Sync',
            'start': start_time,
            'stop': stop_time,
            'recurrency': True,
            'rrule': 'RRULE:FREQ=WEEKLY;COUNT=4',
            'user_id': cls.organizer_user.id,
            'partner_ids': [(6, 0, [cls.organizer_partner.id, cls.attendee_partner_2.id])],
        })

    def test_01_populate_ics_timed_event(self):
        """Verify RFC 5545 attribute population for a standard timed meeting."""
        cal = vobject.iCalendar()
        event = cal.add('vevent')
        self.meeting_timed._populate_ics_event(event)

        self.assertEqual(event.summary.value, 'Q4 Strategy Review')
        self.assertEqual(event.location.value, 'Conference Room Alpha')
        self.assertEqual(event.url.value, 'https://meet.jit.si/odoo-q4-strategy')
        self.assertIn('Reviewing company goals and milestones.', event.description.value)
        self.assertTrue(event.uid.value.startswith(f"odoo-calendar-{self.meeting_timed.id}@"))

        expected_start = self.meeting_timed.start.replace(tzinfo=ZoneInfo('UTC'))
        expected_stop = self.meeting_timed.stop.replace(tzinfo=ZoneInfo('UTC'))
        self.assertEqual(event.dtstart.value, expected_start)
        self.assertEqual(event.dtend.value, expected_stop)

        self.assertEqual(event.organizer.value, 'MAILTO:organizer@example.com')
        self.assertEqual(event.attendee.value, 'MAILTO:attendee1@example.com')
        self.assertEqual(event.valarm.trigger.value, -timedelta(minutes=15))

    def test_02_populate_ics_allday_event(self):
        """Verify all-day events use VALUE=DATE and non-inclusive DTEND."""
        cal = vobject.iCalendar()
        event = cal.add('vevent')
        self.meeting_allday._populate_ics_event(event)

        self.assertEqual(event.dtstart.value, date(2026, 11, 20))
        self.assertEqual(event.dtend.value, date(2026, 11, 21))

    def test_03_populate_ics_recurrent_event(self):
        """Verify recurrent meetings populate clean RRULE without prefix."""
        cal = vobject.iCalendar()
        event = cal.add('vevent')
        self.meeting_recurrent._populate_ics_event(event)

        self.assertEqual(event.rrule.value, 'FREQ=WEEKLY;COUNT=4')

    def test_04_populate_ics_missing_dates_raises(self):
        """Verify UserError is raised if non-allday meeting lacks start or stop date."""
        event_without_dates = self.env['calendar.event'].new({
            'name': 'Meeting Without Time',
            'allday': False,
            'start': False,
            'stop': False,
        })
        cal = vobject.iCalendar()
        vevent = cal.add('vevent')
        with self.assertRaises(UserError):
            event_without_dates._populate_ics_event(vevent)

    def test_05_get_ics_file_serialization(self):
        """Verify _get_ics_file returns valid UTF-8 serialized ICS file bytes."""
        ics_data_dict = self.meeting_timed._get_ics_file()
        self.assertIn(self.meeting_timed.id, ics_data_dict)

        raw_bytes = ics_data_dict[self.meeting_timed.id]
        self.assertIsInstance(raw_bytes, bytes)
        self.assertIn(b'BEGIN:VCALENDAR', raw_bytes)
        self.assertIn(b'BEGIN:VEVENT', raw_bytes)
        self.assertIn(b'SUMMARY:Q4 Strategy Review', raw_bytes)
        self.assertIn(b'END:VEVENT', raw_bytes)
        self.assertIn(b'END:VCALENDAR', raw_bytes)

    def test_06_action_send_ics_success(self):
        """Verify action_send_ics generates attachment and sends email to attendees."""
        result = self.meeting_timed.action_send_ics()
        self.assertTrue(result)

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'calendar.event'),
            ('res_id', '=', self.meeting_timed.id),
            ('mimetype', '=', 'text/calendar'),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertEqual(attachment.name, 'Q4 Strategy Review.ics')
        self.assertIn(b'BEGIN:VCALENDAR', bytes(attachment.raw))

    def test_07_action_send_ics_no_attendee_email_raises(self):
        """Verify action_send_ics raises UserError when attendees lack email addresses."""
        meeting_no_email = self.env['calendar.event'].create({
            'name': 'Internal Discussion',
            'start': datetime(2026, 11, 16, 9, 0, 0),
            'stop': datetime(2026, 11, 16, 10, 0, 0),
            'partner_ids': [(6, 0, [self.attendee_no_email.id])],
        })
        with self.assertRaises(UserError):
            meeting_no_email.action_send_ics()

    def test_08_action_send_attendee_ics_file_multi_records(self):
        """Verify action_send_attendee_ics_file sends combined ICS to attendees across meetings."""
        batch_meetings = self.meeting_timed | self.meeting_allday
        result = batch_meetings.action_send_attendee_ics_file()
        self.assertTrue(result)

        combined_attachment = self.env['ir.attachment'].search([
            ('name', '=', 'All_Events.ics'),
            ('res_model', '=', 'calendar.event'),
        ], limit=1)
        self.assertTrue(combined_attachment)
        self.assertIn(b'SUMMARY:Q4 Strategy Review', bytes(combined_attachment.raw))
        self.assertIn(b'SUMMARY:Annual Company Summit', bytes(combined_attachment.raw))

    def test_09_action_send_attendee_ics_file_no_email_raises(self):
        """Verify action_send_attendee_ics_file raises UserError if no attendees have email."""
        isolated_meeting = self.env['calendar.event'].create({
            'name': 'Solo Offline Task',
            'start': datetime(2026, 11, 17, 14, 0, 0),
            'stop': datetime(2026, 11, 17, 15, 0, 0),
            'partner_ids': [(6, 0, [self.attendee_no_email.id])],
        })
        with self.assertRaises(UserError):
            isolated_meeting.action_send_attendee_ics_file()

    def test_10_vobject_missing_graceful_fallback(self):
        """Verify graceful fallback when vobject library is unavailable."""
        with patch('odoo.addons.odoo_icalendar.models.calendar_event.vobject', None):
            self.assertEqual(self.meeting_timed._get_ics_file(), {})
            self.assertFalse(self.meeting_timed.action_send_attendee_ics_file())
