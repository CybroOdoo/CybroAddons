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
"""Unit tests for the custom_pivot_report hooks."""

from odoo.tests import tagged, TransactionCase
from odoo.addons.custom_pivot_report.hooks import report_uninstall_hook


@tagged('post_install', '-at_install')
class TestHooks(TransactionCase):
    """Test cases for custom_pivot_report hooks."""

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
        cls.parent_menu = cls.env['ir.ui.menu'].create({
            'name': 'Hook Test Parent Menu',
        })
        cls.test_group = cls.env.ref('base.group_user')

    def test_report_uninstall_hook(self):
        """Test report_uninstall_hook function unlinks all custom.report records."""
        report = self.env['custom.report'].create({
            'name': 'Report To Uninstall',
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

        self.assertTrue(report.exists(), "Custom report should exist prior to uninstall hook")

        # Call the uninstall hook
        report_uninstall_hook(self.env)

        # Verify all custom.report records have been unlinked
        all_reports = self.env['custom.report'].search([])
        self.assertFalse(all_reports, "All custom.report records should be unlinked by report_uninstall_hook")
