# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
from odoo.tests.common import TransactionCase


class TestInsuredDocument(TransactionCase):
    """Test cases for the insured.document model.

    Covers CRUD operations, required name, unique constraint, color field,
    and search.
    """

    def setUp(self):
        super().setUp()

    def test_create_insured_document(self):
        """An insured document must be creatable with a valid name."""
        doc = self.env['insured.document'].create({'name': 'Passport'})
        self.assertTrue(doc.id,
                        "Insured document should be created successfully.")
        self.assertEqual(doc.name, 'Passport')


    def test_insured_document_default_color(self):
        """Color field should default to 0 when not provided."""
        doc = self.env['insured.document'].create({'name': 'Voter ID'})
        self.assertEqual(doc.color, 0,
                         "Default color for insured document should be 0.")


    def test_insured_document_color_can_be_set(self):
        """Color field must accept an explicit integer value."""
        doc = self.env['insured.document'].create(
            {'name': 'Driving License', 'color': 7})
        self.assertEqual(doc.color, 7)


    def test_insured_document_unique_name_constraint(self):
        """Creating two insured documents with the same name must raise an error."""
        self.env['insured.document'].create({'name': 'Aadhaar'})
        with self.assertRaises(Exception):
            self.env['insured.document'].create({'name': 'Aadhaar'})


    def test_insured_document_name_required(self):
        """Creating an insured document without a name must raise an error."""
        with self.assertRaises(Exception):
            self.env['insured.document'].create({'name': False})


    def test_insured_document_update(self):
        """An insured document name must be updatable."""
        doc = self.env['insured.document'].create({'name': 'Old Doc'})
        doc.write({'name': 'Updated Doc'})
        self.assertEqual(doc.name, 'Updated Doc')


    def test_insured_document_delete(self):
        """An insured document must be deletable."""
        doc = self.env['insured.document'].create({'name': 'Temp Document'})
        doc_id = doc.id
        doc.unlink()
        self.assertFalse(
            self.env['insured.document'].search([('id', '=', doc_id)]),
            "Insured document should be deleted.")


    def test_insured_document_search(self):
        """Search on insured.document should return the matching record."""
        self.env['insured.document'].create({'name': 'PAN Card'})
        results = self.env['insured.document'].search(
            [('name', '=', 'PAN Card')])
        self.assertEqual(len(results), 1,
                         "Should find exactly one insured document named 'PAN Card'.")

