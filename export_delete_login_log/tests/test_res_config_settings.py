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
from odoo.exceptions import UserError
from odoo import fields


class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResConfigSettings, cls).setUpClass()

        # Fetch sample models to use in configurations
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.company_model = cls.env['ir.model'].search([('model', '=', 'res.company')], limit=1)

        cls.param_key = 'export_delete_login_log.delete_log_models_ids'
        cls.manager_group = cls.env.ref('export_delete_login_log.group_export_log_manager')

        # Create user with custom manager group
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Log Config Manager',
            'login': 'config_mgr',
            'email': 'mgr@test.com',
            'group_ids': [fields.Command.link(cls.manager_group.id)]
        })

        # Create user WITHOUT custom manager group
        cls.user_normal = cls.env['res.users'].create({
            'name': 'Standard Employee',
            'login': 'normal_emp',
            'email': 'emp@test.com',
            'group_ids': []
        })

    def test_01_set_values_as_manager(self):
        """Test that a user with the manager group can successfully save the config settings."""
        # Fix: Create the wizard record with admin permissions
        settings = self.env['res.config.settings'].create({
            'delete_log_models_ids': [fields.Command.set([self.partner_model.id, self.company_model.id])],
            'have_api_key': True,
            'ipapi_key': 'test_token_1234'
        })

        # Fix: Switch context to the manager user only for execution of the logic
        settings.with_user(self.user_manager).set_values()

        # Retrieve parameter and assert it saved correctly
        saved_param = self.env['ir.config_parameter'].sudo().get_param(self.param_key)
        self.assertTrue(saved_param, "Configuration parameters were not saved.")

        saved_ids = eval(saved_param)
        self.assertIn(self.partner_model.id, saved_ids)
        self.assertIn(self.company_model.id, saved_ids)

    def test_02_set_values_unauthorized_raises_user_error(self):
        """Test that a standard user without the group is denied access and triggers a UserError."""
        # Fix: Create the wizard record with admin permissions
        settings = self.env['res.config.settings'].create({
            'delete_log_models_ids': [fields.Command.set([self.partner_model.id])],
        })

        # Fix: Switch context to normal user during execution to trigger your custom exception logic
        with self.assertRaises(UserError,
                               msg="An unauthorized user was incorrectly allowed to save logs configuration."):
            settings.with_user(self.user_normal).set_values()

    def test_03_get_values_format_conversion(self):
        """Test that get_values accurately parses saved string configurations back into structural fields."""
        mock_ids = [self.partner_model.id]
        self.env['ir.config_parameter'].sudo().set_param(self.param_key, str(mock_ids))

        values = self.env['res.config.settings'].get_values()

        self.assertIn('delete_log_models_ids', values, "get_values payload didn't extract target field key.")

        command_tuple = values['delete_log_models_ids'][0]
        self.assertEqual(command_tuple[0], 6,
                         "Expected an Odoo structural Command.SET (value 6) operational indicator.")
        self.assertEqual(command_tuple[2], mock_ids,
                         "The parsed array output did not extract configuration IDs correctly.")