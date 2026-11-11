# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import MagicMock

from odoo import fields
from odoo.http import request_var
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestHideFiltersGroupBy(TransactionCase):
    """Test suite for hide_filters_groupby module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.model_partner = cls.env['ir.model']._get('res.partner')
        cls.model_user = cls.env['ir.model']._get('res.users')

    def setUp(self):
        super().setUp()
        # Bind a mock request so session_info() can execute without web request errors
        user_context = dict(self.env.user.context_get(), lang='en_US')
        self.mock_req = MagicMock(
            env=self.env,
            session=MagicMock(
                uid=self.env.user.id,
                context=user_context,
            ),
            cookies={},
        )
        self.mock_req.session.get.return_value = None
        self.request_token = request_var.set(self.mock_req)
        self.addCleanup(request_var.reset, self.request_token)

        # Clean config parameters before each test
        self.icp.set_bool(
            'hide_filters_groupby.is_hide_filters_groupby_enabled', False
        )
        self.icp.set_str(
            'hide_filters_groupby.hide_filters_groupby', 'global'
        )
        self.icp.set_str(
            'hide_filters_groupby.ir_model_ids', ''
        )

    def test_01_default_settings_and_session_info(self):
        """Test default values in res.config.settings and ir.http.session_info."""
        # Test defaults loaded by res.config.settings
        defaults = self.env['res.config.settings'].default_get([
            'is_hide_filters_groupby_enabled',
            'hide_filters_groupby',
            'ir_model_ids',
        ])
        self.assertFalse(defaults.get('is_hide_filters_groupby_enabled'))
        self.assertEqual(defaults.get('hide_filters_groupby'), 'global')
        self.assertFalse(defaults.get('ir_model_ids'))

        # Test get_values directly
        values = self.env['res.config.settings'].get_values()
        self.assertFalse(values.get('ir_model_ids'))

        # Test session_info payload
        session_data = self.env['ir.http'].session_info()
        self.assertFalse(session_data.get('is_hide_filters_groupby_enabled'))
        self.assertEqual(session_data.get('hide_filters_groupby'), 'global')
        self.assertEqual(session_data.get('ir_model_ids'), '')
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

    def test_02_enable_global_mode(self):
        """Test saving global mode in res.config.settings and verifying session_info."""
        settings = self.env['res.config.settings'].create({
            'is_hide_filters_groupby_enabled': True,
            'hide_filters_groupby': 'global',
        })
        settings.execute()

        # Check system parameters
        self.assertTrue(
            self.icp.get_bool(
                'hide_filters_groupby.is_hide_filters_groupby_enabled'
            )
        )
        self.assertEqual(
            self.icp.get_str('hide_filters_groupby.hide_filters_groupby'),
            'global',
        )

        # Check settings retrieval
        defaults = self.env['res.config.settings'].default_get([
            'is_hide_filters_groupby_enabled',
            'hide_filters_groupby',
        ])
        self.assertTrue(defaults.get('is_hide_filters_groupby_enabled'))
        self.assertEqual(defaults.get('hide_filters_groupby'), 'global')

        # Check session_info payload
        session_data = self.env['ir.http'].session_info()
        self.assertTrue(session_data.get('is_hide_filters_groupby_enabled'))
        self.assertEqual(session_data.get('hide_filters_groupby'), 'global')
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

    def test_03_enable_custom_mode_with_models(self):
        """Test custom mode with specific models in settings and session_info."""
        selected_models = self.model_partner | self.model_user
        settings = self.env['res.config.settings'].create({
            'is_hide_filters_groupby_enabled': True,
            'hide_filters_groupby': 'custom',
            'ir_model_ids': [fields.Command.set(selected_models.ids)],
        })
        settings.execute()

        # Check system parameters
        self.assertTrue(
            self.icp.get_bool(
                'hide_filters_groupby.is_hide_filters_groupby_enabled'
            )
        )
        self.assertEqual(
            self.icp.get_str('hide_filters_groupby.hide_filters_groupby'),
            'custom',
        )
        stored_model_ids = self.icp.get_str('hide_filters_groupby.ir_model_ids')
        self.assertIn(str(self.model_partner.id), stored_model_ids)
        self.assertIn(str(self.model_user.id), stored_model_ids)

        # Check get_values and default_get
        values = self.env['res.config.settings'].get_values()
        loaded_model_command = values.get('ir_model_ids')
        self.assertTrue(loaded_model_command)
        self.assertEqual(
            set(loaded_model_command[0][2]),
            set(selected_models.ids),
        )

        defaults = self.env['res.config.settings'].default_get([
            'is_hide_filters_groupby_enabled',
            'hide_filters_groupby',
            'ir_model_ids',
        ])
        self.assertTrue(defaults.get('is_hide_filters_groupby_enabled'))
        self.assertEqual(defaults.get('hide_filters_groupby'), 'custom')
        self.assertEqual(
            set(defaults.get('ir_model_ids')[0][2]),
            set(selected_models.ids),
        )

        # Check session_info payload
        session_data = self.env['ir.http'].session_info()
        self.assertTrue(session_data.get('is_hide_filters_groupby_enabled'))
        self.assertEqual(session_data.get('hide_filters_groupby'), 'custom')
        models_in_session = session_data.get('hide_filters_groupby_models')
        self.assertIn('res.partner', models_in_session)
        self.assertIn('res.users', models_in_session)

    def test_04_clear_custom_models(self):
        """Test clearing models in custom mode."""
        settings = self.env['res.config.settings'].create({
            'is_hide_filters_groupby_enabled': True,
            'hide_filters_groupby': 'custom',
            'ir_model_ids': [fields.Command.clear()],
        })
        settings.execute()

        values = self.env['res.config.settings'].get_values()
        loaded_command = values.get('ir_model_ids')
        model_ids = loaded_command[0][2] if loaded_command else []
        self.assertEqual(model_ids, [])

        session_data = self.env['ir.http'].session_info()
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

    def test_05_disable_feature(self):
        """Test disabling the hide filters and groupby feature."""
        settings = self.env['res.config.settings'].create({
            'is_hide_filters_groupby_enabled': False,
            'hide_filters_groupby': 'global',
        })
        settings.execute()

        self.assertFalse(
            self.icp.get_bool(
                'hide_filters_groupby.is_hide_filters_groupby_enabled'
            )
        )

        session_data = self.env['ir.http'].session_info()
        self.assertFalse(session_data.get('is_hide_filters_groupby_enabled'))

    def test_06_session_info_edge_cases(self):
        """Test edge cases for ir_model_ids parsing in ir.http.session_info."""
        # 1. Non-list string (e.g. integer or dict string)
        self.icp.set_str('hide_filters_groupby.ir_model_ids', '12345')
        session_data = self.env['ir.http'].session_info()
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

        # 2. Non-list None string
        self.icp.set_str('hide_filters_groupby.ir_model_ids', 'None')
        session_data = self.env['ir.http'].session_info()
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

        # 3. Malformed syntax that triggers Exception in literal_eval
        self.icp.set_str('hide_filters_groupby.ir_model_ids', '[invalid syntax {')
        session_data = self.env['ir.http'].session_info()
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

        # 4. Empty string default
        self.icp.set_str('hide_filters_groupby.ir_model_ids', '')
        session_data = self.env['ir.http'].session_info()
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

        # 5. Non-existent model ID in valid list
        self.icp.set_str('hide_filters_groupby.ir_model_ids', '[99999999]')
        session_data = self.env['ir.http'].session_info()
        self.assertEqual(session_data.get('hide_filters_groupby_models'), [])

    def test_07_res_config_settings_get_values_empty(self):
        """Test get_values when hide_filters_groupby.ir_model_ids parameter is absent."""
        self.icp.search([
            ('key', '=', 'hide_filters_groupby.ir_model_ids')
        ]).unlink()
        values = self.env['res.config.settings'].get_values()
        self.assertFalse(values.get('ir_model_ids'))
