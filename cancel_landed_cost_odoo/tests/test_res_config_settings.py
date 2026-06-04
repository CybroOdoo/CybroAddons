# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

_CONFIG_PARAM = 'cancel_landed_cost_odoo.land_cost_cancel_modes'


def _set_cancel_mode(env, mode):
    """Helper — write the cancel mode directly to ir.config_parameter."""
    env['ir.config_parameter'].sudo().set_param(_CONFIG_PARAM, mode)


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for the ResConfigSettings model extension.
    TC-01 to TC-10
    """

    def setUp(self):
        super().setUp()
        # Reset to module default before every test
        _set_cancel_mode(self.env, 'cancel')
        self.config = self.env['res.config.settings'].create({})

    # -----------------------------------------------------------------------
    # Field existence & type  (TC-01 – TC-03)
    # -----------------------------------------------------------------------

    def test_01_land_cost_cancel_modes_field_exists(self):
        """TC-01: 'land_cost_cancel_modes' field must be present on res.config.settings."""
        self.assertIn(
            'land_cost_cancel_modes',
            self.env['res.config.settings']._fields,
            "Field 'land_cost_cancel_modes' must exist on res.config.settings",
        )


    def test_02_land_cost_cancel_modes_is_selection_field(self):
        """TC-02: 'land_cost_cancel_modes' must be declared as a
        fields.Selection field."""
        field = self.env['res.config.settings']._fields.get('land_cost_cancel_modes')
        self.assertIsNotNone(field)
        self.assertIsInstance(
            field, fields.Selection,
            "'land_cost_cancel_modes' must be a Selection field",
        )


    def test_03_land_cost_cancel_modes_has_three_valid_choices(self):
        """TC-03: The Selection field must expose exactly three choices:
        'cancel', 'cancel_draft', and 'cancel_delete'."""
        field = self.env['res.config.settings']._fields.get('land_cost_cancel_modes')
        keys = [key for key, _ in field.selection]
        self.assertEqual(len(keys), 3, "Exactly 3 selection choices expected")
        self.assertIn('cancel', keys)
        self.assertIn('cancel_draft', keys)
        self.assertIn('cancel_delete', keys)


    # -----------------------------------------------------------------------
    # Default value  (TC-04)
    # -----------------------------------------------------------------------

    def test_04_land_cost_cancel_modes_defaults_to_cancel(self):
        """TC-04: The default value of 'land_cost_cancel_modes' must be
        'cancel' as declared in the model."""
        field = self.env['res.config.settings']._fields.get('land_cost_cancel_modes')
        self.assertEqual(
            field.default(self.config), 'cancel',
            "Default value of 'land_cost_cancel_modes' must be 'cancel'",
        )


    # -----------------------------------------------------------------------
    # config_parameter persistence  (TC-05 – TC-07)
    # -----------------------------------------------------------------------

    def test_05_cancel_mode_persists_to_ir_config_parameter(self):
        """TC-05: Setting land_cost_cancel_modes='cancel' and executing the
        settings form must write 'cancel' to ir.config_parameter."""
        self.config.land_cost_cancel_modes = 'cancel'
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_CONFIG_PARAM)
        self.assertEqual(
            val, 'cancel',
            "ir.config_parameter must store 'cancel' after settings.execute()",
        )

    def test_06_cancel_draft_mode_persists_to_ir_config_parameter(self):
        """TC-06: Setting land_cost_cancel_modes='cancel_draft' and executing
        must write 'cancel_draft' to ir.config_parameter."""
        self.config.land_cost_cancel_modes = 'cancel_draft'
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_CONFIG_PARAM)
        self.assertEqual(
            val, 'cancel_draft',
            "ir.config_parameter must store 'cancel_draft'",
        )


    def test_07_cancel_delete_mode_persists_to_ir_config_parameter(self):
        """TC-07: Setting land_cost_cancel_modes='cancel_delete' and executing
        must write 'cancel_delete' to ir.config_parameter."""
        self.config.land_cost_cancel_modes = 'cancel_delete'
        self.config.execute()
        val = self.env['ir.config_parameter'].sudo().get_param(_CONFIG_PARAM)
        self.assertEqual(
            val, 'cancel_delete',
            "ir.config_parameter must store 'cancel_delete'",
        )

    # -----------------------------------------------------------------------
    # String label & config_parameter key  (TC-08 – TC-10)
    # -----------------------------------------------------------------------

    def test_08_field_string_label_is_operation_type(self):
        """TC-08: The string label of 'land_cost_cancel_modes' must be
        'Operation Type'."""
        field = self.env['res.config.settings']._fields.get('land_cost_cancel_modes')
        self.assertEqual(
            field.string, 'Operation Type',
            "Field string label must be 'Operation Type'",
        )

    def test_09_field_config_parameter_key_is_correct(self):
        """TC-09: The config_parameter backing key must be
        'cancel_landed_cost_odoo.land_cost_cancel_modes'."""
        field = self.env['res.config.settings']._fields.get('land_cost_cancel_modes')
        self.assertEqual(
            field.config_parameter,
            'cancel_landed_cost_odoo.land_cost_cancel_modes',
            "config_parameter key must be "
            "'cancel_landed_cost_odoo.land_cost_cancel_modes'",
        )


    def test_10_mode_change_is_reflected_on_new_config_record(self):
        """TC-10: After changing the config to 'cancel_draft', a freshly
        created settings record must read back 'cancel_draft'."""
        self.config.land_cost_cancel_modes = 'cancel_draft'
        self.config.execute()
        fresh = self.env['res.config.settings'].create({})
        self.assertEqual(
            fresh.land_cost_cancel_modes, 'cancel_draft',
            "New settings record must reflect the persisted 'cancel_draft' mode",
        )