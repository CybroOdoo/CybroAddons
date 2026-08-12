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
from unittest.mock import MagicMock
from ..controllers.warehouse_3d_designer import WarehouseDesignerController
import odoo.addons.warehouse_3d_designer.controllers.warehouse_3d_designer as controller_module

class TestWarehouseDesignerController(TransactionCase):
    """Test suite for the Warehouse 3D Designer controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WarehouseDesignerController()
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Controller Warehouse',
            'code': 'CWH',
        })
        cls.layout = cls.env['warehouse.layout'].create({
            'name': 'Controller Layout',
            'warehouse_id': cls.warehouse.id,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Loc 1',
            'location_id': cls.warehouse.lot_stock_id.id,
            'layout_id': cls.layout.id,
        })

    def test_01_save_positions(self):
        """Test saving location positions via the controller."""
        positions = [{
            'id': self.location.id,
            'pos_x': 10,
            'pos_y': 20,
            'size_x': 4,
            'size_y': 2,
            'location_rotation': 90,
        }]
        
        # Manually mock request to avoid "object is not bound" from LocalProxy
        old_request = controller_module.request
        controller_module.request = MagicMock(env=self.env)
        try:
            self.controller.save_positions(self.layout.id, positions)
        finally:
            controller_module.request = old_request
            
        self.location.invalidate_recordset()
        self.assertEqual(self.location.pos_x, 10)
        self.assertEqual(self.location.pos_y, 20)
        self.assertEqual(self.location.size_x, 4)
        self.assertEqual(self.location.size_y, 2)
        self.assertEqual(self.location.location_rotation, 90)

    def test_02_save_map_objects(self):
        """Test saving map objects via the controller."""
        objects = [{
            'id': 'new_1', # Synthetic ID for new object
            'name': 'New Wall',
            'object_type': 'wall',
            'pos_x': 5,
            'pos_y': 5,
            'size_x': 1,
            'size_y': 1,
        }]
        
        old_request = controller_module.request
        controller_module.request = MagicMock(env=self.env)
        try:
            self.controller.save_map_objects(self.layout.id, objects)
        finally:
            controller_module.request = old_request
        
        new_obj = self.env['warehouse.map.object'].search([
            ('layout_id', '=', self.layout.id),
            ('name', '=', 'New Wall')
        ])
        self.assertTrue(new_obj)
        self.assertEqual(new_obj.pos_x, 5)

    def test_03_export_import_cycle(self):
        """Test a basic export-import cycle (conceptual)."""
        # This is more complex to test fully without full HTTP mock
        # but we can test the internal XML generation if needed.
        pass
