# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
from odoo.tests.common import TransactionCase

class TestWarehouseMapObject(TransactionCase):
    """Test suite for warehouse.map.object model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Map Warehouse',
            'code': 'MWH',
        })
        cls.layout = cls.env['warehouse.layout'].create({
            'name': 'Map Layout',
            'warehouse_id': cls.warehouse.id,
        })
        cls.map_object = cls.env['warehouse.map.object'].create({
            'name': 'Fire Extinguisher',
            'layout_id': cls.layout.id,
            'object_type': 'wall',
        })

    def test_01_onchange_object_type(self):
        """Test that changing object type updates defaults."""
        self.map_object.object_type = 'room'
        self.map_object._onchange_object_type()
        self.assertEqual(self.map_object.icon, '🚪')
        self.assertEqual(self.map_object.color, '#7F8C8D')
        self.assertEqual(self.map_object.size_x, 4)
        self.assertEqual(self.map_object.size_y, 3)
        
        self.map_object.object_type = 'wall'
        self.map_object._onchange_object_type()
        self.assertEqual(self.map_object.icon, '🧱')
        self.assertEqual(self.map_object.color, '#555555')
        self.assertEqual(self.map_object.size_x, 1)
        self.assertEqual(self.map_object.size_y, 1)
