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


class TestNomineeRelation(TransactionCase):
    """Test cases for the nominee.relation model.

    Covers CRUD operations, required name field, unique SQL constraint,
    and search.
    """

    def setUp(self):
        super().setUp()

    def test_create_nominee_relation(self):
        """A nominee relation must be creatable with a valid name."""
        relation = self.env['nominee.relation'].create({'name': 'Spouse'})
        self.assertTrue(relation.id,
                        "Nominee relation should be created successfully.")
        self.assertEqual(relation.name, 'Spouse')


    def test_nominee_relation_name_required(self):
        """Creating a nominee relation without a name must raise an error."""
        with self.assertRaises(Exception):
            self.env['nominee.relation'].create({'name': False})


    def test_nominee_relation_unique_constraint(self):
        """Creating two nominee relations with the same name must raise an error."""
        self.env['nominee.relation'].create({'name': 'Parent'})
        with self.assertRaises(Exception):
            self.env['nominee.relation'].create({'name': 'Parent'})


    def test_nominee_relation_update(self):
        """A nominee relation name must be updatable."""
        relation = self.env['nominee.relation'].create({'name': 'Child'})
        relation.write({'name': 'Minor Child'})
        self.assertEqual(relation.name, 'Minor Child',
                         "Nominee relation name should be updated.")


    def test_nominee_relation_delete(self):
        """A nominee relation must be deletable when not referenced."""
        relation = self.env['nominee.relation'].create({'name': 'Sibling'})
        rel_id = relation.id
        relation.unlink()
        self.assertFalse(
            self.env['nominee.relation'].search([('id', '=', rel_id)]),
            "Nominee relation should be deleted.")


    def test_nominee_relation_search(self):
        """Search on nominee.relation should return the matching record."""
        self.env['nominee.relation'].create({'name': 'Grandparent'})
        results = self.env['nominee.relation'].search(
            [('name', '=', 'Grandparent')])
        self.assertEqual(len(results), 1,
                         "Should find exactly one 'Grandparent' relation.")


    def test_multiple_nominee_relations(self):
        """Multiple distinct nominee relations must be storable."""
        names = ['Uncle', 'Aunt', 'Cousin']
        for name in names:
            self.env['nominee.relation'].create({'name': name})
        count = self.env['nominee.relation'].search_count(
            [('name', 'in', names)])
        self.assertEqual(count, len(names),
                         "All nominee relations must be stored.")

