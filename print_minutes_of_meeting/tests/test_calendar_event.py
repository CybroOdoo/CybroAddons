# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)

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
##############################################################################
from unittest.mock import patch
from odoo.tests.common import TransactionCase


class TestCalendarEvent(TransactionCase):
    """Test suite for CalendarEvent model extensions in
    print_minutes_of_meeting module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reuse built-in users/partners to avoid any res.partner column
        # constraints introduced by installed modules (e.g. autopost_bills
        # added at DB level by the account module migration in Odoo 19).
        cls.user_responsible = cls.env.ref('base.user_demo')
        cls.user_other = cls.env.ref('base.user_admin')

        # Pull real partners that already exist in the DB
        cls.partner_1 = cls.env.ref('base.res_partner_1')
        cls.partner_2 = cls.env.ref('base.res_partner_2')
        cls.partner_3 = cls.env.ref('base.res_partner_3')

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

    # -------------------------------------------------------------------------
    # Field tests
    # -------------------------------------------------------------------------

    def test_responsible_user_id_field_assignment(self):
        """responsible_user_id should be stored and retrievable."""
        self.assertEqual(
            self.event.responsible_user_id,
            self.user_responsible,
            "responsible_user_id should match the assigned user.",
        )

    def test_note_taker_id_field_assignment(self):
        """note_taker_id should accept a partner from partner_ids."""
        self.event.note_taker_id = self.partner_1.id
        self.assertEqual(
            self.event.note_taker_id,
            self.partner_1,
            "note_taker_id should match the assigned partner.",
        )

    def test_absent_member_ids_field_assignment(self):
        """absent_member_ids should accept multiple partners from partner_ids."""
        self.event.absent_member_ids = [(6, 0, [self.partner_1.id, self.partner_2.id])]
        self.assertIn(self.partner_1, self.event.absent_member_ids)
        self.assertIn(self.partner_2, self.event.absent_member_ids)

    def test_notes_field_html(self):
        """notes field should store HTML content."""
        html_content = '<p>Meeting conclusion: <b>All tasks assigned.</b></p>'
        self.event.notes = html_content
        self.assertEqual(self.event.notes, html_content)

    def test_agenda_ids_one2many(self):
        """agenda_ids should link MeetingAgenda records to the event."""
        agenda = self.env['meeting.agenda'].create({
            'topic': 'Budget Review',
            'description': 'Review Q2 budget',
            'calendar_event_id': self.event.id,
        })
        self.assertIn(agenda, self.event.agenda_ids)

    def test_actions_ids_one2many(self):
        """actions_ids should link MeetingActions records to the event."""
        action = self.env['meeting.actions'].create({
            'action': 'Follow up with vendor',
            'description': 'Send follow-up email',
            'calendar_event_id': self.event.id,
        })
        self.assertIn(action, self.event.actions_ids)

    # -------------------------------------------------------------------------
    # Computed field: _compute_is_user
    # -------------------------------------------------------------------------

    def test_compute_is_user_true_when_responsible(self):
        """is_user should be True when the current user is the responsible user."""
        event = self.event.with_user(self.user_responsible)
        self.assertTrue(
            event.is_user,
            "is_user should be True for the responsible user.",
        )

    def test_compute_is_user_false_for_other_user(self):
        """is_user should be False when the current user is NOT the responsible user."""
        event = self.event.with_user(self.user_other)
        self.assertFalse(
            event.is_user,
            "is_user should be False for a non-responsible user.",
        )

    def test_compute_is_user_false_when_no_responsible(self):
        """is_user should be False when no responsible user is set."""
        event = self.env['calendar.event'].create({
            'name': 'No Responsible Meeting',
            'start': '2026-07-01 09:00:00',
            'stop': '2026-07-01 10:00:00',
        })
        self.assertFalse(
            event.is_user,
            "is_user should be False when responsible_user_id is empty.",
        )

    def test_compute_is_user_updates_on_responsible_change(self):
        """is_user should recompute when responsible_user_id changes."""
        event = self.event.with_user(self.user_responsible)
        self.assertTrue(event.is_user)

        self.event.responsible_user_id = self.user_other.id
        event_refreshed = self.event.with_user(self.user_responsible)
        self.assertFalse(
            event_refreshed.is_user,
            "is_user should update when responsible_user_id changes.",
        )
        # Reset
        self.event.responsible_user_id = self.user_responsible.id

    # -------------------------------------------------------------------------
    # action_send_mail
    # -------------------------------------------------------------------------

    def test_action_send_mail_calls_render_pdf(self):
        """action_send_mail should call _render_qweb_pdf with the correct report ref."""
        fake_pdf = b'%PDF-1.4 fake'
        with patch.object(
            type(self.env['ir.actions.report']),
            '_render_qweb_pdf',
            return_value=(fake_pdf, 'pdf'),
        ) as mock_render, \
        patch.object(
            type(self.env['mail.template']),
            'send_mail',
            return_value=True,
        ):
            self.event.action_send_mail()
            mock_render.assert_called_once()
            self.assertIn(
                'print_minutes_of_meeting.action_minutes_of_meeting_report',
                str(mock_render.call_args),
                "Should reference the correct report action.",
            )

    def test_action_send_mail_creates_attachment(self):
        """action_send_mail should create an ir.attachment record."""
        fake_pdf = b'%PDF-1.4 fake'
        count_before = self.env['ir.attachment'].search_count([
            ('name', '=', 'Minutes of Meeting'),
        ])
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

        count_after = self.env['ir.attachment'].search_count([
            ('name', '=', 'Minutes of Meeting'),
        ])
        self.assertGreater(
            count_after, count_before,
            "An ir.attachment record should be created during send_mail.",
        )

    def test_action_send_mail_attachment_cleaned_up(self):
        """action_send_mail should remove the attachment from the template after sending."""
        fake_pdf = b'%PDF-1.4 fake'
        template = self.env.ref(
            'print_minutes_of_meeting.email_template_minutes_of_meeting'
        )
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

        self.assertFalse(
            template.attachment_ids,
            "Template attachment_ids should be cleared after send_mail.",
        )


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
        """Should create a MeetingAgenda record with all fields."""
        agenda = self.env['meeting.agenda'].create({
            'topic': 'Project Kickoff',
            'description': 'Discuss project goals',
            'is_discussed': False,
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(agenda.topic, 'Project Kickoff')
        self.assertEqual(agenda.description, 'Discuss project goals')
        self.assertFalse(agenda.is_discussed)
        self.assertEqual(agenda.calendar_event_id, self.event)

    def test_agenda_display_name_is_topic(self):
        """MeetingAgenda _rec_name is 'topic', so display_name should equal topic."""
        agenda = self.env['meeting.agenda'].create({
            'topic': 'Risk Assessment',
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(agenda.display_name, 'Risk Assessment')

    def test_multiple_agendas_per_event(self):
        """Multiple agendas should be linkable to the same event."""
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
        # Reuse existing partners — avoids any res.partner NOT NULL constraints
        # introduced at the DB level by installed modules (e.g. account).
        cls.partner_a = cls.env.ref('base.res_partner_1')
        cls.partner_b = cls.env.ref('base.res_partner_2')

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
        """Should create a MeetingActions record with all fields."""
        action = self.env['meeting.actions'].create({
            'action': 'Prepare report',
            'description': 'Prepare Q2 report by Friday',
            'agenda_item_id': self.agenda.id,
            'responsible_partner_id': self.partner_a.id,
            'assigned_partner_ids': [(4, self.partner_b.id)],
            'calendar_event_id': self.event.id,
            'deadline': '2026-06-20',
        })
        self.assertEqual(action.action, 'Prepare report')
        self.assertEqual(action.responsible_partner_id, self.partner_a)
        self.assertIn(self.partner_b, action.assigned_partner_ids)
        self.assertEqual(str(action.deadline), '2026-06-20')

    def test_action_linked_to_event(self):
        """MeetingActions should be retrievable via event.actions_ids."""
        action = self.env['meeting.actions'].create({
            'action': 'Send invitation',
            'calendar_event_id': self.event.id,
        })
        self.assertIn(action, self.event.actions_ids)

    def test_action_linked_to_agenda_item(self):
        """MeetingActions agenda_item_id should reference a MeetingAgenda."""
        action = self.env['meeting.actions'].create({
            'action': 'Review agenda items',
            'agenda_item_id': self.agenda.id,
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(action.agenda_item_id, self.agenda)

    def test_responsible_partner_domain(self):
        """_responsible_partner_id_domain should return domain filtered by event partners."""
        action = self.env['meeting.actions'].create({
            'action': 'Domain check',
            'calendar_event_id': self.event.id,
        })
        domain = action._responsible_partner_id_domain()
        partner_ids_in_domain = domain[0][2]
        self.assertIn(self.partner_a.id, partner_ids_in_domain)
        self.assertIn(self.partner_b.id, partner_ids_in_domain)

    def test_assigned_partners_many2many(self):
        """assigned_partner_ids should accept multiple partners."""
        action = self.env['meeting.actions'].create({
            'action': 'Multi-assign test',
            'assigned_partner_ids': [
                (4, self.partner_a.id),
                (4, self.partner_b.id),
            ],
            'calendar_event_id': self.event.id,
        })
        self.assertEqual(len(action.assigned_partner_ids), 2)

    def test_deadline_field(self):
        """deadline should store and retrieve a date correctly."""
        from datetime import date
        action = self.env['meeting.actions'].create({
            'action': 'Deadline test',
            'calendar_event_id': self.event.id,
            'deadline': '2026-07-01',
        })
        self.assertEqual(action.deadline, date(2026, 7, 1))

    def test_action_without_deadline(self):
        """MeetingActions should be creatable without a deadline."""
        action = self.env['meeting.actions'].create({
            'action': 'No deadline action',
            'calendar_event_id': self.event.id,
        })
        self.assertFalse(action.deadline)