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
from odoo.tests import tagged

from .common import DeliveryTrackingCommon


@tagged('post_install', '-at_install')
class TestDeliveryTracking(DeliveryTrackingCommon):
    """Test the model, settings and data of the module."""

    def test_tracking_status_default_is_empty(self):
        """A new picking has no tracking status."""
        self.assertFalse(self.picking.tracking_status)

    def test_tracking_status_can_be_written(self):
        """The tracking status stores the text written on the picking."""
        self.picking.tracking_status = 'Out for delivery'
        self.picking.invalidate_recordset()
        self.assertEqual(self.picking.tracking_status, 'Out for delivery')

    def test_tracking_status_field_definition(self):
        """The tracking status is a text field labelled 'Tracking Status'."""
        field = self.env['stock.picking']._fields['tracking_status']
        self.assertEqual(field.type, 'text')
        self.assertEqual(field.string, 'Tracking Status')

    def test_api_key_is_saved_in_config_parameter(self):
        """Saving the settings stores the API key as a system parameter."""
        settings = self.env['res.config.settings'].create({
            'delivery_tracking_api_key': 'new-secret-key',
        })
        settings.execute()
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_str(self.API_KEY_PARAM),
            'new-secret-key')

    def test_api_key_is_loaded_in_settings(self):
        """The settings screen shows the API key saved in the system."""
        settings = self.env['res.config.settings'].create({
            'delivery_tracking_api_key': self.API_KEY,
        })
        self.assertEqual(settings.delivery_tracking_api_key, self.API_KEY)
        values = self.env['res.config.settings'].default_get(
            ['delivery_tracking_api_key'])
        self.assertEqual(values['delivery_tracking_api_key'], self.API_KEY)

    def test_settings_view_contains_api_key_field(self):
        """The API key field is shown in the settings form."""
        arch = self.env['res.config.settings'].get_view(
            view_type='form')['arch']
        self.assertIn('delivery_tracking_api_key', arch)
        self.assertIn('Delivery Tracking', arch)

    def test_website_menu(self):
        """The website menu opens the tracking page."""
        menu = self.env.ref('website_order_delivery_tracking.tracking_menu')
        self.assertEqual(menu.url, '/tracking/details')
        self.assertEqual(menu.name, 'Tracking Details')
