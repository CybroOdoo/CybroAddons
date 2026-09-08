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
from datetime import timedelta
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMissedCollectionSetting(TransactionCase):
    """Unit tests verifying missed collection reason logging and rescheduling options."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'General Waste Missed Setting Test'})
        cls.product = cls.env['product.product'].create({
            'name': 'Trash',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 10.0,
        })
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Test Point',
            'partner_id': cls.partner.id,
            'category_ids': [(4, cls.category.id)],
        })
        cls.route = cls.env['wm.route'].create({'name': 'Missed Test Route'})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Missed Brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Missed Truck Model', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'driver_id': cls.partner.id,
            'license_plate': 'MISSED-01',
        })

        cls.order = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner.id,
            'collection_point_id': cls.collection_point.id,
            'route_id': cls.route.id,
            'vehicle_id': cls.vehicle.id,
            'scheduled_start': fields.Datetime.now(),
            'scheduled_end': fields.Datetime.now() + timedelta(hours=3),
            'order_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'category_id': cls.category.id,
                'weight': 50.0,
            })],
        })
        cls.reason = cls.env['wm.missed.reason'].create({'name': 'Blocked Driveway'})

    def test_missed_collection_enabled(self):
        """
        Test missed collection flow when feature is enabled.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_missed_collection', 'True')
        self.order.action_dispatch()
        self.assertTrue(self.order.use_missed_collection)

        action = self.order.action_mark_missed()
        self.assertEqual(action['res_model'], 'wm.mark.missed.wizard')

        wizard = self.env['wm.mark.missed.wizard'].create({
            'order_id': self.order.id,
            'reason_id': self.reason.id,
            'notes': 'Cannot access',
        })
        wizard.action_confirm()

        self.assertEqual(self.order.state, 'missed')
        self.assertTrue(self.order.is_missed)
        self.assertTrue(self.order.retry_order_id)

    def test_missed_collection_disabled(self):
        """
        Test missed collection blocking when feature is disabled.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_missed_collection', 'False')
        self.order.action_dispatch()
        self.assertFalse(self.order.use_missed_collection)

        with self.assertRaises(UserError):
            self.order.action_mark_missed()

        wizard = self.env['wm.mark.missed.wizard'].create({
            'order_id': self.order.id,
            'reason_id': self.reason.id,
            'notes': 'Cannot access',
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_res_config_settings_get_set_values(self):
        """
        Test that res.config.settings correctly persists get_values and
        set_values.
        """
        # Enable setting via res.config.settings
        settings = self.env['res.config.settings'].create({'use_missed_collection': True})
        settings.set_values()
        vals = settings.get_values()
        self.assertTrue(vals.get('use_missed_collection'))

        # Disable setting via res.config.settings
        settings = self.env['res.config.settings'].create({'use_missed_collection': False})
        settings.set_values()
        vals = settings.get_values()
        self.assertFalse(vals.get('use_missed_collection'))

    def test_read_group_states_kanban(self):
        """
        Test that _read_group_states excludes 'missed' column when feature is
        disabled.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_missed_collection', 'True')
        states_enabled = self.env['wm.collection.order']._read_group_states([], [])
        self.assertIn('missed', states_enabled)

        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_missed_collection', 'False')
        states_disabled = self.env['wm.collection.order']._read_group_states([], [])
        self.assertNotIn('missed', states_disabled)
