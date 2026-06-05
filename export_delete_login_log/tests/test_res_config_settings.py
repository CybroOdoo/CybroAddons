# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from ast import literal_eval
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Test cases for ResConfigSettings extensions in
    res_config_settings.py."""

    def setUp(self):
        super().setUp()
        self.Settings = self.env['res.config.settings']

        # Resolve the export log manager group
        self.manager_group = self.env.ref(
            'export_delete_login_log.group_export_log_manager')

        # Ensure the current user (admin) is in the manager group.
        # Use write() so the Many2many relation is persisted properly.
        admin = self.env.ref('base.user_admin')
        admin.sudo().write({'groups_id': [(4, self.manager_group.id)]})
        # Run all settings operations as admin (who has the manager group)
        self.admin = admin

        # Grab two ir.model records to use as tracked models
        self.model_partner = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')], limit=1)
        self.model_product = self.env['ir.model'].sudo().search(
            [('model', '=', 'product.template')], limit=1)

    def tearDown(self):
        # Clean ir.config_parameter entries after each test
        for key in [
            'export_delete_login_log.delete_log_models_ids',
            'export_delete_login_log.have_api_key',
            'export_delete_login_log.ipapi_key',
        ]:
            self.env['ir.config_parameter'].sudo().set_param(key, '')
        super().tearDown()

    # ------------------------------------------------------------------
    # Field existence on res.config.settings
    # ------------------------------------------------------------------

    def test_field_delete_log_models_ids_exists(self):
        """delete_log_models_ids field must be present on res.config.settings."""
        self.assertIn('delete_log_models_ids', self.Settings._fields)

    def test_field_have_api_key_exists(self):
        """have_api_key field must be present on res.config.settings."""
        self.assertIn('have_api_key', self.Settings._fields)

    def test_field_ipapi_key_exists(self):
        """ipapi_key field must be present on res.config.settings."""
        self.assertIn('ipapi_key', self.Settings._fields)

    def test_delete_log_models_ids_is_many2many(self):
        """delete_log_models_ids should be a Many2many field."""
        from odoo import fields as odoo_fields
        field = self.Settings._fields['delete_log_models_ids']
        self.assertIsInstance(field, odoo_fields.Many2many)

    def test_have_api_key_is_boolean(self):
        """have_api_key should be a Boolean field."""
        from odoo import fields as odoo_fields
        field = self.Settings._fields['have_api_key']
        self.assertIsInstance(field, odoo_fields.Boolean)

    def test_ipapi_key_is_char(self):
        """ipapi_key should be a Char field."""
        from odoo import fields as odoo_fields
        field = self.Settings._fields['ipapi_key']
        self.assertIsInstance(field, odoo_fields.Char)

    # ------------------------------------------------------------------
    # set_values – manager user saves successfully
    # ------------------------------------------------------------------

    def test_set_values_saves_delete_log_models(self):
        """set_values called by a manager should store delete_log_models_ids
        in ir.config_parameter."""
        settings = self.Settings.with_user(self.admin).create({
            'delete_log_models_ids': [(4, self.model_partner.id)],
        })
        settings.with_user(self.admin).set_values()
        stored = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.delete_log_models_ids')
        self.assertTrue(stored)
        ids = literal_eval(stored)
        self.assertIn(self.model_partner.id, ids)

    def test_set_values_saves_multiple_models(self):
        """set_values should persist multiple model IDs correctly."""
        settings = self.Settings.with_user(self.admin).create({
            'delete_log_models_ids': [
                (4, self.model_partner.id),
                (4, self.model_product.id),
            ],
        })
        settings.with_user(self.admin).set_values()
        stored = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.delete_log_models_ids')
        ids = literal_eval(stored)
        self.assertIn(self.model_partner.id, ids)
        self.assertIn(self.model_product.id, ids)

    def test_set_values_clears_models_when_empty(self):
        """set_values with an empty Many2many should store an empty list."""
        settings = self.Settings.with_user(self.admin).create({
            'delete_log_models_ids': [(5, 0, 0)],
        })
        settings.with_user(self.admin).set_values()
        stored = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.delete_log_models_ids')
        # stored may be '[]' or '' – either means no tracked models
        if stored:
            self.assertEqual(literal_eval(stored), [])

    def test_set_values_non_manager_raises_user_error(self):
        """set_values called by a non-manager user should raise UserError."""
        # Create a plain internal user without manager group
        non_manager = self.env['res.users'].sudo().create({
            'name': 'Non Manager',
            'login': 'non_manager_test@example.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
            ])],
        })
        # res.config.settings create requires Administration/Settings group.
        # Create as admin, then call set_values as the non-manager user to
        # confirm the UserError is raised by the permission check.
        settings = self.Settings.with_user(self.admin).create({
            'delete_log_models_ids': [(4, self.model_partner.id)],
        })
        with self.assertRaises(UserError):
            settings.with_user(non_manager).set_values()

    # ------------------------------------------------------------------
    # get_values – reads back from ir.config_parameter
    # ------------------------------------------------------------------

    def test_get_values_returns_delete_log_models_ids(self):
        """get_values should return delete_log_models_ids populated from
        ir.config_parameter."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids',
            str(self.model_partner.ids))
        result = self.Settings.sudo().get_values()
        self.assertIn('delete_log_models_ids', result)

    def test_get_values_empty_param_returns_false(self):
        """get_values should return False for delete_log_models_ids when the
        config param is empty."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids', '')
        result = self.Settings.sudo().get_values()
        self.assertFalse(result.get('delete_log_models_ids'))

    def test_get_values_returns_all_fields(self):
        """get_values should return a dict that includes standard settings
        keys alongside the custom field."""
        result = self.Settings.sudo().get_values()
        self.assertIsInstance(result, dict)
        self.assertIn('delete_log_models_ids', result)

    # ------------------------------------------------------------------
    # have_api_key and ipapi_key – config_parameter persistence
    # ------------------------------------------------------------------

    def test_have_api_key_persists_via_config_parameter(self):
        """have_api_key (config_parameter) should be saved/read correctly."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.have_api_key', 'True')
        val = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.have_api_key')
        self.assertEqual(val, 'True')

    def test_ipapi_key_persists_via_config_parameter(self):
        """ipapi_key (config_parameter) should be saved/read correctly."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.ipapi_key', 'MY_SECRET_KEY')
        val = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.ipapi_key')
        self.assertEqual(val, 'MY_SECRET_KEY')

    def test_have_api_key_default_false(self):
        """have_api_key should be False when the config parameter is not set."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.have_api_key', '')
        settings = self.Settings.with_user(self.admin).create({})
        # When param is empty the field evaluates to False
        self.assertFalse(settings.have_api_key)

    def test_ipapi_key_empty_when_not_set(self):
        """ipapi_key should be empty/False when the config parameter is not set."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.ipapi_key', '')
        settings = self.Settings.with_user(self.admin).create({})
        self.assertFalse(settings.ipapi_key)

    # ------------------------------------------------------------------
    # Round-trip: set_values then get_values
    # ------------------------------------------------------------------

    def test_set_then_get_values_roundtrip(self):
        """Data saved via set_values should be readable via get_values."""
        settings = self.Settings.with_user(self.admin).create({
            'delete_log_models_ids': [(4, self.model_partner.id)],
        })
        settings.with_user(self.admin).set_values()
        result = self.Settings.sudo().get_values()
        # The returned value is a Command.set list; check it's truthy
        self.assertTrue(result.get('delete_log_models_ids'))

    def test_set_values_does_not_log_delete_log_model_itself(self):
        """The domain on delete_log_models_ids excludes 'delete.log' itself,
        so delete.log should not appear in the field options."""
        delete_log_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'delete.log')], limit=1)
        # The field has domain [('model', '!=', 'delete.log')]
        # Verify by checking the field's domain attribute
        field = self.Settings._fields['delete_log_models_ids']
        domain = field.domain
        self.assertIn(('model', '!=', 'delete.log'), domain)
