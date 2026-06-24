# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
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
##############################################################################
from odoo.tests.common import TransactionCase


class TestPosSession(TransactionCase):
    """Test cases for PosSession._load_pos_data_models override."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config for Session',
            })

    def test_01_load_pos_data_models_returns_list(self):
        """Verify _load_pos_data_models returns a list."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id)
        self.assertIsInstance(result, list,
            "_load_pos_data_models should return a list.")


    def test_02_load_pos_data_models_includes_res_config_settings(self):
        """Verify res.config.settings is included in the models list."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id)
        self.assertIn('res.config.settings', result,
            "res.config.settings must be present in the POS data models list.")


    def test_03_load_pos_data_models_contains_multiple_models(self):
        """Verify the returned list contains core POS models from super()."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id)
        self.assertGreater(len(result), 1,
            "The models list should contain more than just res.config.settings.")


    def test_04_load_pos_data_models_res_config_settings_count(self):
        """Verify res.config.settings appears at least once."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id)
        self.assertGreaterEqual(result.count('res.config.settings'), 1,
            "res.config.settings should appear at least once in the list.")


    def test_05_load_pos_data_models_with_different_config(self):
        """Verify _load_pos_data_models works with any valid config_id."""
        second_config = self.env['pos.config'].create({
            'name': 'Second Test POS Config',
        })
        result = self.env['pos.session']._load_pos_data_models(
            second_config.id)
        self.assertIn('res.config.settings', result,
            "res.config.settings should be present for any config.")


    def test_06_load_pos_data_models_no_duplicate_base_models(self):
        """Verify core models are not duplicated (excluding res.config.settings)."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id)
        for model_name in result:
            if model_name != 'res.config.settings':
                self.assertEqual(result.count(model_name), 1,
                    f"Model '{model_name}' should not be duplicated.")


    def test_07_pos_session_has_override_method(self):
        """Verify pos.session model exposes _load_pos_data_models method."""
        self.assertTrue(
            hasattr(self.env['pos.session'], '_load_pos_data_models'),
            "pos.session must expose _load_pos_data_models method.")


    def test_08_load_pos_data_models_all_items_are_strings(self):
        """Verify all items returned are strings."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id)
        for item in result:
            self.assertIsInstance(item, str,
                f"Each model name must be a string, got: {type(item)}.")

