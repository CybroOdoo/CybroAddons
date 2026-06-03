# -*- coding: utf-8 -*-
import json

from .common import TenderManagementTestCommon


class TestResConfigSettings(TenderManagementTestCommon):
    """Tests for settings persistence."""

    def test_set_values_and_get_values_for_manual_approval_users(self):
        settings = self.env['res.config.settings'].create({
            'auto_approval': False,
            'manual_approval_users_ids': [(
                6, 0, [self.env.user.id]
            )],
        })

        settings.set_values()
        values = self.env['res.config.settings'].get_values()

        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param(
                'advanced_tender_management.manual_approval_users_ids'
            ),
            json.dumps([self.env.user.id]),
        )
        self.assertEqual(values['manual_approval_users_ids'], self.env.user)

    def test_set_values_stores_empty_list_without_manual_users(self):
        settings = self.env['res.config.settings'].create({
            'manual_approval_users_ids': [(6, 0, [])],
        })

        settings.set_values()

        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param(
                'advanced_tender_management.manual_approval_users_ids'
            ),
            '[]',
        )
