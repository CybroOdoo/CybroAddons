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


class TestWmAuditTrailSetting(TransactionCase):
    """Unit tests verifying audit log recording and status transition tracking."""

    def setUp(self):
        """ Set up test case preconditions and test data. """
        super().setUp()
        self.category_model = self.env['wm.waste.category']

    def test_audit_trail_disabled_by_default_or_false(self):
        """
        When wm_base.group_wm_audit_trail is not set or False, audit logs
        should not be created.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_base.group_wm_audit_trail', 'False')
        self.assertFalse(self.category_model._is_audit_trail_enabled())

        initial_count = self.env['wm.audit.log'].search_count([])
        cat = self.category_model.create({
            'name': 'Test Category Audit Off',
            'code': 'TCAO',
        })
        cat.write({'name': 'Test Category Audit Off Updated'})
        cat.unlink()

        final_count = self.env['wm.audit.log'].search_count([])
        self.assertEqual(initial_count, final_count, "No audit logs should be created when audit trail is disabled.")

    def test_audit_trail_enabled_when_true(self):
        """
        When wm_base.group_wm_audit_trail is True, audit logs should be
        created.
        """
        self.env['ir.config_parameter'].sudo().set_param('wm_base.group_wm_audit_trail', 'True')
        self.assertTrue(self.category_model._is_audit_trail_enabled())

        initial_count = self.env['wm.audit.log'].search_count([])
        cat = self.category_model.create({
            'name': 'Test Category Audit On',
            'code': 'TCAO2',
        })
        after_create_count = self.env['wm.audit.log'].search_count([])
        self.assertGreater(after_create_count, initial_count, "Audit logs should be created on create when enabled.")

        cat.write({'name': 'Test Category Audit On Updated'})
        after_write_count = self.env['wm.audit.log'].search_count([])
        self.assertGreater(after_write_count, after_create_count, "Audit logs should be created on write when enabled.")

    def test_settings_save_and_menu_toggle(self):
        """
        Test that saving res.config.settings toggles menu and config param
        correctly.
        """
        # Enable via settings
        setting = self.env['res.config.settings'].create({'group_wm_audit_trail': True})
        setting.set_values()
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param('wm_base.group_wm_audit_trail'), 'True')
        menu = self.env.ref('wm_base.menu_wm_audit_trail', raise_if_not_found=False)
        if menu:
            self.assertTrue(menu.active)

        # Disable via settings
        setting = self.env['res.config.settings'].create({'group_wm_audit_trail': False})
        setting.set_values()
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param('wm_base.group_wm_audit_trail'), 'False')
        if menu:
            self.assertFalse(menu.active)
