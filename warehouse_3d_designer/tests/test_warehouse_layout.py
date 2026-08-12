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

class TestWarehouseLayout(TransactionCase):
    """Test suite for warehouse.layout model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Main Warehouse',
            'code': 'MWH',
        })
        cls.layout = cls.env['warehouse.layout'].create({
            'name': 'Ground Floor',
            'warehouse_id': cls.warehouse.id,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Bin 1',
            'location_id': cls.warehouse.lot_stock_id.id,
            'layout_id': cls.layout.id,
            'usage': 'internal',
        })

    def test_01_compute_location_count(self):
        """Test the location count calculation."""
        self.layout._compute_location_count()
        self.assertEqual(self.layout.location_count, 1)
        
        # Create another location for this layout
        self.env['stock.location'].create({
            'name': 'Bin 2',
            'location_id': self.warehouse.lot_stock_id.id,
            'layout_id': self.layout.id,
        })
        self.layout._compute_location_count()
        self.assertEqual(self.layout.location_count, 2)

    def test_02_action_open_designer(self):
        """Test it returns the correct client action."""
        action = self.layout.action_open_designer()
        self.assertEqual(action['tag'], 'warehouse_designer')
        self.assertEqual(action['context']['default_layout_id'], self.layout.id)

    def test_03_get_layout_data(self):
        """Test layout data structure for the designer."""
        data = self.layout.get_layout_data()
        self.assertEqual(data['layout']['id'], self.layout.id)
        self.assertEqual(len(data['locations']), 1)
        self.assertEqual(data['locations'][0]['id'], self.location.id)
        self.assertEqual(data['locations'][0]['name'], self.location.name)
