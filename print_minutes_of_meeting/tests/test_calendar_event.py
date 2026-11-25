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
"""Unit tests for CalendarEvent and related meeting models."""
from unittest.mock import patch
from odoo.tests.common import TransactionCase


class TestCalendarEvent(TransactionCase):
    """Test suite for CalendarEvent model extensions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref('base.group_user')
        cls.user_responsible = cls.env['res.users'].create({
            'name': 'Test Responsible User',
            'login': 'test_responsible_user_unique',
            'email': 'responsible_test@example.com',
            'group_ids': [(4, group_user.id)],
        })
        cls.user_other = cls.env['res.users'].create({
            'name': 'Test Other User',
            'login': 'test_other_user_unique',
            'email': 'other_test@example.com',
            'group_ids': [(4, group_user.id)],
        })

        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Meeting Partner 1',
            'email': 'partner1@example.com',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Meeting Partner 2',
            'email': 'partner2@example.com',
        })
        cls.partner_3 = cls.env['res.partner'].create({
            'name': 'Meeting Partner 3',
            'email': 'partner3@example.com',
        })

        cls.event = cls.env['calendar.event'].create({
            'name': 'Test Meeting',
            'start': '2026-06-01 10:00:00',
            'stop': '2026-06-01 11:00:00',
            'responsible_user_id': cls.user_responsible.id,
            'partner_ids': [
                (4, cls.partner_1.id),
                (4, cls.partner_2.id),
                (4, cls.partner_3.id),
            ],
        })

    def test_responsible_user_id_field_assignment(self):
        """responsible_user_id should match assigned user."""
        self.assertEqual(
            self.event.responsible_user_id.id,
            self.user_responsible.id,
        )

    def test_note_taker_id_field_assignment(self):
        """note_taker_id should accept a partner from partner_ids."""
        self.event.note_taker_id = self.partner_1.id
        self.assertEqual(
            self.event.note_taker_id.id,
            self.partner_1.id,
        )

    def test_absent_member_ids_field_assignment(self):
        """absent_member_ids should store absent attendees."""
        self.event.absent_member_ids = [
            (6, 0, [self.partner_2.id, self.partner_3.id])
        ]
        self.assertIn(self.partner_2, self.event.absent_member_ids)
        self.assertIn(self.partner_3, self.event.absent_member_ids)
        self.assertNotIn(self.partner_1, self.event.absent_member_ids)

    def test_notes_field_html(self):
        """notes field should store HTML formatted conclusions."""
        html_content = (
            "<p>Meeting concluded with <strong>positive</strong> feedback.</p>"
        )
        self.event.notes = html_content
        self.assertEqual(self.event.notes, html_content)

    def test_compute_is_user_true_when_responsible(self):
        """is_user should be True when logged-in user is responsible."""
        event = self.event.with_user(self.user_responsible)
        self.assertTrue(event.is_user)

    def test_compute_is_user_false_for_other_user(self):
        """is_user should be False when user is not responsible."""
        event = self.event.with_user(self.user_other)
        self.assertFalse(event.is_user)

    def test_compute_is_user_false_when_no_responsible(self):
        """is_user should be False when responsible_user_id is empty."""
        event = self.env['calendar.event'].create({
            'name': 'No Responsible Meeting',
            'start': '2026-07-01 09:00:00',
            'stop': '2026-07-01 10:00:00',
        })
        self.assertFalse(event.is_user)

    def test_compute_is_user_updates_on_responsible_change(self):
        """is_user should recompute when responsible_user_id changes."""
        event = self.event.with_user(self.user_responsible)
        self.assertTrue(event.is_user)

        self.event.responsible_user_id = self.user_other.id
        event_refreshed = self.event.with_user(self.user_responsible)
        self.assertFalse(event_refreshed.is_user)
        self.event.responsible_user_id = self.user_responsible.id

    def test_action_send_mail_calls_render_pdf(self):
        """action_send_mail should call _render_qweb_pdf with correct ref."""
        fake_pdf = b'%PDF-1.4 fake'
        with patch.object(
            type(self.env['ir.actions.report']),
            '_render_qweb_pdf',
            return_value=(fake_pdf, 'pdf'),
        ) as mock_render, patch.object(
            type(self.env['mail.template']),
            'send_mail',
            return_value=True,
        ):
            self.event.action_send_mail()
            mock_render.assert_called_once()
            self.assertIn(
                'print_minutes_of_meeting.action_minutes_of_meeting_report',
                str(mock_render.call_args),
            )

    def test_action_send_mail_creates_attachment(self):
        """action_send_mail should create an ir.attachment record."""
        fake_pdf = b'%PDF-1.4 fake'
        with patch.object(
            type(self.env['ir.actions.report']),
            '_render_qweb_pdf',
            return_value=(fake_pdf, 'pdf'),
        ), patch.object(
            type(self.env['mail.template']),
            'send_mail',
            return_value=True,
        ):
            self.event.action_send_mail()

        created_attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'calendar.event'),
            ('res_id', '=', self.event.id),
            ('name', '=', 'Minutes of Meeting.pdf'),
        ], order='id desc', limit=1)
        self.assertTrue(created_attachment)
        self.assertEqual(bytes(created_attachment.raw), fake_pdf)

    def test_action_send_mail_attachment_cleaned_up(self):
        """action_send_mail should remove previous meeting attachments."""
        fake_pdf = b'%PDF-1.4 fake'
        with patch.object(
            type(self.env['ir.actions.report']),
            '_render_qweb_pdf',
            return_value=(fake_pdf, 'pdf'),
        ), patch.object(
            type(self.env['mail.template']),
            'send_mail',
            return_value=True,
        ):
            self.event.action_send_mail()
            self.event.action_send_mail()

        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'calendar.event'),
            ('res_id', '=', self.event.id),
            ('name', '=', 'Minutes of Meeting.pdf'),
        ])
        self.assertEqual(len(attachments), 1)


class TestMeetingAgenda(TransactionCase):
    """Test suite for MeetingAgenda model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env['calendar.event'].create({
            'name': 'Agenda Test Meeting',
            'start': '2026-06-10 14:00:00',
            'stop': '2026-06-10 15:00:00',
        })

    def test_create_agenda(self):
        """Can create an agenda item linked to an event."""
        agenda = self.env['meeting.agenda'].create({
            'topic': 'Budget Review',
            'description': 'Q3 Budget allocation discussion',
            'is_discussed': False,
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(agenda.topic, 'Budget Review')
        self.assertEqual(agenda.description, 'Q3 Budget allocation discussion')
        self.assertFalse(agenda.is_discussed)
        self.assertEqual(agenda.calendar_event_id.id, self.event.id)

    def test_agenda_display_name_is_topic(self):
        """_rec_name is 'topic', so display_name should match topic."""
        agenda = self.env['meeting.agenda'].create({
            'topic': 'Product Roadmap',
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(agenda.display_name, 'Product Roadmap')

    def test_multiple_agendas_per_event(self):
        """An event can have multiple agenda lines."""
        topics = ['Topic A', 'Topic B', 'Topic C']
        for t in topics:
            self.env['meeting.agenda'].create({
                'topic': t,
                'calendar_event_id': self.event.id,
            })
        self.assertEqual(len(self.event.agenda_ids), len(topics))


class TestMeetingActions(TransactionCase):
    """Test suite for MeetingActions model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Action Partner A',
            'email': 'partner_a@example.com',
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Action Partner B',
            'email': 'partner_b@example.com',
        })

        cls.event = cls.env['calendar.event'].create({
            'name': 'Actions Test Meeting',
            'start': '2026-06-15 09:00:00',
            'stop': '2026-06-15 10:00:00',
            'partner_ids': [(4, cls.partner_a.id), (4, cls.partner_b.id)],
        })
        cls.agenda = cls.env['meeting.agenda'].create({
            'topic': 'Action Item Discussion',
            'calendar_event_id': cls.event.id,
        })

    def test_create_action(self):
        """Can create an action record with all fields."""
        action = self.env['meeting.actions'].create({
            'action': 'Draft Q3 report',
            'description': 'Summarize all Q3 metrics and share with team',
            'agenda_item_id': self.agenda.id,
            'responsible_partner_id': self.partner_a.id,
            'assigned_partner_ids': [
                (6, 0, [self.partner_a.id, self.partner_b.id])
            ],
            'calendar_event_id': self.event.id,
            'deadline': '2026-07-01',
        })
        self.assertEqual(action.action, 'Draft Q3 report')
        self.assertEqual(action.responsible_partner_id.id, self.partner_a.id)
        self.assertEqual(str(action.deadline), '2026-07-01')

    def test_responsible_partner_domain(self):
        """Domain should return partner IDs in event.partner_ids."""
        action = self.env['meeting.actions'].create({
            'action': 'Domain check',
            'calendar_event_id': self.event.id,
        })
        domain = action._responsible_partner_id_domain()
        self.assertEqual(
            domain,
            [('id', 'in', [self.partner_a.id, self.partner_b.id])],
        )

    def test_action_linked_to_event(self):
        """Actions should appear in event.actions_ids."""
        action = self.env['meeting.actions'].create({
            'action': 'Follow-up call',
            'calendar_event_id': self.event.id,
        })
        self.assertIn(action, self.event.actions_ids)

    def test_action_linked_to_agenda_item(self):
        """Action can optionally reference an agenda item."""
        action = self.env['meeting.actions'].create({
            'action': 'Check analytics',
            'agenda_item_id': self.agenda.id,
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(action.agenda_item_id.id, self.agenda.id)

    def test_assigned_partners_many2many(self):
        """assigned_partner_ids can store multiple partners."""
        action = self.env['meeting.actions'].create({
            'action': 'Review code',
            'assigned_partner_ids': [
                (6, 0, [self.partner_a.id, self.partner_b.id])
            ],
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(len(action.assigned_partner_ids), 2)
        self.assertIn(self.partner_a, action.assigned_partner_ids)
        self.assertIn(self.partner_b, action.assigned_partner_ids)

    def test_deadline_field(self):
        """deadline field should correctly store a Date."""
        action = self.env['meeting.actions'].create({
            'action': 'Submit paperwork',
            'deadline': '2026-12-31',
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(str(action.deadline), '2026-12-31')

    def test_action_without_deadline(self):
        """deadline is optional; creating an action without it succeeds."""
        action = self.env['meeting.actions'].create({
            'action': 'No deadline action',
            'calendar_event_id': self.event.id,
        })
        self.assertFalse(action.deadline)


class TestMeetingSecurity(TransactionCase):
    """Test suite for access rights and record rules on meeting models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref('base.group_user')
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Security Test Internal User',
            'login': 'test_internal_user_security_unique',
            'email': 'internal_sec_test@example.com',
            'group_ids': [(4, group_user.id)],
        })
        cls.user_owner = cls.env['res.users'].create({
            'name': 'Security Test Owner User',
            'login': 'test_owner_user_security_unique',
            'email': 'owner_sec_test@example.com',
            'group_ids': [(4, group_user.id)],
        })
        cls.event = cls.env['calendar.event'].create({
            'name': 'Security Test Meeting',
            'start': '2026-06-20 10:00:00',
            'stop': '2026-06-20 11:00:00',
        })

    def test_internal_user_can_create_and_read_agenda(self):
        """Internal user can create and read agenda."""
        agenda = self.env['meeting.agenda'].with_user(
            self.user_internal
        ).create({
            'topic': 'Security Test Agenda',
            'calendar_event_id': self.event.id,
        })
        self.assertTrue(agenda.id)
        self.assertTrue(
            self.env['meeting.agenda'].with_user(
                self.user_internal
            ).has_access('create')
        )
        self.assertTrue(
            self.env['meeting.agenda'].with_user(
                self.user_internal
            ).has_access('write')
        )

    def test_internal_user_can_create_and_read_actions(self):
        """Internal user can create and read actions."""
        action = self.env['meeting.actions'].with_user(
            self.user_internal
        ).create({
            'action': 'Security Test Action',
            'calendar_event_id': self.event.id,
        })
        self.assertTrue(action.id)
        self.assertTrue(
            self.env['meeting.actions'].with_user(
                self.user_internal
            ).has_access('create')
        )
        self.assertTrue(
            self.env['meeting.actions'].with_user(
                self.user_internal
            ).has_access('write')
        )

    def test_private_event_agenda_record_rule(self):
        """Non-attendee cannot see agenda of a private event."""
        private_event = self.env['calendar.event'].with_user(
            self.user_owner
        ).create({
            'name': 'Confidential Meeting',
            'start': '2026-07-01 10:00:00',
            'stop': '2026-07-01 11:00:00',
            'privacy': 'private',
            'partner_ids': [(4, self.user_owner.partner_id.id)],
        })
        agenda = self.env['meeting.agenda'].with_user(
            self.user_owner
        ).create({
            'topic': 'Confidential Topic',
            'calendar_event_id': private_event.id,
        })
        # Non-attendee search should not return the private agenda
        agendas_seen = self.env['meeting.agenda'].with_user(
            self.user_internal
        ).search([('id', '=', agenda.id)])
        self.assertFalse(agendas_seen)

        # When attendee is added, the agenda becomes visible
        private_event.write({
            'partner_ids': [(4, self.user_internal.partner_id.id)],
        })
        agendas_seen_after = self.env['meeting.agenda'].with_user(
            self.user_internal
        ).search([('id', '=', agenda.id)])
        self.assertEqual(agendas_seen_after.ids, [agenda.id])

    def test_private_event_actions_record_rule(self):
        """Non-attendee cannot see actions of a private event."""
        private_event = self.env['calendar.event'].with_user(
            self.user_owner
        ).create({
            'name': 'Confidential Actions Meeting',
            'start': '2026-07-01 14:00:00',
            'stop': '2026-07-01 15:00:00',
            'privacy': 'private',
            'partner_ids': [(4, self.user_owner.partner_id.id)],
        })
        action = self.env['meeting.actions'].with_user(
            self.user_owner
        ).create({
            'action': 'Classified Task',
            'calendar_event_id': private_event.id,
        })
        # Non-attendee search should not return the private action
        actions_seen = self.env['meeting.actions'].with_user(
            self.user_internal
        ).search([('id', '=', action.id)])
        self.assertFalse(actions_seen)

        # When assigned to the action, it becomes visible
        action.write({
            'assigned_partner_ids': [(4, self.user_internal.partner_id.id)],
        })
        actions_seen_after = self.env['meeting.actions'].with_user(
            self.user_internal
        ).search([('id', '=', action.id)])
        self.assertEqual(actions_seen_after.ids, [action.id])
