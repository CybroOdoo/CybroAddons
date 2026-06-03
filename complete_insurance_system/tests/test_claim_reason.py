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


class TestClaimReason(TransactionCase):
    """Test cases for the claim.reason model.

    Covers field creation, color handling, unique-name SQL constraint,
    and basic CRUD operations.
    """

    def setUp(self):
        super().setUp()

    def test_create_claim_reason(self):
        """A claim reason must be creatable with a valid name."""
        reason = self.env['claim.reason'].create({'name': 'Fire Damage'})
        self.assertTrue(reason.id,
                        "Claim reason should be created successfully.")
        self.assertEqual(reason.name, 'Fire Damage')

    def test_claim_reason_default_color(self):
        """Color field should default to 0 when not provided."""
        reason = self.env['claim.reason'].create({'name': 'Theft'})
        self.assertEqual(reason.color, 0,
                         "Default color for a claim reason should be 0.")

    def test_claim_reason_color_can_be_set(self):
        """Color field must accept an explicit integer value."""
        reason = self.env['claim.reason'].create(
            {'name': 'Flood Damage', 'color': 5})
        self.assertEqual(reason.color, 5,
                         "Color should be stored as provided.")

    def test_claim_reason_unique_name_constraint(self):
        """Creating two claim reasons with the same name must raise an error."""
        self.env['claim.reason'].create({'name': 'Natural Disaster'})
        with self.assertRaises(Exception):
            self.env['claim.reason'].create({'name': 'Natural Disaster'})

    def test_claim_reason_name_required(self):
        """Creating a claim reason without a name must raise an error."""
        with self.assertRaises(Exception):
            self.env['claim.reason'].create({'name': False})

    def test_claim_reason_update_name(self):
        """A claim reason name must be updatable."""
        reason = self.env['claim.reason'].create({'name': 'Initial Reason'})
        reason.write({'name': 'Updated Reason'})
        self.assertEqual(reason.name, 'Updated Reason',
                         "Claim reason name should be updated correctly.")

    def test_claim_reason_delete(self):
        """A claim reason must be deletable when no claims reference it."""
        reason = self.env['claim.reason'].create({'name': 'Temporary Reason'})
        reason_id = reason.id
        reason.unlink()
        self.assertFalse(
            self.env['claim.reason'].search([('id', '=', reason_id)]),
            "Claim reason should be deleted.")

    def test_claim_reason_search(self):
        """Search on claim.reason should return matching records."""
        self.env['claim.reason'].create({'name': 'Storm Damage'})
        results = self.env['claim.reason'].search(
            [('name', '=', 'Storm Damage')])
        self.assertEqual(len(results), 1,
                         "Should find exactly one matching claim reason.")
