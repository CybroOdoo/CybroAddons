# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo.tests.common import TransactionCase

class TestCustomRestaurantTable(TransactionCase):

    def setUp(self):
        super(TestCustomRestaurantTable, self).setUp()
        self.floor = self.env['restaurant.floor'].create({'name': 'Main Floor'})
        self.table = self.env['restaurant.table'].create({
            'floor_id': self.floor.id,
            'table_number': 10,
        })

    def test_load_pos_data_fields(self):
        """Test if custom_table_name is included in POS data fields."""
        fields = self.env['restaurant.table']._load_pos_data_fields({})
        self.assertIn('custom_table_name', fields, "custom_table_name should be in POS data fields")

    def test_create_custom_table_name(self):
        """Test if custom_table_name is correctly set on creation."""
        # Case 1: custom_table_name not provided, should default to table_number
        table1 = self.env['restaurant.table'].create({
            'floor_id': self.floor.id,
            'table_number': 101,
        })
        self.assertEqual(table1.custom_table_name, '101', "custom_table_name should default to table_number")

        # Case 2: custom_table_name provided
        table2 = self.env['restaurant.table'].create({
            'floor_id': self.floor.id,
            'table_number': 102,
            'custom_table_name': 'VIP-1',
        })
        self.assertEqual(table2.custom_table_name, 'VIP-1', "custom_table_name should be set as provided")

    def test_compute_display_name(self):
        """Test the display_name computation."""
        # Case 1: Custom name with floor
        self.table.custom_table_name = 'T-10'
        self.assertEqual(self.table.display_name, 'Main Floor, T-10', "Display name should include floor and custom table name")

        # Case 2: No custom name (defaults to table number) with floor
        self.table.custom_table_name = False
        # Trigger recompute
        self.table._compute_display_name()
        self.assertEqual(self.table.display_name, 'Main Floor, 10', "Display name should include floor and table number if custom name is missing")

        # Case 3: Custom name without floor
        self.table.floor_id = False
        self.table.custom_table_name = 'T-10'
        self.assertEqual(self.table.display_name, 'T-10', "Display name should only be custom name if floor is missing")

    def test_write_custom_table_name(self):
        """Test if custom_table_name updates when table_number changes."""
        # Case 1: Name tracks number
        table = self.env['restaurant.table'].create({
            'table_number': 20,
        })
        self.assertEqual(table.custom_table_name, '20')
        
        table.write({'table_number': 21})
        self.assertEqual(table.custom_table_name, '21', "custom_table_name should update to match new table_number")

        # Case 2: Name does NOT track number
        table.write({'custom_table_name': 'Custom-21'})
        table.write({'table_number': 22})
        self.assertEqual(table.custom_table_name, 'Custom-21', "custom_table_name should NOT update if it's different from previous table_number")
