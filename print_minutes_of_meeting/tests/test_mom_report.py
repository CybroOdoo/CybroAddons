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
"""Unit tests for report/mom_report.py."""
from odoo.tests.common import TransactionCase


class TestReportMinutesOfMeeting(TransactionCase):
    """Test suite for ReportMinutesofMeeting abstract model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env[
            'report.print_minutes_of_meeting.report_mom_template'
        ]

        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Report Partner 1',
            'email': 'report_p1@example.com',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Report Partner 2',
            'email': 'report_p2@example.com',
        })
        group_user = cls.env.ref('base.group_user')
        cls.responsible_user = cls.env['res.users'].create({
            'name': 'Report Responsible User',
            'login': 'report_resp_user_unique',
            'email': 'report_resp@example.com',
            'group_ids': [(4, group_user.id)],
        })

        cls.event_1 = cls.env['calendar.event'].create({
            'name': 'Report Meeting One',
            'start': '2026-06-01 10:00:00',
            'stop': '2026-06-01 11:00:00',
            'responsible_user_id': cls.responsible_user.id,
            'partner_ids': [(4, cls.partner_1.id), (4, cls.partner_2.id)],
            'notes': '<p>Some conclusions</p>',
        })
        cls.event_2 = cls.env['calendar.event'].create({
            'name': 'Report Meeting Two',
            'start': '2026-07-01 14:00:00',
            'stop': '2026-07-01 15:00:00',
        })

    def test_get_report_values_returns_dict(self):
        """_get_report_values should return a dict."""
        res = self.report_model._get_report_values(self.event_1.ids)
        self.assertIsInstance(res, dict)

    def test_get_report_values_doc_ids_key(self):
        """Result dict must contain 'doc_ids' matching passed docids."""
        docids = [self.event_1.id, self.event_2.id]
        res = self.report_model._get_report_values(docids)
        self.assertIn('doc_ids', res)
        self.assertEqual(res['doc_ids'], docids)

    def test_get_report_values_doc_model_key(self):
        """Result dict must specify 'calendar.event' as the doc_model."""
        res = self.report_model._get_report_values(self.event_1.ids)
        self.assertIn('doc_model', res)
        self.assertEqual(res['doc_model'], 'calendar.event')

    def test_get_report_values_docs_key(self):
        """Result dict must contain 'docs' as a recordset."""
        res = self.report_model._get_report_values(self.event_1.ids)
        self.assertIn('docs', res)
        self.assertEqual(res['docs'], self.event_1)

    def test_get_report_values_data_key_default_none(self):
        """When data argument is not provided, 'data' key should be None."""
        res = self.report_model._get_report_values(self.event_1.ids)
        self.assertIn('data', res)
        self.assertIsNone(res['data'])

    def test_get_report_values_data_key_passed_through(self):
        """Custom data dictionary should be forwarded in the result dict."""
        custom_data = {'context_lang': 'en_US', 'printed_by': 'Admin'}
        res = self.report_model._get_report_values(
            self.event_1.ids, data=custom_data
        )
        self.assertIn('data', res)
        self.assertEqual(res['data'], custom_data)

    def test_get_report_values_docs_matches_doc_ids(self):
        """docs recordset ids should match doc_ids."""
        docids = [self.event_1.id, self.event_2.id]
        res = self.report_model._get_report_values(docids)
        self.assertEqual(set(res['docs'].ids), set(docids))

    def test_get_report_values_docs_reflects_event_data(self):
        """docs in report values should reflect the actual event attributes."""
        res = self.report_model._get_report_values(self.event_1.ids)
        event_in_docs = res['docs']
        self.assertEqual(event_in_docs.name, 'Report Meeting One')
        self.assertEqual(
            event_in_docs.responsible_user_id, self.responsible_user
        )
        self.assertIn(self.partner_1, event_in_docs.partner_ids)
        self.assertIn(self.partner_2, event_in_docs.partner_ids)
        self.assertEqual(event_in_docs.notes, '<p>Some conclusions</p>')

    def test_get_report_values_multiple_events(self):
        """Should handle multiple events simultaneously."""
        docids = [self.event_1.id, self.event_2.id]
        res = self.report_model._get_report_values(docids)
        self.assertEqual(len(res['docs']), 2)
        names = res['docs'].mapped('name')
        self.assertIn('Report Meeting One', names)
        self.assertIn('Report Meeting Two', names)

    def test_get_report_values_empty_ids(self):
        """Empty docids list should produce empty docs recordset."""
        res = self.report_model._get_report_values([])
        self.assertEqual(len(res['docs']), 0)
        self.assertEqual(res['doc_ids'], [])

    def test_get_report_values_docs_contains_event_fields(self):
        """Event fields from print_minutes_of_meeting should be in docs."""
        self.env['meeting.agenda'].create({
            'topic': 'Report Agenda Topic',
            'calendar_event_id': self.event_1.id,
        })
        self.env['meeting.actions'].create({
            'action': 'Report Action Item',
            'calendar_event_id': self.event_1.id,
        })

        res = self.report_model._get_report_values(self.event_1.ids)
        event = res['docs']
        self.assertEqual(len(event.agenda_ids), 1)
        self.assertEqual(event.agenda_ids.topic, 'Report Agenda Topic')
        self.assertEqual(len(event.actions_ids), 1)
        self.assertEqual(event.actions_ids.action, 'Report Action Item')
