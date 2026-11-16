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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for product recommendation configuration settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param_obj = cls.env['ir.config_parameter'].sudo()

    def test_default_config_settings(self):
        """Test default values of recommendation configuration fields."""
        # Remove any value saved on this database (e.g. from manual testing)
        # so the test checks the real defaults. The test transaction is rolled back.
        self.config_param_obj.search([
            ('key', '=like', 'product_recommendation_ai.%'),
        ]).unlink()
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.model_choice, 'fast')
        self.assertEqual(settings.product_metadata, 'description')
        self.assertEqual(settings.recommendation_limit, 4)
        self.assertFalse(settings.enable_recommendations)
        self.assertFalse(settings.nomic_token)

    def test_execute_fast_model_without_token(self):
        """Test executing settings with 'fast' model does not require a Nomic token."""
        settings = self.env['res.config.settings'].create({
            'model_choice': 'fast',
            'nomic_token': False,
        })
        # Should execute without raising any UserError
        settings.execute()
        saved_model = self.config_param_obj.get_str('product_recommendation_ai.model_choice')
        self.assertEqual(saved_model, 'fast')

    def test_execute_accurate_model_without_token_raises_error(self):
        """Test executing settings with 'accurate' model without a Nomic token raises UserError."""
        settings = self.env['res.config.settings'].create({
            'model_choice': 'accurate',
            'nomic_token': False,
        })
        with self.assertRaises(UserError) as err:
            settings.execute()
        self.assertIn(
            "Configuration Error: You must provide a Nomic API Token",
            str(err.exception)
        )

    def test_execute_accurate_model_with_token_succeeds(self):
        """Test executing settings with 'accurate' model and a valid token succeeds."""
        token = "test_nomic_token_12345"
        settings = self.env['res.config.settings'].create({
            'model_choice': 'accurate',
            'nomic_token': token,
        })
        settings.execute()
        saved_model = self.config_param_obj.get_str('product_recommendation_ai.model_choice')
        saved_token = self.config_param_obj.get_str('product_recommendation_ai.nomic_token')
        self.assertEqual(saved_model, 'accurate')
        self.assertEqual(saved_token, token)

    def test_custom_parameters_persistence(self):
        """Test saving custom metadata options, limit, and enablement in settings."""
        settings = self.env['res.config.settings'].create({
            'model_choice': 'fast',
            'product_metadata': 'name_categ',
            'recommendation_limit': 8,
            'enable_recommendations': True,
        })
        settings.execute()

        metadata = self.config_param_obj.get_str('product_recommendation_ai.product_metadata')
        limit = int(self.config_param_obj.get_str('product_recommendation_ai.recommendation_limit'))
        enabled = self.config_param_obj.get_bool('product_recommendation_ai.enable_recommendations')

        self.assertEqual(metadata, 'name_categ')
        self.assertEqual(limit, 8)
        self.assertTrue(enabled)
