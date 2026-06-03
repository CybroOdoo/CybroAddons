# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Tests for export_delete_login_log settings."""

    def setUp(self):
        super().setUp()
        self.admin = self.env.ref('base.user_admin')
        self.config_parameter = self.env['ir.config_parameter'].sudo()
        self.partner_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')],
            limit=1,
        )
        self.group_manager = self.env.ref(
            'export_delete_login_log.group_export_log_manager'
        )

    def test_set_values_stores_tracked_models_for_manager(self):
        settings = self.env['res.config.settings'].with_user(self.admin).create({
            'delete_log_models_ids': [(6, 0, [self.partner_model.id])],
            'have_api_key': True,
            'ipapi_key': 'test-api-key',
        })

        settings.set_values()

        self.assertEqual(
            self.config_parameter.get_param(
                'export_delete_login_log.delete_log_models_ids'
            ),
            str([self.partner_model.id]),
        )
        self.assertEqual(
            self.config_parameter.get_param(
                'export_delete_login_log.have_api_key'
            ),
            'True',
        )
        self.assertEqual(
            self.config_parameter.get_param(
                'export_delete_login_log.ipapi_key'
            ),
            'test-api-key',
        )

    def test_set_values_raises_for_user_outside_manager_group(self):
        self.group_manager.write({
            'users': [(3, self.admin.id)],
        })
        settings = self.env['res.config.settings'].with_user(self.admin).create({
            'delete_log_models_ids': [(6, 0, [self.partner_model.id])],
        })

        with self.assertRaises(UserError):
            settings.set_values()

    def test_get_values_returns_saved_tracked_models(self):
        self.config_parameter.set_param(
            'export_delete_login_log.delete_log_models_ids',
            [self.partner_model.id],
        )

        values = self.env['res.config.settings'].get_values()

        self.assertEqual(
            values['delete_log_models_ids'],
            [(6, 0, [self.partner_model.id])],
        )
