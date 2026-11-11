# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (odoo@cybrosys.com)
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
###############################################################################
import io

import openpyxl

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools.binary import BinaryBytes


@tagged('post_install', '-at_install')
class TestImportChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login='cmc_importer', groups='base.group_user')
        cls.Checklist = cls.env['meeting.checklist']

    def _wizard(self, content, file_type='csv'):
        return self.env['import.meeting.checklist'].with_user(self.user).create({
            'file_type': file_type,
            'filename': 'checklist.%s' % ('csv' if file_type == 'csv' else 'xlsx'),
            'file_content': BinaryBytes(content) if content else False,
        })

    def _xlsx(self, rows):
        book = openpyxl.Workbook()
        for row in rows:
            book.active.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        return buffer.getvalue()

    def _names(self):
        return set(self.Checklist.search([]).mapped('name'))

    def test_csv_with_header(self):
        self.Checklist.create({'name': 'Bring slides', 'description': 'old'})
        result = self._wizard(
            b"name,description\nBring slides,new text\nBook room,Floor 2\n\n").action_import_meeting_checklist_csv()
        self.assertEqual(result['params']['type'], 'success')
        self.assertIn('Book room', self._names())
        self.assertEqual(self.Checklist.search([('name', '=', 'Bring slides')]).description, 'new text')
        self.assertEqual(self.Checklist.search_count([('name', '=', 'Bring slides')]), 1)

    def test_csv_without_header(self):
        self._wizard(b"Order lunch,For 8 people\nPrint agenda\n").action_import_meeting_checklist_csv()
        self.assertTrue({'Order lunch', 'Print agenda'} <= self._names())
        self.assertEqual(self.Checklist.search([('name', '=', 'Order lunch')]).description, 'For 8 people')

    def test_csv_with_external_ids(self):
        self._wizard(
            b"id,name,description\n__export__.cl_1,Check projector,HDMI\n").action_import_meeting_checklist_csv()
        record = self.Checklist.search([('name', '=', 'Check projector')])
        self.assertEqual(record.description, 'HDMI')

    def test_csv_columns_found_by_header_name(self):
        self._wizard(b"details,title\nSome notes,Send invites\n").action_import_meeting_checklist_csv()
        self.assertEqual(self.Checklist.search([('name', '=', 'Send invites')]).description, 'Some notes')

    def test_csv_empty_and_invalid(self):
        result = self._wizard(b"\n , \n").action_import_meeting_checklist_csv()
        self.assertEqual(result['params']['type'], 'warning')
        with self.assertRaises(UserError):
            self._wizard(b"\xff\xfe\x00bad").action_import_meeting_checklist_csv()
        with self.assertRaises(UserError):
            self._wizard(False).action_import_meeting_checklist_csv()

    def test_xlsx(self):
        content = self._xlsx([['Name', 'Description'], ['Water bottles', 'Six'], [None, None]])
        result = self._wizard(content, 'xls').action_import_meeting_checklist_xlsx()
        self.assertEqual(result['params']['type'], 'success')
        self.assertEqual(self.Checklist.search([('name', '=', 'Water bottles')]).description, 'Six')

    def test_xlsx_empty_and_invalid(self):
        result = self._wizard(self._xlsx([]), 'xls').action_import_meeting_checklist_xlsx()
        self.assertEqual(result['params']['type'], 'warning')
        with self.assertRaises(UserError):
            self._wizard(b"name,description\n", 'xls').action_import_meeting_checklist_xlsx()

    def test_import_runs_with_user_rights(self):
        """The import uses the user's own rights: no rights, no import."""
        self.env.ref('calendar_meeting_checklist.access_meeting_checklist_user').unlink()
        wizard = self._wizard(b"name\nShould not exist\n")
        with self.assertRaises(AccessError):
            wizard.action_import_meeting_checklist_csv()
        self.assertNotIn('Should not exist', self._names())

    def test_row_helpers(self):
        wizard = self.env['import.meeting.checklist']
        self.assertFalse(wizard._has_header([]))
        self.assertEqual(wizard._get_field_indices([]), (0, 1))
        self.assertEqual(wizard._get_field_indices(['id', 'something']), (1, None))
        self.assertEqual(wizard._extract_row_data([], 0, 1), (False, False))
        self.assertEqual(wizard._extract_row_data(['__import__.x'], 0, None), ('__import__.x', False))
        self.assertEqual(wizard._extract_row_data([None, 'Only name'], 1, None), ('Only name', False))
