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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for ResConfigSettings extension (res_config_settings.py).

    Covers:
        - set_values: saves delete_log_models_ids as an ir.config_parameter.
        - get_values: reads the saved ids back from ir.config_parameter.
        - Permission enforcement: only users in the manager group may set_values.
    """

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')], limit=1)
        self.users_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.users')], limit=1)

        # Resolve the manager group and ensure the admin user is a member.
        self.manager_group = self.env.ref(
            'export_delete_login_log.group_export_log_manager')
        self.admin_user = self.env.ref('base.user_admin')

        # Add admin to the manager group so set_values succeeds for admin.
        self.manager_group.sudo().write(
            {'users': [(4, self.admin_user.id)]})

    def _get_config_as_admin(self):
        """Return a res.config.settings record owned by the admin user.

        Using with_user(admin) ensures self.env.user inside set_values/get_values
        is the admin, who has already been added to the manager group in setUp.
        """
        return (self.env['res.config.settings']
                .with_user(self.admin_user)
                .create({}))

    # ------------------------------------------------------------------ #
    # set_values tests                                                     #
    # ------------------------------------------------------------------ #

    def test_set_values_saves_delete_log_models_ids(self):
        """set_values should persist delete_log_models_ids to ir.config_parameter."""
        config = self._get_config_as_admin()
        config.delete_log_models_ids = [(6, 0, [self.partner_model.id])]
        config.set_values()

        saved_param = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.delete_log_models_ids')
        self.assertIn(
            str(self.partner_model.id), saved_param,
            "Partner model ID should be saved in the config parameter."
        )

    def test_set_values_saves_multiple_models(self):
        """set_values should persist multiple model IDs to ir.config_parameter."""
        config = self._get_config_as_admin()
        config.delete_log_models_ids = [
            (6, 0, [self.partner_model.id, self.users_model.id])
        ]
        config.set_values()

        saved_param = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.delete_log_models_ids')
        self.assertIn(str(self.partner_model.id), saved_param,
                      "Partner model ID must be in the saved parameter.")
        self.assertIn(str(self.users_model.id), saved_param,
                      "Users model ID must be in the saved parameter.")

    # ------------------------------------------------------------------ #
    # get_values tests                                                     #
    # ------------------------------------------------------------------ #

    def test_get_values_reads_saved_ids(self):
        """get_values should return the previously stored model IDs."""
        # Store ids directly via ir.config_parameter to avoid set_values
        # permission concerns in this specific test.
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids',
            str([self.partner_model.id]))

        result = self.env['res.config.settings'].sudo().get_values()
        returned_ids = result.get('delete_log_models_ids', False)
        self.assertTrue(
            returned_ids,
            "get_values should return saved model IDs."
        )

    def test_get_values_returns_false_when_no_param(self):
        """get_values should return False for delete_log_models_ids when param is unset."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.delete_log_models_ids', '')
        result = self.env['res.config.settings'].sudo().get_values()
        returned_ids = result.get('delete_log_models_ids', False)
        self.assertFalse(
            returned_ids,
            "get_values should return False when no tracked models param is stored."
        )

    # ------------------------------------------------------------------ #
    # Permission tests                                                     #
    # ------------------------------------------------------------------ #

    def test_set_values_raises_for_non_manager_user(self):
        """set_values should raise UserError when user is not in the manager group."""
        # Create a non-manager user that has the Settings group so they can
        # read/write res.config.settings, but is NOT in the export manager group.
        system_group = self.env.ref('base.group_system')
        non_manager = self.env['res.users'].sudo().create({
            'name': 'Non Manager Export Log',
            'login': 'non_manager_export_log_test_unique',
            'email': 'non_manager_export_log_test@example.com',
            'groups_id': [(4, system_group.id)],
        })
        # Explicitly remove from manager group in case implied groups added them
        self.manager_group.sudo().write({'users': [(3, non_manager.id)]})

        # Create the config record with sudo then switch the env to non_manager.
        config = self.env['res.config.settings'].sudo().create({})
        config_nm = config.with_user(non_manager)

        with self.assertRaises(UserError):
            config_nm.set_values()

    # ------------------------------------------------------------------ #
    # Field-level tests                                                    #
    # ------------------------------------------------------------------ #

    def test_have_api_key_field_default_false(self):
        """have_api_key field should default to False unless explicitly set."""
        config = self._get_config_as_admin()
        self.assertFalse(
            config.have_api_key,
            "have_api_key should default to False."
        )

    def test_ipapi_key_field_default_empty(self):
        """ipapi_key field should be empty/False by default."""
        config = self._get_config_as_admin()
        self.assertFalse(
            config.ipapi_key,
            "ipapi_key should default to False/empty."
        )

    def test_delete_log_models_ids_domain_excludes_delete_log(self):
        """The domain on delete_log_models_ids should exclude delete.log model."""
        field = self.env['res.config.settings']._fields.get('delete_log_models_ids')
        self.assertIsNotNone(field, "delete_log_models_ids field should exist.")
        domain = field.domain
        self.assertIn(('model', '!=', 'delete.log'), domain,
                      "Domain should exclude the delete.log model itself.")

    def test_config_settings_inherits_base(self):
        """Verify that the model correctly inherits from res.config.settings."""
        config = self._get_config_as_admin()
        # Should have both custom and standard res.config.settings fields.
        self.assertIn('delete_log_models_ids', config._fields,
                      "Custom field delete_log_models_ids must be present.")
        self.assertIn('have_api_key', config._fields,
                      "Custom field have_api_key must be present.")
        self.assertIn('ipapi_key', config._fields,
                      "Custom field ipapi_key must be present.")
