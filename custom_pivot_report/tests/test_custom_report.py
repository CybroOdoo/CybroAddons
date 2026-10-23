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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Unit tests for the custom.report model."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestCustomReport(TransactionCase):
    """Test cases for custom.report model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1
        )
        cls.field_name = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'name'),
        ], limit=1)
        cls.field_id = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'id'),
        ], limit=1)
        cls.field_category = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'category_id'),
        ], limit=1)

        cls.parent_menu = cls.env['ir.ui.menu'].create({
            'name': 'Test Reports Parent Menu',
        })
        cls.other_parent_menu = cls.env['ir.ui.menu'].create({
            'name': 'Other Reports Parent Menu',
        })
        cls.test_group = cls.env.ref('base.group_user')

    def test_sync_ui_components_create_and_write(self):
        """Test _sync_ui_components called on create and write to build views, actions, and menus."""
        report = self.env['custom.report'].create({
            'name': 'Partner Custom & Pivot <Special>',
            'model_id': self.partner_model.id,
            'menu_id': self.parent_menu.id,
            'menu_group_ids': [(6, 0, [self.test_group.id])],
            'fields_ids': [
                (0, 0, {
                    'custom_field_id': self.field_name.id,
                    'label': 'Partner Name & Co',
                    'row': True,
                    'measure': False,
                }),
                (0, 0, {
                    'custom_field_id': self.field_id.id,
                    'label': 'Partner Count <Measure>',
                    'row': False,
                    'measure': True,
                }),
                (0, 0, {
                    'custom_field_id': self.field_category.id,
                    'label': 'Partner Tags',
                    'row': False,
                    'measure': False,
                }),
            ],
        })

        expected_tag = f"custom_report_{report.id}"

        # 1. Verify view creation and XML escaping
        view = self.env['ir.ui.view'].search([('custom_report', '=', expected_tag)])
        self.assertTrue(view, "Pivot view must be created by _sync_ui_components on create")
        self.assertEqual(view.model, 'res.partner')
        self.assertEqual(view.type, 'pivot')
        self.assertIn('&amp;', view.arch_base)
        self.assertIn('&lt;Special&gt;', view.arch_base)
        self.assertIn('&lt;Measure&gt;', view.arch_base)

        # 2. Verify window action creation
        action = self.env['ir.actions.act_window'].search([('custom_report', '=', expected_tag)])
        self.assertTrue(action, "Window action must be created by _sync_ui_components on create")
        self.assertEqual(action.res_model, 'res.partner')
        self.assertEqual(action.view_mode, 'pivot')
        self.assertEqual(action.view_id.id, view.id)
        self.assertEqual(action.target, 'current')

        # 3. Verify menu item creation
        menu = self.env['ir.ui.menu'].search([('custom_report', '=', expected_tag)])
        self.assertTrue(menu, "Menu item must be created by _sync_ui_components on create")
        self.assertEqual(menu.parent_id.id, self.parent_menu.id)
        self.assertEqual(menu.action.id, action.id)
        self.assertIn(self.test_group, menu.group_ids)

        # 4. Test write: change name and parent menu without orphaning old records
        report.write({
            'name': 'Updated Partner Pivot',
            'menu_id': self.other_parent_menu.id,
        })
        self.assertEqual(view.name, 'Updated Partner Pivot')
        self.assertEqual(action.name, 'Updated Partner Pivot')
        self.assertEqual(menu.name, 'Updated Partner Pivot')
        self.assertEqual(menu.parent_id.id, self.other_parent_menu.id)

        # Verify no duplicate orphaned records were created
        views_count = self.env['ir.ui.view'].search_count([('custom_report', '=', expected_tag)])
        actions_count = self.env['ir.actions.act_window'].search_count([('custom_report', '=', expected_tag)])
        menus_count = self.env['ir.ui.menu'].search_count([('custom_report', '=', expected_tag)])
        self.assertEqual(views_count, 1)
        self.assertEqual(actions_count, 1)
        self.assertEqual(menus_count, 1)

    def test__create_menu_id_backward_compatibility(self):
        """Test _create_menu_id backwards compatibility alias."""
        report = self.env['custom.report'].create({
            'name': 'Alias Compatibility Report',
            'model_id': self.partner_model.id,
            'menu_id': self.parent_menu.id,
            'menu_group_ids': [(6, 0, [self.test_group.id])],
            'fields_ids': [
                (0, 0, {
                    'custom_field_id': self.field_name.id,
                    'label': 'Name',
                    'row': True,
                }),
            ],
        })
        report._create_menu_id()
        expected_tag = f"custom_report_{report.id}"
        menu = self.env['ir.ui.menu'].search([('custom_report', '=', expected_tag)])
        self.assertTrue(menu)

    def test_fields_ids_validation_constraint(self):
        """Test that ValidationError is raised if custom report has no fields."""
        with self.assertRaises(ValidationError):
            self.env['custom.report'].create({
                'name': 'Report Without Fields',
                'model_id': self.partner_model.id,
                'menu_id': self.parent_menu.id,
                'menu_group_ids': [(6, 0, [self.test_group.id])],
                'fields_ids': [],
            })

    def test_unlink(self):
        """Test unlink function to ensure associated views, actions, and menus are cleaned up."""
        report = self.env['custom.report'].create({
            'name': 'Temporary Report For Unlink',
            'model_id': self.partner_model.id,
            'menu_id': self.parent_menu.id,
            'menu_group_ids': [(6, 0, [self.test_group.id])],
            'fields_ids': [
                (0, 0, {
                    'custom_field_id': self.field_name.id,
                    'label': 'Name',
                    'row': True,
                }),
            ],
        })

        expected_tag = f"custom_report_{report.id}"

        # Ensure records are present before deletion
        view = self.env['ir.ui.view'].search([('custom_report', '=', expected_tag)])
        action = self.env['ir.actions.act_window'].search([('custom_report', '=', expected_tag)])
        menu = self.env['ir.ui.menu'].search([('custom_report', '=', expected_tag)])
        self.assertTrue(view)
        self.assertTrue(action)
        self.assertTrue(menu)

        # Execute unlink
        report.unlink()

        # Verify all related components were deleted
        view_after = self.env['ir.ui.view'].search([('custom_report', '=', expected_tag)])
        action_after = self.env['ir.actions.act_window'].search([('custom_report', '=', expected_tag)])
        menu_after = self.env['ir.ui.menu'].search([('custom_report', '=', expected_tag)])

        self.assertFalse(view_after, "Related ir.ui.view should be deleted on report unlink")
        self.assertFalse(action_after, "Related ir.actions.act_window should be deleted on report unlink")
        self.assertFalse(menu_after, "Related ir.ui.menu should be deleted on report unlink")
        self.assertFalse(report.exists(), "custom.report record itself should be deleted")
