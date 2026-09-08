# -*- coding: utf-8 -*-
#############################################################################
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestRouteZonesSetting(TransactionCase):
    """Unit tests verifying service zone routing rules and collection point assignment."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Zone Customer'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'General Waste TestZone'})
        cls.product = cls.env['product.product'].create({
            'name': 'Garbage',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 15.0,
        })
        cls.zone = cls.env['wm.service.zone'].create({
            'name': 'North Zone',
            'max_stops_per_route': 10,
        })
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Zone Point 1',
            'partner_id': cls.partner.id,
            'zone_id': cls.zone.id,
        })
        cls.order = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner.id,
            'collection_point_id': cls.point.id,
            'scheduled_start': '2026-08-01 09:00:00',
            'state': 'draft',
        })

    def test_route_zones_enabled(self):
        """
        Test route zones compute and cron when enabled.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_route_zones', 'True')

        self.assertTrue(self.point.use_route_zones)
        route = self.env['wm.route'].create({'name': 'Test Route', 'zone_id': self.zone.id})
        self.assertTrue(route.use_route_zones)

        # Run cron
        self.env['wm.route']._cron_auto_assign_orders_to_routes()
        self.order.invalidate_recordset(['route_id'])
        self.assertTrue(self.order.route_id)

    def test_route_zones_disabled(self):
        """
        Test route zones cron bypass when disabled.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_route_zones', 'False')

        point = self.env['wm.collection.point'].create({'name': 'Point 2', 'partner_id': self.partner.id})
        self.assertFalse(point.use_route_zones)

        unassigned_order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': '2026-08-02 09:00:00',
            'state': 'draft',
        })

        # Run cron
        self.env['wm.route']._cron_auto_assign_orders_to_routes()
        unassigned_order.invalidate_recordset(['route_id'])
        self.assertFalse(unassigned_order.route_id)

    def test_res_config_settings_zones(self):
        """
        Test res.config.settings get_values and set_values for route zones.
        """
        settings = self.env['res.config.settings'].create({'use_route_zones': True})
        settings.set_values()
        vals = settings.get_values()
        self.assertTrue(vals.get('use_route_zones'))

        menu_zone = self.env.ref('wm_collection.menu_wm_service_zone', raise_if_not_found=False)
        if menu_zone:
            self.assertTrue(menu_zone.active)

        cron_assign = self.env.ref('wm_collection.ir_cron_auto_assign_orders_to_routes', raise_if_not_found=False)
        if cron_assign:
            self.assertTrue(cron_assign.active)

        settings = self.env['res.config.settings'].create({'use_route_zones': False})
        settings.set_values()
        vals = settings.get_values()
        self.assertFalse(vals.get('use_route_zones'))

        if menu_zone:
            self.assertFalse(menu_zone.active)

        if cron_assign:
            self.assertFalse(cron_assign.active)
