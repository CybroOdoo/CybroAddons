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
from unittest.mock import MagicMock, patch

import openai

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOpenAIProductImages(TransactionCase):
    """Test suite for AI product image generation actions and workflows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'AI Camera Lens',
            'list_price': 250.0,
        })
        cls.product_tmpl_2 = cls.env['product.template'].create({
            'name': 'AI Camera Tripod',
            'list_price': 80.0,
        })
        cls.dummy_image_b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='

    def test_action_open_image_prompt_wizard_single(self):
        """Test wizard action opens successfully for a single product template."""
        action = self.product_tmpl.action_open_image_prompt_wizard()
        self.assertEqual(action['res_model'], 'image.suggestion')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_product_tmpl_id'], self.product_tmpl.id)

    def test_action_open_image_prompt_wizard_multiple(self):
        """Test opening wizard with multiple templates raises UserError."""
        templates = self.product_tmpl | self.product_tmpl_2
        with self.assertRaises(UserError):
            templates.action_open_image_prompt_wizard()

    def test_action_view_ai_images(self):
        """Test action to view generated AI images for the product."""
        action = self.product_tmpl.action_view_ai_images()
        self.assertEqual(action['res_model'], 'openai.image.suggestion')
        self.assertIn(('product_tmpl_id', '=', self.product_tmpl.id), action['domain'])

    def test_action_set_as_product_image(self):
        """Test promoting an AI generated suggestion to be the product template's main image."""
        ai_suggestion = self.env['openai.image.suggestion'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'product_image': self.dummy_image_b64,
        })
        self.assertFalse(self.product_tmpl.image_1920)

        self.assertIn("AI Camera Lens", ai_suggestion.display_name)
        action = ai_suggestion.action_set_as_product_image()
        self.assertTrue(self.product_tmpl.image_1920)
        self.assertEqual(action['res_model'], 'product.template')
        self.assertEqual(action['res_id'], self.product_tmpl.id)

        # Test backward-compatible alias
        alias_action = ai_suggestion.action_make_as_product_image()
        self.assertEqual(alias_action['res_model'], 'product.template')

    def test_wizard_missing_api_key_raises_error(self):
        """Test that running the generation wizard without configuring an API key raises UserError."""
        self.env['ir.config_parameter'].sudo().set_str('openai_api_key', '')

        wizard = self.env['image.suggestion'].create({
            'image_prompt': 'A high quality studio photograph of a camera lens',
            'product_tmpl_id': self.product_tmpl.id,
            'num_image': 1,
            'size_image': '1024x1024',
            'quality': 'low',
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_generate_images()
        self.assertIn("API key", str(cm.exception))

    def test_wizard_action_generate_images_success(self):
        """Test successful execution of image generation wizard with mocked OpenAI API."""
        self.env['ir.config_parameter'].sudo().set_str('openai_api_key', 'sk-mock-key-1234')

        wizard = self.env['image.suggestion'].create({
            'image_prompt': 'A sleek modern coffee grinder',
            'product_tmpl_id': self.product_tmpl.id,
            'num_image': 2,
            'size_image': '1024x1024',
            'quality': 'medium',
        })

        mock_image_item = MagicMock()
        mock_image_item.b64_json = self.dummy_image_b64
        mock_response = MagicMock()
        mock_response.data = [mock_image_item, mock_image_item]

        with patch('odoo.addons.openai_product_images.wizard.image_suggestion.OpenAI') as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            res = wizard.action_generate_images()
            self.assertEqual(res['type'], 'ir.actions.act_window_close')

            suggestions = self.env['openai.image.suggestion'].search([
                ('product_tmpl_id', '=', self.product_tmpl.id),
            ])
            self.assertEqual(len(suggestions), 2)
            mock_client.images.generate.assert_called_once()
            self.assertEqual(
                mock_client.images.generate.call_args.kwargs['n'], 2)
            self.assertTrue(self.product_tmpl.image_1920)

    def test_wizard_action_generate_images_api_failure(self):
        """Test error handling when OpenAI API raises an exception."""
        self.env['ir.config_parameter'].sudo().set_str('openai_api_key', 'sk-mock-key-1234')

        wizard = self.env['image.suggestion'].create({
            'image_prompt': 'A modern lamp',
            'product_tmpl_id': self.product_tmpl.id,
            'num_image': 1,
            'size_image': '1024x1024',
            'quality': 'medium',
        })

        with patch('odoo.addons.openai_product_images.wizard.image_suggestion.OpenAI') as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.side_effect = openai.OpenAIError(
                "Rate limit exceeded")
            mock_openai_cls.return_value = mock_client

            with self.assertRaises(UserError) as cm, mute_logger(
                    'odoo.addons.openai_product_images.wizard.image_suggestion'):
                wizard.action_generate_images()
            self.assertNotIn("Rate limit exceeded", str(cm.exception))
            self.assertFalse(self.env['openai.image.suggestion'].search_count(
                [('product_tmpl_id', '=', self.product_tmpl.id)]))

    def test_wizard_num_image_constraint(self):
        """Test the number of images must be between 1 and 4."""
        for value in (0, -1, 5):
            with self.assertRaises(ValidationError):
                self.env['image.suggestion'].create({
                    'image_prompt': 'A lamp',
                    'product_tmpl_id': self.product_tmpl.id,
                    'num_image': value,
                })

    def test_wizard_access_rights(self):
        """Test only product managers can generate; users can only read."""
        user = new_test_user(
            self.env, login='opi_plain_user', groups='base.group_user')
        manager = new_test_user(
            self.env, login='opi_manager',
            groups='base.group_user,product.group_product_manager')
        with self.assertRaises(AccessError):
            self.env['image.suggestion'].with_user(user).create({
                'image_prompt': 'A lamp',
                'product_tmpl_id': self.product_tmpl.id,
            })
        wizard = self.env['image.suggestion'].with_user(manager).create({
            'image_prompt': 'A lamp',
            'product_tmpl_id': self.product_tmpl.id,
        })
        self.assertTrue(wizard)
        suggestion = self.env['openai.image.suggestion'].with_user(
            manager).create({
                'product_tmpl_id': self.product_tmpl.id,
                'product_image': self.dummy_image_b64,
            })
        self.assertTrue(suggestion.with_user(user).read(['product_image']))
        with self.assertRaises(AccessError):
            suggestion.with_user(user).unlink()
