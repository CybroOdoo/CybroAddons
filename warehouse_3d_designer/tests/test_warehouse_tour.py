# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestWarehouseTour(HttpCase):
    """Test the designer and the read-only map in the browser."""

    @classmethod
    def setUpClass(cls):
        """Create a layout listed first, with one placed location."""
        super().setUpClass()
        warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id)], limit=1)
        cls.layout = cls.env['warehouse.layout'].create({
            'name': '00 Tour Layout',
            'warehouse_id': warehouse.id,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Tour Rack',
            'location_id': warehouse.lot_stock_id.id,
            'layout_id': cls.layout.id,
        })
        new_test_user(cls.env, login='tour_manager',
                      groups='stock.group_stock_manager')
        new_test_user(cls.env, login='tour_viewer',
                      groups='stock.group_stock_user')

    def test_01_remove_location_in_designer(self):
        """A location removed in the designer leaves the layout on save."""
        action = self.env.ref(
            'warehouse_3d_designer.action_warehouse_designer')
        self.start_tour(f'/odoo/action-{action.id}',
                        'warehouse_3d_designer_remove_location',
                        login='tour_manager')
        self.assertFalse(self.location.layout_id)

    def test_02_read_only_map(self):
        """Inventory users see the map without the editing tools."""
        action = self.env.ref(
            'warehouse_3d_designer.action_warehouse_map_viewer')
        self.start_tour(f'/odoo/action-{action.id}',
                        'warehouse_3d_designer_read_only_map',
                        login='tour_viewer')
        self.assertEqual(self.location.layout_id, self.layout)
