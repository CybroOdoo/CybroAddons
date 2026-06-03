# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gion Dany (odoo@cybrosys.com)
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


@tagged('post_install', '-at_install', 'contacts_email_validator')
class TestResConfigSettings(TransactionCase):
    """Tests for the email_validation_enabled Boolean on res.config.settings."""

    # ------------------------------------------------------------------
    # 1. Field presence & metadata
    # ------------------------------------------------------------------

    def test_field_email_validation_enabled_exists(self):
        """email_validation_enabled must be defined on res.config.settings."""
        settings = self.env['res.config.settings']
        self.assertIn(
            'email_validation_enabled',
            settings._fields,
            "Field 'email_validation_enabled' missing from res.config.settings",
        )

    def test_field_is_boolean(self):
        """email_validation_enabled must be a Boolean field."""
        field = self.env['res.config.settings']._fields['email_validation_enabled']
        self.assertEqual(field.type, 'boolean')


    # ------------------------------------------------------------------
    # 2. Save / load round-trip via ir.config_parameter
    # ------------------------------------------------------------------

    def test_enable_sets_param_to_true(self):
        """Saving with email_validation_enabled=True must write 'True' to ir.config_parameter."""
        settings = self.env['res.config.settings'].create({
            'email_validation_enabled': True,
        })
        settings.execute()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'contacts_email_validator.email_validation'
        )
        self.assertEqual(param.lower(), 'true')

    def test_disable_sets_param_to_falsy(self):
        """Saving with email_validation_enabled=False must result in a falsy param value.
        Odoo deletes the ir.config_parameter record when a Boolean config_parameter
        field is saved as False, so get_param() returns False (bool) rather than a
        string. We assert the value is falsy in either form.
        """
        # First enable so the record exists, then disable
        s1 = self.env['res.config.settings'].create({'email_validation_enabled': True})
        s1.execute()
        s2 = self.env['res.config.settings'].create({'email_validation_enabled': False})
        s2.execute()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'contacts_email_validator.email_validation'
        )
        # After disabling, param is either False (deleted) or a falsy string
        if isinstance(param, str):
            self.assertNotEqual(param.lower(), 'true')
        else:
            self.assertFalse(param)

    def test_toggle_on_then_off(self):
        """Enabling then disabling must result in a non-true param value."""
        s1 = self.env['res.config.settings'].create({'email_validation_enabled': True})
        s1.execute()
        param_on = self.env['ir.config_parameter'].sudo().get_param(
            'contacts_email_validator.email_validation'
        )
        self.assertEqual(param_on.lower(), 'true')

        s2 = self.env['res.config.settings'].create({'email_validation_enabled': False})
        s2.execute()
        param_off = self.env['ir.config_parameter'].sudo().get_param(
            'contacts_email_validator.email_validation'
        )
        # Odoo removes the record on False, so get_param returns False (bool)
        if isinstance(param_off, str):
            self.assertNotEqual(param_off.lower(), 'true')
        else:
            self.assertFalse(param_off)

    def test_default_value_is_false(self):
        """A freshly created settings record must default email_validation_enabled to False.
        We ensure no leftover param exists before creating the settings record,
        since a prior test in the same transaction may have enabled it.
        """
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'contacts_email_validator.email_validation')
        ]).unlink()
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.email_validation_enabled)