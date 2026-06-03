# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import UserError

class TestCalendarEvent(common.TransactionCase):

    def setUp(self):
        super(TestCalendarEvent, self).setUp()
        self.CalendarEvent = self.env['calendar.event']
        self.Partner = self.env['res.partner']
        
        self.partner_1 = self.Partner.create({
            'name': 'Test Partner 1',
            'email': 'partner1@example.com'
        })
        self.partner_2 = self.Partner.create({
            'name': 'Test Partner 2',
            'email': 'partner2@example.com'
        })

        self.calendar_event = self.CalendarEvent.create({
            'name': 'Test Event',
            'start': '2023-01-01 10:00:00',
            'stop': '2023-01-01 12:00:00',
            'allday': False,
            'partner_ids': [(6, 0, [self.partner_1.id, self.partner_2.id])],
            'description': '<p>Test Description</p>',
            'location': 'Test Location',
        })

    def test_action_send_ics(self):
        # We test that the method doesn't raise any error during execution
        # Assuming calendar module and calendar_sms are installed correctly.
        self.calendar_event.action_send_ics()

    def test_action_send_attendee_ics_file(self):
        # Testing action_send_attendee_ics_file
        self.calendar_event.action_send_attendee_ics_file()

    def test_action_send_attendee_ics_file_no_date(self):
        # Create an in-memory event without start or stop date
        # We use .new() to avoid database NOT NULL constraint violations
        event = self.CalendarEvent.new({
            'name': 'Test Event',
            'partner_ids': [(6, 0, [self.partner_1.id])],
            'start': False,
        })
        with self.assertRaises(UserError):
            event.action_send_attendee_ics_file()
