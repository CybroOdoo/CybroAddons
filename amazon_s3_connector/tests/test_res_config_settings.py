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
from odoo.tests.common import TransactionCase

from odoo.addons.amazon_s3_connector.hooks import uninstall_hook

PARAM_KEYS = [
    'amazon_s3_connector.amazon_access_key',
    'amazon_s3_connector.amazon_secret_key',
    'amazon_s3_connector.amazon_bucket_name',
    'amazon_s3_connector.amazon_connector',
]


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Tests for the Amazon S3 settings and uninstall hook."""

    def _save_settings(self):
        """Save Amazon S3 credentials through the settings."""
        self.env['res.config.settings'].create({
            'is_amazon_connector': True,
            'amazon_access_key': 'ACCESS',
            'amazon_secret_key': 'SECRET',
            'amazon_bucket_name': 'my-bucket',
        }).execute()

    def test_settings_saved_as_parameters(self):
        """Settings are stored as system parameters."""
        self._save_settings()
        params = self.env['ir.config_parameter'].sudo()
        self.assertEqual(params.get_str('amazon_s3_connector.amazon_access_key'), 'ACCESS')
        self.assertEqual(params.get_str('amazon_s3_connector.amazon_secret_key'), 'SECRET')
        self.assertEqual(params.get_str('amazon_s3_connector.amazon_bucket_name'), 'my-bucket')
        self.assertTrue(params.get_str('amazon_s3_connector.amazon_connector'))

    def test_settings_loaded_from_parameters(self):
        """Saved values are shown when the settings are opened again."""
        self._save_settings()
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(settings.is_amazon_connector)
        self.assertEqual(settings.amazon_access_key, 'ACCESS')
        self.assertEqual(settings.amazon_bucket_name, 'my-bucket')

    def test_uninstall_hook_removes_parameters(self):
        """The uninstall hook deletes the Amazon S3 parameters."""
        self._save_settings()
        uninstall_hook(self.env)
        params = self.env['ir.config_parameter'].sudo().search([('key', 'in', PARAM_KEYS)])
        self.assertFalse(params)
