# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests.common import TransactionCase


class TestDeliveryWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Settings = cls.env['website.estimated.delivery.time']

    def test_action_website_estimated_delivery_time_cleanup(self):
        """Test that action_website_estimated_delivery_time unlinks old records"""
        old_settings = self.Settings.create({
            'available_message': 'Old',
            'number_of_days': 1,
        })
        current_settings = self.Settings.create({
            'available_message': 'Current',
            'number_of_days': 1,
        })
        current_settings.action_website_estimated_delivery_time()
        # Verify old settings are unlinked
        self.assertFalse(old_settings.exists())
        self.assertTrue(current_settings.exists())

    def test_action_open_estimated_delivery_time(self):
        """Test action_open_estimated_delivery_time returns action and ensures record"""
        # Ensure no records exist initially
        self.Settings.search([]).unlink()
        wizard = self.Settings.new({})
        action = wizard.action_open_estimated_delivery_time()
        # Verify a record was created
        settings_count = self.Settings.search_count([])
        self.assertEqual(settings_count, 1)
        # Verify action details
        self.assertEqual(action.get('res_model'), 'website.estimated.delivery.time')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('res_id'), self.Settings.search([], limit=1).id)
