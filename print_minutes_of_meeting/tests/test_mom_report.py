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
from odoo.tests.common import TransactionCase


class TestReportMinutesOfMeeting(TransactionCase):
    """Test suite for report/mom_report.py — ReportMinutesofMeeting abstract model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env[
            'report.print_minutes_of_meeting.report_mom_template'
        ]

        # Reuse existing partners and users — avoids triggering NOT NULL
        # constraints on res.partner columns added at the DB level by installed
        # modules (e.g. autopost_bills from account in Odoo 19).
        cls.partner_1 = cls.env.ref('base.res_partner_1')
        cls.partner_2 = cls.env.ref('base.res_partner_2')
        cls.responsible_user = cls.env.ref('base.user_demo')

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

    # -------------------------------------------------------------------------
    # _get_report_values — return structure
    # -------------------------------------------------------------------------

    def test_get_report_values_returns_dict(self):
        """_get_report_values should return a dictionary."""
        result = self.report_model._get_report_values([self.event_1.id])
        self.assertIsInstance(result, dict, "Result should be a dict.")

    def test_get_report_values_doc_ids_key(self):
        """Result dict should contain 'doc_ids' matching the input ids."""
        ids = [self.event_1.id]
        result = self.report_model._get_report_values(ids)
        self.assertIn('doc_ids', result)
        self.assertEqual(result['doc_ids'], ids)

    def test_get_report_values_doc_model_key(self):
        """Result dict should contain 'doc_model' set to 'calendar.event'."""
        result = self.report_model._get_report_values([self.event_1.id])
        self.assertIn('doc_model', result)
        self.assertEqual(result['doc_model'], 'calendar.event')

    def test_get_report_values_docs_key(self):
        """Result dict should contain 'docs' as a recordset of calendar.event."""
        result = self.report_model._get_report_values([self.event_1.id])
        self.assertIn('docs', result)
        self.assertIn(self.event_1, result['docs'])

    def test_get_report_values_data_key_default_none(self):
        """When data is not passed, result['data'] should be None."""
        result = self.report_model._get_report_values([self.event_1.id])
        self.assertIn('data', result)
        self.assertIsNone(result['data'])

    def test_get_report_values_data_key_passed_through(self):
        """When a data dict is passed it should be returned unchanged."""
        custom_data = {'extra': 'value', 'count': 42}
        result = self.report_model._get_report_values(
            [self.event_1.id], data=custom_data
        )
        self.assertEqual(result['data'], custom_data)

    # -------------------------------------------------------------------------
    # _get_report_values — multiple records
    # -------------------------------------------------------------------------

    def test_get_report_values_multiple_events(self):
        """_get_report_values should handle a list of multiple event IDs."""
        ids = [self.event_1.id, self.event_2.id]
        result = self.report_model._get_report_values(ids)
        self.assertEqual(len(result['docs']), 2)
        self.assertIn(self.event_1, result['docs'])
        self.assertIn(self.event_2, result['docs'])

    def test_get_report_values_docs_matches_doc_ids(self):
        """Each id in doc_ids should correspond to a record in docs."""
        ids = [self.event_1.id, self.event_2.id]
        result = self.report_model._get_report_values(ids)
        returned_ids = result['docs'].ids
        for doc_id in result['doc_ids']:
            self.assertIn(doc_id, returned_ids)

    # -------------------------------------------------------------------------
    # _get_report_values — edge cases
    # -------------------------------------------------------------------------

    def test_get_report_values_empty_ids(self):
        """_get_report_values with an empty list should return an empty recordset."""
        result = self.report_model._get_report_values([])
        self.assertEqual(len(result['docs']), 0)
        self.assertEqual(result['doc_ids'], [])

    def test_get_report_values_docs_contains_event_fields(self):
        """Docs recordset should expose fields added by the module."""
        result = self.report_model._get_report_values([self.event_1.id])
        doc = result['docs'][0]
        for field in ('responsible_user_id', 'note_taker_id',
                      'absent_member_ids', 'agenda_ids', 'actions_ids', 'notes'):
            self.assertTrue(
                hasattr(doc, field),
                f"Expected field '{field}' on the docs record.",
            )

    def test_get_report_values_docs_reflects_event_data(self):
        """Docs should reflect the actual data stored on the calendar.event."""
        result = self.report_model._get_report_values([self.event_1.id])
        doc = result['docs'][0]
        self.assertEqual(doc.name, 'Report Meeting One')
        self.assertEqual(doc.responsible_user_id, self.responsible_user)
        self.assertEqual(doc.notes, '<p>Some conclusions</p>')