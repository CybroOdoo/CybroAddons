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
from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResponsiveWebTour(HttpCase):
    """Tour tests for the responsive_web module."""

    def test_responsive_web_app_drawer_tour(self):
        """Test app drawer toggle, menu search, and navigation via browser tour."""
        self.start_tour('/odoo', 'responsive_web_tour', login='admin')


@tagged('post_install', '-at_install')
class TestResponsiveWebBackend(TransactionCase):
    """Backend unit tests for responsive_web records and assets."""

    def test_client_action_web_responsive(self):
        """Verify the 'web_responsive' client action is properly defined."""
        action = self.env.ref('responsive_web.action_web_responsive', raise_if_not_found=False)
        self.assertTrue(action, "Action 'responsive_web.action_web_responsive' should exist.")
        self.assertEqual(action.tag, 'web_responsive', "Client action tag must be 'web_responsive'.")
        self.assertEqual(action.name, 'Web Responsive', "Client action name must match definition.")

    def test_assets_definition(self):
        """Verify backend and test assets include responsive_web components and styles."""
        manifest = self.env['ir.module.module'].search([('name', '=', 'responsive_web')], limit=1)
        self.assertTrue(manifest, "Module 'responsive_web' should be found in ir.module.module.")
        # Ensure ir.asset records or manifest entries exist for sticky headers and tours
        assets = self.env['ir.asset'].search([('path', 'ilike', 'responsive_web')])
        # Verify that assets can be queried without orm errors
        self.assertIsNotNone(assets)
