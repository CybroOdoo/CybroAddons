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
import json

from odoo.tests import tagged

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestResConfigSettings(TenderManagementTestCommon):
    """Tests for settings persistence."""

    def test_set_values_and_get_values_for_manual_approval_users(self):
        approver = self.env.ref('base.user_admin')
        settings = self.env['res.config.settings'].create({
            'auto_approval': False,
            'manual_approval_users_ids': [(
                6, 0, [approver.id]
            )],
        })

        settings.set_values()
        values = self.env['res.config.settings'].get_values()

        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_str(
                'advanced_tender_management.manual_approval_users_ids'
            ),
            json.dumps([approver.id]),
        )
        self.assertEqual(values['manual_approval_users_ids'], approver)

    def test_set_values_stores_empty_list_without_manual_users(self):
        settings = self.env['res.config.settings'].create({
            'manual_approval_users_ids': [(6, 0, [])],
        })

        settings.set_values()

        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_str(
                'advanced_tender_management.manual_approval_users_ids'
            ),
            '[]',
        )

    def test_auto_approval_shown_as_the_controller_reads_it(self):
        """Settings show Auto Approval as the registration reads it: off
        until it is saved as on."""
        params = self.env['ir.config_parameter'].sudo()
        params.search([('key', '=', 'advanced_tender_management.auto_approval')]).unlink()
        self.assertFalse(self.env['res.config.settings'].create({}).auto_approval)
        self.assertFalse(params.get_bool('advanced_tender_management.auto_approval'))

        self.env['res.config.settings'].create({'auto_approval': True}).set_values()
        self.assertTrue(self.env['res.config.settings'].create({}).auto_approval)
        self.assertTrue(params.get_bool('advanced_tender_management.auto_approval'))
