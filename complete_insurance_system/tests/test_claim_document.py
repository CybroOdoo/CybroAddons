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

class TestClaimDocument(TransactionCase):
    """Test cases for the claim.document model.

    Covers field validation, unique-name constraint, and basic CRUD operations.
    """

    def setUp(self):
        super().setUp()

    def test_create_claim_document(self):
        """A claim document must be creatable with a valid name."""
        doc = self.env['claim.document'].create({'name': 'Medical Certificate'})
        self.assertTrue(doc.id, "Claim document should be created successfully.")
        self.assertEqual(doc.name, 'Medical Certificate')

    def test_claim_document_default_color(self):
        """Color field should default to 0 when not provided."""
        doc = self.env['claim.document'].create({'name': 'Police Report'})
        self.assertEqual(doc.color, 0,
                         "Default color for a claim document should be 0.")

    def test_claim_document_color_can_be_set(self):
        """Color field must accept an explicit integer value."""
        doc = self.env['claim.document'].create(
            {'name': 'Lab Report', 'color': 3})
        self.assertEqual(doc.color, 3,
                         "Color should be stored as provided.")

    def test_claim_document_unique_name_constraint(self):
        """Creating two claim documents with the same name must raise an error."""
        self.env['claim.document'].create({'name': 'X-Ray Report'})
        with self.assertRaises(Exception):
            self.env['claim.document'].create({'name': 'X-Ray Report'})

    def test_claim_document_name_required(self):
        """Creating a claim document without a name must raise a ValidationError."""
        with self.assertRaises(Exception):
            self.env['claim.document'].create({'name': False})

    def test_claim_document_update_name(self):
        """A claim document name must be updatable."""
        doc = self.env['claim.document'].create({'name': 'Old Name'})
        doc.write({'name': 'New Name'})
        self.assertEqual(doc.name, 'New Name',
                         "Claim document name should be updated correctly.")

    def test_claim_document_delete(self):
        """A claim document must be deletable."""
        doc = self.env['claim.document'].create({'name': 'Temp Doc'})
        doc_id = doc.id
        doc.unlink()
        self.assertFalse(
            self.env['claim.document'].search([('id', '=', doc_id)]),
            "Claim document should be deleted.")
