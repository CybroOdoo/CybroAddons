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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for AI image generator settings in res.config.settings."""

    def _get_config_param(self, key, type_='str'):
        """Fetch a system parameter value."""
        ICP = self.env['ir.config_parameter'].sudo()
        if type_ == 'bool':
            return ICP.get_bool(key)
        if type_ == 'int':
            return ICP.get_int(key)
        return ICP.get_str(key) or ''

    def test_res_config_settings_set_and_get_values(self):
        """Test setting and retrieving AI image generation configuration values."""
        settings = self.env['res.config.settings'].create({
            'ai_brand_dna': 'Clean minimalist, soft studio lighting, pastel colors',
            'openai_api_key': 'sk-openai-test-api-key',
            'stability_api_key': 'sk-stability-test-api-key',
            'gemini_api_key': 'sk-gemini-test-api-key',
            'ai_approval_required': True,
            'ai_max_variants': 3,
        })
        settings.set_values()

        loaded = self.env['res.config.settings'].default_get([
            'ai_brand_dna',
            'openai_api_key',
            'stability_api_key',
            'gemini_api_key',
            'ai_approval_required',
            'ai_max_variants',
        ])
        self.assertEqual(
            loaded.get('ai_brand_dna'),
            'Clean minimalist, soft studio lighting, pastel colors',
        )
        self.assertEqual(loaded.get('openai_api_key'), 'sk-openai-test-api-key')
        self.assertEqual(loaded.get('stability_api_key'), 'sk-stability-test-api-key')
        self.assertEqual(loaded.get('gemini_api_key'), 'sk-gemini-test-api-key')
        self.assertTrue(loaded.get('ai_approval_required'))
        self.assertEqual(loaded.get('ai_max_variants'), 3)

        self.assertEqual(
            self._get_config_param('smart_product_image_generator.brand_dna'),
            'Clean minimalist, soft studio lighting, pastel colors',
        )
        self.assertEqual(
            self._get_config_param('smart_product_image_generator.openai_api_key'),
            'sk-openai-test-api-key',
        )
        self.assertEqual(
            self._get_config_param('smart_product_image_generator.stability_api_key'),
            'sk-stability-test-api-key',
        )
        self.assertEqual(
            self._get_config_param('smart_product_image_generator.gemini_api_key'),
            'sk-gemini-test-api-key',
        )
        self.assertTrue(
            self._get_config_param('smart_product_image_generator.approval_required', 'bool')
        )
        self.assertEqual(
            self._get_config_param('smart_product_image_generator.max_variants', 'int'),
            3,
        )

    def test_res_config_settings_default_values(self):
        """Test default values on new res.config.settings record."""
        settings = self.env['res.config.settings'].new()
        self.assertEqual(settings.ai_max_variants, 4)

    def test_res_config_settings_update_parameters(self):
        """Test updating AI image configuration parameters re-syncs accurately."""
        settings = self.env['res.config.settings'].create({
            'ai_brand_dna': 'Updated brand DNA statement',
            'ai_approval_required': False,
            'ai_max_variants': 2,
        })
        settings.set_values()

        self.assertEqual(
            self._get_config_param('smart_product_image_generator.brand_dna'),
            'Updated brand DNA statement',
        )
        self.assertFalse(
            self._get_config_param('smart_product_image_generator.approval_required', 'bool')
        )
        self.assertEqual(
            self._get_config_param('smart_product_image_generator.max_variants', 'int'),
            2,
        )
