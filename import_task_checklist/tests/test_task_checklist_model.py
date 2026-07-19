# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################

from odoo.tests.common import TransactionCase


class TestTaskChecklistModel(TransactionCase):
    """Unit tests for the company_id extension on task.checklist."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    def setUp(self):
        super().setUp()
        self.Checklist = self.env['task.checklist']
        self.company   = self.env.company

    # ------------------------------------------------------------------
    # Field existence & metadata
    # ------------------------------------------------------------------
    def test_company_id_field_exists(self):
        """task.checklist must have a company_id field after module install."""
        field = self.Checklist._fields.get('company_id')
        self.assertIsNotNone(
            field,
            "company_id should be present on task.checklist after install."
        )

    def test_company_id_comodel_is_res_company(self):
        """company_id must reference res.company."""
        field = self.Checklist._fields['company_id']
        self.assertEqual(
            field.comodel_name, 'res.company',
            "company_id.comodel_name should be 'res.company'."
        )

    def test_company_id_field_type_is_many2one(self):
        """company_id must be a Many2one field."""
        from odoo.fields import Many2one
        self.assertIsInstance(
            self.Checklist._fields['company_id'],
            Many2one,
            "company_id should be a Many2one field."
        )

    # ------------------------------------------------------------------
    # Default value
    # ------------------------------------------------------------------
    def test_company_id_defaults_to_current_company(self):
        """New records should default company_id to env.company."""
        rec = self.Checklist.create({'name': 'Default Co Test'})
        self.assertEqual(
            rec.company_id, self.company,
            "company_id should default to the current company."
        )

    # ------------------------------------------------------------------
    # Explicit assignment & update
    # ------------------------------------------------------------------
    def test_company_id_explicit_create(self):
        """company_id should be persisted when set explicitly on create."""
        rec = self.Checklist.create({
            'name': 'Explicit Co',
            'company_id': self.company.id,
        })
        self.assertEqual(rec.company_id.id, self.company.id)

    def test_company_id_writable_after_create(self):
        """company_id should be updatable via write()."""
        rec = self.Checklist.create({'name': 'Writable Co'})
        second = self.env['res.company'].create({'name': 'Second Co (model test)'})
        rec.write({'company_id': second.id})
        self.assertEqual(rec.company_id.id, second.id)

    def test_company_id_accepts_false(self):
        """company_id should accept False (no company) without raising."""
        rec = self.Checklist.create({'name': 'No Co', 'company_id': False})
        self.assertFalse(rec.company_id)

    # ------------------------------------------------------------------
    # Base fields still work
    # ------------------------------------------------------------------
    def test_name_field_stored(self):
        """Base name field should still be stored correctly."""
        rec = self.Checklist.create({'name': 'Base Name Test'})
        self.assertEqual(rec.name, 'Base Name Test')

    def test_description_field_stored(self):
        """Base description field should persist after v19 migration."""
        rec = self.Checklist.create({
            'name': 'With Desc',
            'description': 'Some detailed description',
        })
        self.assertEqual(rec.description, 'Some detailed description')

    # ------------------------------------------------------------------
    # Multi-company isolation
    # ------------------------------------------------------------------
    def test_same_name_different_companies_allowed(self):
        """Two records with the same name under different companies must coexist."""
        co_a = self.env['res.company'].create({'name': 'Co A (model test)'})
        co_b = self.env['res.company'].create({'name': 'Co B (model test)'})
        rec_a = self.Checklist.create({'name': 'Shared', 'company_id': co_a.id})
        rec_b = self.Checklist.create({'name': 'Shared', 'company_id': co_b.id})
        self.assertNotEqual(rec_a.id, rec_b.id)
        self.assertEqual(rec_a.company_id.id, co_a.id)
        self.assertEqual(rec_b.company_id.id, co_b.id)

    def test_search_by_company(self):
        """Filtering task.checklist by company_id should return correct subset."""
        co_x = self.env['res.company'].create({'name': 'Co X (search test)'})
        rec = self.Checklist.create({'name': 'Co X Only', 'company_id': co_x.id})
        results = self.Checklist.search([
            ('name', '=', 'Co X Only'),
            ('company_id', '=', co_x.id),
        ])
        self.assertIn(rec, results)
