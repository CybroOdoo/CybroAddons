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
class TestHrShortlistLine(TransactionCase):
    """
    Test suite for hr_shortlist_line.py (HrShortlistLine model).

    Covers:
        - Record creation with all fields
        - Many2one relationship with hr.shortlist
        - name, score field read/write
        - Record unlink
        - Search by criterion fields
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Parent shortlisting configuration
        cls.shortlist = cls.env['hr.shortlist'].create({
            'name': 'Backend Developer Criteria',
        })
        # A default line used across tests
        cls.line = cls.env['hr.shortlist.line'].create({
            'name': 'Python Expertise',
            'score': 40,
            'hr_shortlist_id': cls.shortlist.id,
        })

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_create_line_with_all_fields(self):
        """hr.shortlist.line should be creatable with name, score and parent."""
        line = self.env['hr.shortlist.line'].create({
            'name': 'Django Framework',
            'score': 20,
            'hr_shortlist_id': self.shortlist.id,
        })
        self.assertTrue(line.id, "Line should have a valid id after creation.")
        self.assertEqual(line.name, 'Django Framework')
        self.assertEqual(line.score, 20)
        self.assertEqual(line.hr_shortlist_id, self.shortlist)

    def test_create_line_without_parent(self):
        """hr.shortlist.line can be created without a parent shortlist."""
        line = self.env['hr.shortlist.line'].create({
            'name': 'Standalone Criterion',
            'score': 10,
        })
        self.assertTrue(line.id)
        self.assertFalse(
            line.hr_shortlist_id,
            "hr_shortlist_id should be empty when not provided.",
        )

    def test_create_line_zero_score(self):
        """hr.shortlist.line score should accept 0."""
        line = self.env['hr.shortlist.line'].create({
            'name': 'Optional Skill',
            'score': 0,
            'hr_shortlist_id': self.shortlist.id,
        })
        self.assertEqual(line.score, 0)

    def test_line_belongs_to_parent_shortlist(self):
        """hr_shortlist_id on the line should point to the correct parent."""
        self.assertEqual(
            self.line.hr_shortlist_id,
            self.shortlist,
            "Line's hr_shortlist_id must reference the parent hr.shortlist.",
        )

    def test_line_appears_in_parent_one2many(self):
        """A line should be accessible from the parent's hr_shortlist_line_ids."""
        self.assertIn(
            self.line,
            self.shortlist.hr_shortlist_line_ids,
            "Line should appear in the parent shortlist's hr_shortlist_line_ids.",
        )

    def test_update_line_name(self):
        """name field on hr.shortlist.line should be writable."""
        self.line.write({'name': 'Updated Python Expertise'})
        self.assertEqual(self.line.name, 'Updated Python Expertise')

    def test_update_line_score(self):
        """score field on hr.shortlist.line should be writable."""
        self.line.write({'score': 55})
        self.assertEqual(self.line.score, 55)

    def test_update_line_parent(self):
        """hr_shortlist_id on a line should be reassignable to a different parent."""
        new_parent = self.env['hr.shortlist'].create({'name': 'Frontend Criteria'})
        self.line.write({'hr_shortlist_id': new_parent.id})
        self.assertEqual(self.line.hr_shortlist_id, new_parent)

    def test_unlink_line(self):
        """hr.shortlist.line records should be deletable."""
        line = self.env['hr.shortlist.line'].create({
            'name': 'Delete Me',
            'score': 5,
            'hr_shortlist_id': self.shortlist.id,
        })
        line_id = line.id
        line.unlink()
        self.assertFalse(
            self.env['hr.shortlist.line'].browse(line_id).exists(),
            "Record should not exist after unlink().",
        )

    def test_search_line_by_name(self):
        """hr.shortlist.line records should be searchable by criterion name."""
        self.env['hr.shortlist.line'].create({
            'name': 'Unique Criterion XYZ',
            'score': 15,
            'hr_shortlist_id': self.shortlist.id,
        })
        results = self.env['hr.shortlist.line'].search([
            ('name', '=', 'Unique Criterion XYZ')
        ])
        self.assertTrue(results, "Search should return matching criterion lines.")

    def test_search_line_by_shortlist(self):
        """hr.shortlist.line records should be filterable by parent hr_shortlist_id."""
        results = self.env['hr.shortlist.line'].search([
            ('hr_shortlist_id', '=', self.shortlist.id)
        ])
        self.assertTrue(
            results,
            "Should find lines belonging to the test shortlist.",
        )

    def test_model_name(self):
        """Model _name should be 'hr.shortlist.line'."""
        self.assertEqual(
            self.env['hr.shortlist.line']._name,
            'hr.shortlist.line',
        )

    def test_model_description(self):
        """Model _description should not be empty."""
        self.assertTrue(self.env['hr.shortlist.line']._description)
