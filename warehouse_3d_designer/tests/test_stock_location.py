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

class TestStockLocation(TransactionCase):
    """Test suite for stock.location overrides in warehouse_3d_designer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
        })
        cls.layout = cls.env['warehouse.layout'].create({
            'name': 'Main Floor',
            'warehouse_id': cls.warehouse.id,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Test Location',
            'location_id': cls.warehouse.view_location_id.id,
            'usage': 'internal',
        })

    def test_01_compute_is_on_layout(self):
        """Test that is_on_layout is correctly computed."""
        self.assertFalse(self.location.is_on_layout)
        
        self.location.layout_id = self.layout.id
        self.location._compute_is_on_layout()
        self.assertTrue(self.location.is_on_layout)
        
        self.location.layout_id = False
        self.location._compute_is_on_layout()
        self.assertFalse(self.location.is_on_layout)

    def test_02_onchange_location_shape(self):
        """Test that changing shape updates size and color defaults."""
        self.location.location_shape = 'bin'
        self.location._onchange_location_shape()
        self.assertEqual(self.location.size_x, 1)
        self.assertEqual(self.location.size_y, 1)
        self.assertEqual(self.location.location_color, '#FFB347')
        
        self.location.location_shape = 'zone'
        self.location._onchange_location_shape()
        self.assertEqual(self.location.size_x, 6)
        self.assertEqual(self.location.size_y, 4)
        self.assertEqual(self.location.location_color, '#DDA0DD')
