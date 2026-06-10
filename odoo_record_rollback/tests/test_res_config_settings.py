# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from ast import literal_eval
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for the ResConfigSettings extension in res_config_settings.py.

    Covers:
    - set_values() persists the Many2many IDs to ir.config_parameter.
    - get_values() reads back the correct IDs and populates the field.
    - Clearing all models and saving produces an empty-list param.
    - get_values() is robust when the param is missing or malformed.
    - set_values() and get_values() are consistent (round-trip).
    """

    def setUp(self):
        super().setUp()
        self.IrParam = self.env['ir.config_parameter'].sudo()
        self.param_key = 'odoo_record_rollback.res_rollback_model_ids'
        # Find two real ir.model records to use as test data
        models = self.env['ir.model'].search(
            [('model', 'in', ['res.partner', 'res.users'])], limit=2)
        self.model_a = models.filtered(lambda m: m.model == 'res.partner')
        self.model_b = models.filtered(lambda m: m.model == 'res.users')
        # Start from a clean param state
        self.IrParam.set_param(self.param_key, False)

    def _get_param_value(self):
        """Read the raw string value of the config parameter."""
        return self.IrParam.get_param(self.param_key)

    def _create_settings(self, model_ids=None):
        """Create a res.config.settings record with optional model IDs."""
        vals = {}
        if model_ids is not None:
            vals['res_rollback_model_ids'] = [(6, 0, model_ids)]
        return self.env['res.config.settings'].create(vals)

    # ------------------------------------------------------------------
    # set_values()
    # ------------------------------------------------------------------

    def test_set_values_saves_ids_to_config_parameter(self):
        """set_values() must write the selected model IDs as a stringified
        list into ir.config_parameter."""
        settings = self._create_settings([self.model_a.id])
        settings.set_values()
        raw = self._get_param_value()
        self.assertIsNotNone(raw, "Config parameter should be set after set_values()")
        stored_ids = literal_eval(raw)
        self.assertIn(self.model_a.id, stored_ids,
                      "model_a ID should be stored in the parameter")

    def test_set_values_saves_multiple_ids(self):
        """set_values() correctly stores multiple model IDs."""
        settings = self._create_settings([self.model_a.id, self.model_b.id])
        settings.set_values()
        raw = self._get_param_value()
        stored_ids = literal_eval(raw)
        self.assertIn(self.model_a.id, stored_ids)
        self.assertIn(self.model_b.id, stored_ids)

    def test_set_values_saves_empty_list_when_cleared(self):
        """When all models are removed and set_values() is called, the
        parameter value must become '[]'."""
        # First save some models
        settings = self._create_settings([self.model_a.id])
        settings.set_values()
        # Now clear and save
        settings_empty = self._create_settings([])
        settings_empty.set_values()
        raw = self._get_param_value()
        stored_ids = literal_eval(raw)
        self.assertEqual(stored_ids, [],
                         "Clearing the field should store an empty list param")

    def test_set_values_overwrites_previous_param(self):
        """A second call to set_values() with different models must overwrite
        the parameter, not append."""
        settings_first = self._create_settings([self.model_a.id])
        settings_first.set_values()

        settings_second = self._create_settings([self.model_b.id])
        settings_second.set_values()

        raw = self._get_param_value()
        stored_ids = literal_eval(raw)
        self.assertNotIn(self.model_a.id, stored_ids,
                         "Previous model should have been overwritten")
        self.assertIn(self.model_b.id, stored_ids,
                      "New model should be in the stored param")

    # ------------------------------------------------------------------
    # get_values()
    # ------------------------------------------------------------------

    def test_get_values_returns_configured_ids(self):
        """get_values() populates res_rollback_model_ids with the IDs that
        were previously stored by set_values()."""
        self.IrParam.set_param(self.param_key, str([self.model_a.id]))
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        ids_command = result.get('res_rollback_model_ids')
        self.assertIsNotNone(ids_command,
                             "res_rollback_model_ids key must be present in get_values() result")
        # The value is [(6, 0, [ids])]
        self.assertIsInstance(ids_command, list)
        self.assertEqual(ids_command[0][0], 6)
        self.assertIn(self.model_a.id, ids_command[0][2])

    def test_get_values_returns_empty_list_when_param_absent(self):
        """get_values() must return [(6, 0, [])] when the config parameter is
        not set, so the UI widget renders an empty field."""
        self.IrParam.set_param(self.param_key, False)
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        ids_command = result.get('res_rollback_model_ids')
        self.assertEqual(ids_command, [(6, 0, [])],
                         "get_values() should return empty command list when param is absent")

    def test_get_values_returns_empty_list_for_empty_param(self):
        """get_values() must return [(6, 0, [])] when the param is '[]'."""
        self.IrParam.set_param(self.param_key, '[]')
        settings = self.env['res.config.settings'].create({})
        result = settings.get_values()
        ids_command = result.get('res_rollback_model_ids')
        self.assertEqual(ids_command, [(6, 0, [])],
                         "get_values() should return empty command list for '[]' param")

    def test_get_values_is_robust_against_corrupt_param(self):
        """get_values() must not raise when the stored param is corrupt;
        it should return [(6, 0, [])] as a safe fallback."""
        self.IrParam.set_param(self.param_key, 'CORRUPT_VALUE_!!')
        settings = self.env['res.config.settings'].create({})
        try:
            result = settings.get_values()
            ids_command = result.get('res_rollback_model_ids')
            self.assertEqual(ids_command, [(6, 0, [])],
                             "Corrupt param should fall back to empty list")
        except Exception as exc:
            self.fail(f"get_values() raised unexpectedly with corrupt param: {exc}")

    # ------------------------------------------------------------------
    # Round-trip consistency
    # ------------------------------------------------------------------

    def test_set_then_get_round_trip_single_model(self):
        """A full set → get cycle with one model must produce consistent data."""
        settings = self._create_settings([self.model_a.id])
        settings.set_values()

        settings2 = self.env['res.config.settings'].create({})
        result = settings2.get_values()
        ids_command = result.get('res_rollback_model_ids')
        self.assertEqual(ids_command[0][2], [self.model_a.id],
                         "Round-trip: get_values() should return the same ID as set_values() stored")

    def test_set_then_get_round_trip_multiple_models(self):
        """A full set → get cycle with multiple models must be consistent."""
        expected_ids = sorted([self.model_a.id, self.model_b.id])
        settings = self._create_settings(expected_ids)
        settings.set_values()

        settings2 = self.env['res.config.settings'].create({})
        result = settings2.get_values()
        ids_command = result.get('res_rollback_model_ids')
        self.assertEqual(sorted(ids_command[0][2]), expected_ids,
                         "Round-trip: all model IDs should survive set→get cycle")

    def test_set_then_get_round_trip_clear(self):
        """Saving with no models and reading back must produce an empty list."""
        # Set some models first
        settings = self._create_settings([self.model_a.id])
        settings.set_values()
        # Clear
        settings_empty = self._create_settings([])
        settings_empty.set_values()
        # Read back
        settings3 = self.env['res.config.settings'].create({})
        result = settings3.get_values()
        ids_command = result.get('res_rollback_model_ids')
        self.assertEqual(ids_command, [(6, 0, [])],
                         "After clearing, round-trip should yield empty list")

    # ------------------------------------------------------------------
    # Field definition
    # ------------------------------------------------------------------

    def test_res_rollback_model_ids_field_exists(self):
        """The res_rollback_model_ids field must exist on res.config.settings."""
        self.assertIn('res_rollback_model_ids',
                      self.env['res.config.settings']._fields,
                      "res_rollback_model_ids field must be defined on the model")

    def test_res_rollback_model_ids_is_many2many(self):
        """res_rollback_model_ids must be a Many2many field linked to ir.model."""
        field = self.env['res.config.settings']._fields.get('res_rollback_model_ids')
        self.assertIsNotNone(field)
        self.assertEqual(field.type, 'many2many',
                         "res_rollback_model_ids should be a Many2many field")
        self.assertEqual(field.comodel_name, 'ir.model',
                         "res_rollback_model_ids should relate to ir.model")
