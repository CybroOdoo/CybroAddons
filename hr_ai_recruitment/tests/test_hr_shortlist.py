# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
#
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
################################################################################

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'hr_ai_recruitment')
class TestHrShortlist(TransactionCase):
    """
    Test suite for hr_shortlist.py (HRShortlistConfig model).

    Covers:
        - Record creation with a name (required field)
        - Relationship with hr.shortlist.line (One2many)
        - name field constraint (required=True)
        - Record read, write, and unlink operations
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shortlist = cls.env['hr.shortlist'].create({
            'name': 'Python Developer Criteria 2026',
        })

    def test_create_shortlist_with_name(self):
        """hr.shortlist record should be creatable with a valid name."""
        record = self.env['hr.shortlist'].create({
            'name': 'Sales Role AI Criteria 2026',
        })
        self.assertTrue(record.id, "Record should be persisted with a valid id.")
        self.assertEqual(record.name, 'Sales Role AI Criteria 2026')

    def test_create_shortlist_name_required(self):
        """Creating an hr.shortlist without a name should raise an error."""
        with self.assertRaises(Exception):
            self.env['hr.shortlist'].create({})

    def test_shortlist_line_ids_initially_empty(self):
        """A new hr.shortlist should have no criteria lines by default."""
        new_sl = self.env['hr.shortlist'].create({'name': 'Empty Config'})
        self.assertFalse(new_sl.hr_shortlist_line_ids)

    def test_shortlist_with_criteria_lines(self):
        """Lines created against a shortlist appear in hr_shortlist_line_ids."""
        line = self.env['hr.shortlist.line'].create({
            'name': 'Python Skills',
            'score': 30,
            'hr_shortlist_id': self.shortlist.id,
        })
        self.assertIn(line, self.shortlist.hr_shortlist_line_ids)

    def test_shortlist_multiple_lines(self):
        """hr.shortlist supports multiple criteria lines."""
        for name, score in [('Communication', 20), ('Technical', 40)]:
            self.env['hr.shortlist.line'].create({
                'name': name,
                'score': score,
                'hr_shortlist_id': self.shortlist.id,
            })
        self.assertGreaterEqual(len(self.shortlist.hr_shortlist_line_ids), 2)

    def test_update_shortlist_name(self):
        """hr.shortlist name field should be writable."""
        self.shortlist.write({'name': 'Updated Criteria Name'})
        self.assertEqual(self.shortlist.name, 'Updated Criteria Name')

    def test_unlink_shortlist(self):
        """hr.shortlist record should be deletable."""
        record = self.env['hr.shortlist'].create({'name': 'To Be Deleted'})
        record_id = record.id
        record.unlink()
        self.assertFalse(self.env['hr.shortlist'].browse(record_id).exists())

    def test_search_shortlist_by_name(self):
        """hr.shortlist records should be searchable by name."""
        self.env['hr.shortlist'].create({'name': 'Unique Search 9999'})
        results = self.env['hr.shortlist'].search([('name', '=', 'Unique Search 9999')])
        self.assertTrue(results)

    def test_model_name(self):
        """Model _name should be 'hr.shortlist'."""
        self.assertEqual(self.env['hr.shortlist']._name, 'hr.shortlist')
