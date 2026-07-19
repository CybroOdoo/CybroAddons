# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA(odoo@cybrosys.com)
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
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRestaurantTable(TransactionCase):
    """Test cases for the pos_table_name module."""

    def setUp(self):
        """Set up test environment data (floor and a default table record)."""
        super(TestRestaurantTable, self).setUp()
        # Create a Floor
        self.floor = self.env['restaurant.floor'].create({
            'name': 'Main Floor',
        })
        # Create a Table
        self.table = self.env['restaurant.table'].create({
            'table_number': 1,
            'floor_id': self.floor.id,
            'table_alias': 'VIP-1',
            'shape': 'square',
        })

    def test_load_pos_data_fields(self):
        """Test _load_pos_data_fields of restaurant.table."""
        # Mocking config as it might be needed by super()
        config = self.env['pos.config'].create({'name': 'Test Config'})
        fields = self.env['restaurant.table']._load_pos_data_fields(config)
        self.assertIn('table_alias', fields, "table_alias should be in loaded fields")

    def test_compute_display_name(self):
        """Test _compute_display_name of restaurant.table."""
        # Case 1: With alias and floor
        self.assertEqual(self.table.display_name, "VIP-1 @ Main Floor")

        # Case 2: Without alias, with floor
        table_no_alias = self.env['restaurant.table'].create({
            'table_number': 2,
            'floor_id': self.floor.id,
            'shape': 'square',
        })
        self.assertEqual(table_no_alias.display_name, "2 @ Main Floor")

        # Case 3: Without alias, without floor (though floor is usually required in restaurant POS)
        table_no_floor = self.env['restaurant.table'].create({
            'table_number': 3,
            'shape': 'square',
        })
        # Note: the code does: label = row.table_alias if row.table_alias else str(row.table_number)
        # then display_name = f"{label} @ {row.floor_id.name}" if row.floor_id else label
        # In this case, table_alias is auto-assigned to '3' by create()
        self.assertEqual(table_no_floor.display_name, "3")

    def test_create_auto_alias(self):
        """Test create method auto-assignment logic."""
        # Create a table without number or alias
        table = self.env['restaurant.table'].create({
            'floor_id': self.floor.id,
            'shape': 'square',
        })
        
        # Since self.table (number 1) exists, this should be number 2
        self.assertEqual(table.table_number, 2, "Table number should be auto-incremented")
        self.assertEqual(table.table_alias, '2', "Table alias should be set to table number string")

        # Create another table with specific number but no alias
        table_with_num = self.env['restaurant.table'].create({
            'floor_id': self.floor.id,
            'table_number': 10,
            'shape': 'square',
        })
        self.assertEqual(table_with_num.table_alias, '10', "Table alias should match table number")
