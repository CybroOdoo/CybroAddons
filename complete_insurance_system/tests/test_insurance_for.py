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


class TestInsuranceFor(TransactionCase):
    """Test cases for the insurance.for model.

    Covers CRUD operations and field validation for the entity/purpose
    for which an insurance policy is purchased.
    """

    def setUp(self):
        super().setUp()

    def test_create_insurance_for(self):
        """An insurance.for record must be creatable with a valid name."""
        insurance_for = self.env['insurance.for'].create(
            {'name': 'Individual'})
        self.assertTrue(insurance_for.id,
                        "insurance.for record should be created successfully.")
        self.assertEqual(insurance_for.name, 'Individual')


    def test_insurance_for_name_required(self):
        """Creating an insurance.for record without a name must raise an error."""
        with self.assertRaises(Exception):
            self.env['insurance.for'].create({'name': False})


    def test_insurance_for_update_name(self):
        """An insurance.for record name must be updatable."""
        insurance_for = self.env['insurance.for'].create(
            {'name': 'Family'})
        insurance_for.write({'name': 'Corporate Group'})
        self.assertEqual(insurance_for.name, 'Corporate Group',
                         "insurance.for name should be updated correctly.")


    def test_insurance_for_delete(self):
        """An insurance.for record must be deletable."""
        insurance_for = self.env['insurance.for'].create(
            {'name': 'Temp Entry'})
        rec_id = insurance_for.id
        insurance_for.unlink()
        self.assertFalse(
            self.env['insurance.for'].search([('id', '=', rec_id)]),
            "insurance.for record should be deleted.")


    def test_insurance_for_search(self):
        """Search on insurance.for should return the matching record."""
        self.env['insurance.for'].create({'name': 'Senior Citizens'})
        results = self.env['insurance.for'].search(
            [('name', '=', 'Senior Citizens')])
        self.assertEqual(len(results), 1,
                         "Should find exactly one matching insurance.for record.")


    def test_insurance_for_multiple_records(self):
        """Multiple distinct insurance.for records must be storable."""
        names = ['Individual', 'Family', 'Group']
        for name in names:
            self.env['insurance.for'].create({'name': name})
        count = self.env['insurance.for'].search_count(
            [('name', 'in', names)])
        self.assertEqual(count, len(names),
                         "All insurance.for records must be stored.")

