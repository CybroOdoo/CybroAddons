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
import base64
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes


@tagged('post_install', '-at_install')
class TestProductAiImageLine(TransactionCase):
    """Test cases for product.ai.image.line model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Desk Lamp',
            'list_price': 45.0,
        })
        cls.wizard = cls.env['smart.product.image.generator'].create({
            'product_id': cls.product.id,
        })
        cls.sample_b64 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
            '+A8AAQUBAScY42YAAAAASUVORK5CYII='
        )
        cls.image_line = cls.env['product.ai.image.line'].create({
            'wizard_id': cls.wizard.id,
            'image': cls.sample_b64,
            'image_name': 'test_line.png',
            'provider_used': 'Stability AI',
            'style_used': 'Professional Product Photo',
        })

    def test_action_apply_image_line_success(self):
        """Test action_apply_image_line delegates to wizard.action_apply_image."""
        action = self.image_line.action_apply_image_line()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'reload')
        self.assertTrue(bool(self.product.image_1920))

    def test_action_apply_image_line_wizard_expired_raises(self):
        """Test action_apply_image_line raises UserError when wizard does not exist."""
        with patch.object(type(self.image_line.wizard_id), 'exists', return_value=False):
            with self.assertRaises(UserError):
                self.image_line.action_apply_image_line()


@tagged('post_install', '-at_install')
class TestSmartProductImageGenerator(TransactionCase):
    """Test cases for smart.product.image.generator wizard functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Electronics & Gadgets',
        })
        cls.product = cls.env['product.template'].create({
            'name': 'Wireless Noise Canceling Headphones',
            'categ_id': cls.category.id,
            'list_price': 250.0,
            'description_sale': 'Comfortable over-ear headphones with superior sound quality.',
        })
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Color',
            'create_variant': 'no_variant',
        })
        cls.value_black = cls.env['product.attribute.value'].create({
            'name': 'Matte Black',
            'attribute_id': cls.attribute.id,
        })
        cls.value_silver = cls.env['product.attribute.value'].create({
            'name': 'Silver',
            'attribute_id': cls.attribute.id,
        })
        cls.env['product.template.attribute.line'].create({
            'product_tmpl_id': cls.product.id,
            'attribute_id': cls.attribute.id,
            'value_ids': [(6, 0, [cls.value_black.id, cls.value_silver.id])],
        })

        cls.sample_b64_str = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
            '+A8AAQUBAScY42YAAAAASUVORK5CYII='
        )
        cls.sample_png_bytes = base64.b64decode(cls.sample_b64_str)

    def _set_config_param(self, key, value):
        """Set a system parameter."""
        self.env['ir.config_parameter'].sudo().set_str(key, value)

    def _get_config_param(self, key, default=''):
        """Get a system parameter."""
        return self.env['ir.config_parameter'].sudo().get_str(key, default)

    # ── _compute_ai_prompt ─────────────────────────────────────────

    def test_compute_ai_prompt_styles(self):
        """Test prompt generation for each image style."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
            'image_style': 'professional',
        })
        wizard._compute_ai_prompt()
        self.assertIn('Professional high-resolution product photograph', wizard.prompt)
        self.assertIn('Category: Electronics & Gadgets', wizard.prompt)
        self.assertIn('Attributes: Color: Matte Black, Silver', wizard.prompt)
        self.assertIn('This is a premium product.', wizard.prompt)

        wizard.image_style = 'lifestyle'
        wizard._compute_ai_prompt()
        self.assertIn('Lifestyle product photograph in a real-world context', wizard.prompt)

        wizard.image_style = 'minimal'
        wizard._compute_ai_prompt()
        self.assertIn('Minimalist product photograph', wizard.prompt)

        wizard.image_style = 'artistic'
        wizard._compute_ai_prompt()
        self.assertIn('Artistic product visualization', wizard.prompt)

        wizard.image_style = False
        wizard._compute_ai_prompt()
        self.assertIn('Professional high-resolution product photograph', wizard.prompt)

    def test_compute_ai_prompt_brand_dna(self):
        """Test prompt includes brand DNA when configured in ir.config_parameter."""
        self._set_config_param(
            'smart_product_image_generator.brand_dna',
            'Nordic aesthetic with warm shadows',
        )

        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
            'image_style': 'professional',
        })
        wizard._compute_ai_prompt()
        self.assertIn('Nordic aesthetic with warm shadows', wizard.prompt)

        # Clear brand DNA
        self._set_config_param('smart_product_image_generator.brand_dna', '')
        wizard._compute_ai_prompt()
        self.assertNotIn('Nordic aesthetic with warm shadows', wizard.prompt)

    def test_compute_ai_prompt_price_tiers(self):
        """Test prompt price tier detection (budget, mid-range, premium)."""
        product_budget = self.env['product.template'].create({
            'name': 'Budget Cable',
            'list_price': 15.0,
        })
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': product_budget.id,
        })
        wizard._compute_ai_prompt()
        self.assertIn('This is a budget-friendly product.', wizard.prompt)

        product_mid = self.env['product.template'].create({
            'name': 'Mid-range Case',
            'list_price': 99.0,
        })
        wizard.product_id = product_mid
        wizard._compute_ai_prompt()
        self.assertIn('This is a mid-range product.', wizard.prompt)

        product_zero = self.env['product.template'].create({
            'name': 'Free Sample',
            'list_price': 0.0,
        })
        wizard.product_id = product_zero
        wizard._compute_ai_prompt()
        self.assertIn('This is a budget-friendly product.', wizard.prompt)

    def test_compute_ai_prompt_description_truncation(self):
        """Test product description is truncated to 300 characters."""
        long_description = 'x' * 500
        product_long = self.env['product.template'].create({
            'name': 'Long Description Product',
            'list_price': 50.0,
            'description_sale': long_description,
        })
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': product_long.id,
        })
        wizard._compute_ai_prompt()
        self.assertIn('Description: ' + ('x' * 300), wizard.prompt)
        self.assertNotIn('x' * 301, wizard.prompt)

    def test_compute_ai_prompt_no_product(self):
        """Test compute_ai_prompt sets empty prompt when product_id is not set."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': False,
        })
        wizard._compute_ai_prompt()
        self.assertEqual(wizard.prompt, '')

    # ── _check_num_variants ─────────────────────────────────────────

    def test_check_num_variants(self):
        """Test validation constraint on number of variants (1 to 4)."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'num_variants': 2,
        })
        wizard._check_num_variants()

        wizard.num_variants = 1
        wizard._check_num_variants()

        wizard.num_variants = 4
        wizard._check_num_variants()

        with self.assertRaises(ValidationError):
            wizard.num_variants = 0
            wizard._check_num_variants()

        with self.assertRaises(ValidationError):
            wizard.num_variants = 5
            wizard._check_num_variants()

        with self.assertRaises(ValidationError):
            wizard.num_variants = -1
            wizard._check_num_variants()

    # ── _get_config_param ──────────────────────────────────────────

    def test_get_config_param(self):
        """Test _get_config_param handles existing and missing parameters with defaults."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
        })
        self._set_config_param('test_param_key', 'test_val')
        self.assertEqual(wizard._get_config_param('test_param_key'), 'test_val')
        self.assertEqual(
            wizard._get_config_param('non_existent_key', default='fallback'),
            'fallback',
        )
        self.assertEqual(wizard._get_config_param('non_existent_key_no_def'), '')

    # ── _is_approval_required & _get_selection_labels ──────────────

    def test_is_approval_required(self):
        """Test _is_approval_required reads smart_product_image_generator.approval_required."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
        })
        self._set_config_param('smart_product_image_generator.approval_required', 'False')
        self.assertFalse(wizard._is_approval_required())

        self._set_config_param('smart_product_image_generator.approval_required', 'True')
        self.assertTrue(wizard._is_approval_required())

        self._set_config_param('smart_product_image_generator.approval_required', 'False')
        self.assertFalse(wizard._is_approval_required())

    def test_get_selection_labels(self):
        """Test _get_selection_labels returns human-readable provider and style labels."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
            'ai_provider': 'openai',
            'image_style': 'lifestyle',
        })
        provider_label, style_label = wizard._get_selection_labels()
        self.assertEqual(provider_label, 'OpenAI DALL-E 3')
        self.assertEqual(style_label, 'Lifestyle / In Context')

    # ── _get_api_key ───────────────────────────────────────────────

    def test_get_api_key_success_and_missing(self):
        """Test _get_api_key returns configured key or raises UserError."""
        self._set_config_param(
            'smart_product_image_generator.openai_api_key', '  sk-openai-valid  '
        )
        self._set_config_param(
            'smart_product_image_generator.stability_api_key', 'sk-stability-valid'
        )
        self._set_config_param(
            'smart_product_image_generator.gemini_api_key', 'sk-gemini-valid'
        )

        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
        })

        self.assertEqual(wizard._get_api_key('openai'), 'sk-openai-valid')
        self.assertEqual(wizard._get_api_key('stability'), 'sk-stability-valid')
        self.assertEqual(wizard._get_api_key('gemini'), 'sk-gemini-valid')

        # Test unconfigured key raises UserError
        self._set_config_param('smart_product_image_generator.openai_api_key', '')
        with self.assertRaises(UserError):
            wizard._get_api_key('openai')

        # Test unknown provider raises UserError
        with self.assertRaises(UserError):
            wizard._get_api_key('unknown_provider')

    # ── _extract_raw_bytes and _to_b64_bytes ──────────────────────

    def test_extract_raw_bytes(self):
        """Test _extract_raw_bytes for various input types."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
        })

        # Empty data
        self.assertEqual(wizard._extract_raw_bytes(None), b'')
        self.assertEqual(wizard._extract_raw_bytes(''), b'')

        # Magic bytes: PNG, JPEG, GIF, RIFF
        png_bytes = b'\x89PNG\r\n\x1a\n'
        self.assertEqual(wizard._extract_raw_bytes(png_bytes), png_bytes)
        jpeg_bytes = b'\xff\xd8\xff\xe0'
        self.assertEqual(wizard._extract_raw_bytes(jpeg_bytes), jpeg_bytes)
        gif_bytes = b'GIF89a'
        self.assertEqual(wizard._extract_raw_bytes(gif_bytes), gif_bytes)
        riff_bytes = b'RIFF1234'
        self.assertEqual(wizard._extract_raw_bytes(riff_bytes), riff_bytes)

        # Base64 encoded bytes
        raw = b'my-image-data'
        b64_bytes = base64.b64encode(raw)
        self.assertEqual(wizard._extract_raw_bytes(b64_bytes), raw)

        # Base64 encoded string
        b64_str = base64.b64encode(raw).decode('ascii')
        self.assertEqual(wizard._extract_raw_bytes(b64_str), raw)

        # Plain non-base64 string
        plain_str = 'ordinary-string'
        self.assertEqual(wizard._extract_raw_bytes(plain_str), plain_str.encode('utf-8'))

        # Object with .content attribute
        mock_obj = MagicMock()
        mock_obj.content = b'mock-content'
        self.assertEqual(wizard._extract_raw_bytes(mock_obj), b'mock-content')

        # BinaryValue / BinaryBytes instance
        bin_val = BinaryBytes(b'binary-bytes-content')
        self.assertEqual(wizard._extract_raw_bytes(bin_val), b'binary-bytes-content')

    def test_to_b64_bytes(self):
        """Test _to_b64_bytes handles empty, BinaryValue, and raw inputs."""
        wizard = self.env['smart.product.image.generator'].new({
            'product_id': self.product.id,
        })
        self.assertFalse(wizard._to_b64_bytes(None))
        self.assertFalse(wizard._to_b64_bytes(''))

        bin_val = BinaryBytes(b'existing-binary')
        self.assertIs(wizard._to_b64_bytes(bin_val), bin_val)

        res = wizard._to_b64_bytes(b'test-data')
        self.assertTrue(bool(res))

    # ── _safe_log ──────────────────────────────────────────────────

    def test_safe_log(self):
        """Test _safe_log creates log records and catches internal errors without raising."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'ai_provider': 'stability',
            'image_style': 'lifestyle',
            'image_size': '1024x1024',
            'num_variants': 2,
        })
        wizard._safe_log(status='success', image_applied=True)

        log = self.env['ai.image.generation.log'].search([
            ('product_id', '=', self.product.id),
        ], order='id desc', limit=1)
        self.assertTrue(log)
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.ai_provider, 'stability')
        self.assertEqual(log.image_style, 'lifestyle')
        self.assertTrue(log.image_applied)

        # Verify exceptions in logging are swallowed safely
        log_model = type(self.env['ai.image.generation.log'].sudo())
        with patch.object(log_model, 'create', side_effect=Exception('Log DB crash')):
            # Must not raise
            wizard._safe_log(status='failed', error_message='Handled error')

    # ── _generate_openai ───────────────────────────────────────────

    @patch('requests.post')
    @patch('requests.get')
    def test_generate_openai_success(self, mock_get, mock_post):
        """Test _generate_openai parses OpenAI b64_json and url responses without response_format."""
        self._set_config_param('smart_product_image_generator.openai_api_key', 'sk-mock-openai')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })

        # Test b64_json response (gpt-image-1 default)
        mock_post_b64 = MagicMock()
        mock_post_b64.json.return_value = {
            'data': [{'b64_json': self.sample_b64_str}]
        }
        mock_post.return_value = mock_post_b64

        images = wizard._generate_openai(
            prompt='Test OpenAI Prompt',
            num_variants=1,
            image_size='1792x1024',
            enhance_desc='Add subtle shadow',
        )

        self.assertEqual(len(images), 1)
        mock_post.assert_called_once()
        sent_payload = mock_post.call_args[1]['json']
        self.assertIn('Enhancement: Add subtle shadow', sent_payload['prompt'])
        self.assertEqual(sent_payload['size'], '1536x1024')
        self.assertEqual(sent_payload['model'], 'gpt-image-1')
        self.assertEqual(sent_payload['quality'], 'high')
        self.assertNotIn('response_format', sent_payload)

        # Test url fallback response
        mock_post.reset_mock()
        mock_post_url = MagicMock()
        mock_post_url.json.return_value = {
            'data': [{'url': 'https://example.com/openai_image.png'}]
        }
        mock_post.return_value = mock_post_url
        mock_get_resp = MagicMock()
        mock_get_resp.content = self.sample_png_bytes
        mock_get.return_value = mock_get_resp

        images_url = wizard._generate_openai(
            prompt='Test URL Fallback',
            num_variants=1,
            image_size='1024x1792',
        )
        self.assertEqual(len(images_url), 1)
        self.assertEqual(mock_post.call_args[1]['json']['size'], '1024x1536')

        # Test empty item raises UserError
        mock_post_empty = MagicMock()
        mock_post_empty.json.return_value = {'data': [{}]}
        mock_post.return_value = mock_post_empty
        with self.assertRaises(UserError):
            wizard._generate_openai('Prompt', 1, '1024x1024')

    @patch('requests.post')
    def test_generate_openai_http_error(self, mock_post):
        """Test _generate_openai handles HTTPError with API error message."""
        self._set_config_param('smart_product_image_generator.openai_api_key', 'sk-mock-openai')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })

        mock_response = MagicMock()
        mock_response.json.return_value = {'error': {'message': 'OpenAI Quota Exceeded'}}
        mock_post.side_effect = requests.exceptions.HTTPError(
            '429 Client Error', response=mock_response
        )

        with self.assertRaises(UserError) as cm:
            wizard._generate_openai('Prompt', 1, '1024x1024')
        self.assertIn('OpenAI Quota Exceeded', str(cm.exception))

    @patch('requests.post')
    def test_generate_openai_generic_error(self, mock_post):
        """Test _generate_openai handles unexpected connection errors."""
        self._set_config_param('smart_product_image_generator.openai_api_key', 'sk-mock-openai')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })
        mock_post.side_effect = requests.exceptions.ConnectionError('Network unreachable')

        with self.assertRaises(UserError) as cm:
            wizard._generate_openai('Prompt', 1, '1024x1024')
        self.assertIn('OpenAI request failed', str(cm.exception))

    # ── _generate_stability ────────────────────────────────────────

    @patch('requests.post')
    def test_generate_stability_success(self, mock_post):
        """Test _generate_stability parses Stability AI response successfully."""
        self._set_config_param(
            'smart_product_image_generator.stability_api_key', 'sk-mock-stability'
        )

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })

        mock_post_resp = MagicMock()
        mock_post_resp.content = self.sample_png_bytes
        mock_post.return_value = mock_post_resp

        images = wizard._generate_stability(
            prompt='Stability Prompt',
            num_variants=2,
            image_size='1024x1792',
            existing_image=self.sample_png_bytes,
            enhance_desc='High detail background',
        )

        self.assertEqual(len(images), 2)
        self.assertEqual(mock_post.call_count, 2)
        files_sent = mock_post.call_args[1]['files']
        self.assertEqual(files_sent['aspect_ratio'][1], '9:16')
        self.assertIn('image', files_sent)

    @patch('requests.post')
    def test_generate_stability_http_error(self, mock_post):
        """Test _generate_stability handles HTTPError from Stability AI."""
        self._set_config_param(
            'smart_product_image_generator.stability_api_key', 'sk-mock-stability'
        )

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {'message': 'Insufficient credits'}
        mock_post.side_effect = requests.exceptions.HTTPError(
            '402 Payment Required', response=mock_response
        )

        with self.assertRaises(UserError) as cm:
            wizard._generate_stability('Prompt', 1, '1024x1024')
        self.assertIn('Insufficient credits', str(cm.exception))

    @patch('requests.post')
    def test_generate_stability_generic_error(self, mock_post):
        """Test _generate_stability handles general exceptions."""
        self._set_config_param(
            'smart_product_image_generator.stability_api_key', 'sk-mock-stability'
        )

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })
        mock_post.side_effect = Exception('Unexpected stability crash')

        with self.assertRaises(UserError) as cm:
            wizard._generate_stability('Prompt', 1, '1024x1024')
        self.assertIn('Stability AI request failed', str(cm.exception))

    # ── _generate_gemini ───────────────────────────────────────────

    @patch('requests.post')
    def test_generate_gemini_success(self, mock_post):
        """Test _generate_gemini extracts inlineData images from response."""
        self._set_config_param('smart_product_image_generator.gemini_api_key', 'sk-mock-gemini')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })

        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'inlineData': {
                                    'mimeType': 'image/png',
                                    'data': self.sample_b64_str,
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_post_resp

        images = wizard._generate_gemini(
            prompt='Gemini Prompt',
            num_variants=1,
            image_size='1024x1024',
            existing_image=self.sample_png_bytes,
            enhance_desc='Sharpen edges',
        )

        self.assertEqual(len(images), 1)

    @patch('requests.post')
    def test_generate_gemini_no_image_returned_raises(self, mock_post):
        """Test _generate_gemini raises UserError when candidate contains no image."""
        self._set_config_param('smart_product_image_generator.gemini_api_key', 'sk-mock-gemini')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })

        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {'candidates': []}
        mock_post.return_value = mock_post_resp

        with self.assertRaises(UserError) as cm:
            wizard._generate_gemini('Prompt', 1, '1024x1024')
        self.assertIn('Gemini returned no images', str(cm.exception))

    @patch('requests.post')
    def test_generate_gemini_http_error(self, mock_post):
        """Test _generate_gemini handles HTTPError."""
        self._set_config_param('smart_product_image_generator.gemini_api_key', 'sk-mock-gemini')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': {'message': 'Invalid Gemini API key'}}
        mock_post.side_effect = requests.exceptions.HTTPError(
            '400 Bad Request', response=mock_response
        )

        with self.assertRaises(UserError) as cm:
            wizard._generate_gemini('Prompt', 1, '1024x1024')
        self.assertIn('Invalid Gemini API key', str(cm.exception))

    @patch('requests.post')
    def test_generate_gemini_generic_error(self, mock_post):
        """Test _generate_gemini handles generic exceptions."""
        self._set_config_param('smart_product_image_generator.gemini_api_key', 'sk-mock-gemini')

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
        })
        mock_post.side_effect = Exception('Gemini network socket dropped')

        with self.assertRaises(UserError) as cm:
            wizard._generate_gemini('Prompt', 1, '1024x1024')
        self.assertIn('Google Gemini request failed', str(cm.exception))

    # ── action_generate_images ─────────────────────────────────────

    def test_action_generate_images_empty_prompt_raises(self):
        """Test action_generate_images raises UserError if prompt is blank."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'prompt': '',
        })
        with self.assertRaises(UserError):
            wizard.action_generate_images()

    def test_action_generate_images_unknown_provider_raises(self):
        """Test action_generate_images raises UserError for unknown provider."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'prompt': 'Valid prompt',
        })
        with patch.object(type(wizard), 'ai_provider', 'unsupported_provider'):
            with self.assertRaises(UserError):
                wizard.action_generate_images()

    def test_action_generate_images_success(self):
        """Test action_generate_images creates line records and sets state to generated."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'ai_provider': 'stability',
            'prompt': 'A high quality render',
            'num_variants': 2,
        })

        mock_images = [self.sample_b64_str, self.sample_b64_str]
        with patch.object(type(wizard), '_generate_stability', return_value=mock_images):
            action = wizard.action_generate_images()

        self.assertEqual(wizard.state, 'generated')
        self.assertEqual(len(wizard.generated_image_ids), 2)
        self.assertEqual(action.get('res_id'), wizard.id)

        # Generating again replaces old lines
        with patch.object(
            type(wizard), '_generate_stability', return_value=[self.sample_b64_str]
        ):
            wizard.action_generate_images()
        self.assertEqual(len(wizard.generated_image_ids), 1)

    def test_action_generate_images_generator_exception_handling(self):
        """Test action_generate_images propagates UserError or wraps general Exception."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'ai_provider': 'openai',
            'prompt': 'Prompt',
        })
        with patch.object(
            type(wizard), '_generate_openai', side_effect=UserError('OpenAI specific error')
        ):
            with self.assertRaises(UserError) as cm:
                wizard.action_generate_images()
            self.assertIn('OpenAI specific error', str(cm.exception))

        with patch.object(
            type(wizard), '_generate_openai', side_effect=RuntimeError('Fatal crash')
        ):
            with self.assertRaises(UserError) as cm:
                wizard.action_generate_images()
            self.assertIn('Image generation failed: Fatal crash', str(cm.exception))

    # ── action_apply_image ─────────────────────────────────────────

    def test_action_apply_image_invalid_line_raises(self):
        """Test action_apply_image raises UserError on non-existent or foreign line."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'prompt': 'Sample',
        })
        with self.assertRaises(UserError):
            wizard.action_apply_image(999999)

        foreign_wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'prompt': 'Foreign wizard',
        })
        foreign_line = self.env['product.ai.image.line'].create({
            'wizard_id': foreign_wizard.id,
            'image': self.sample_b64_str,
        })
        with self.assertRaises(UserError):
            wizard.action_apply_image(foreign_line.id)

    def test_action_apply_image_success(self):
        """Test action_apply_image updates product image, count, date, and posts chatter."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'prompt': 'Sample product image',
        })
        line = self.env['product.ai.image.line'].create({
            'wizard_id': wizard.id,
            'image': self.sample_b64_str,
            'provider_used': 'OpenAI DALL-E 3',
            'style_used': 'Professional Product Photo',
        })

        initial_count = self.product.ai_generation_count
        action = wizard.action_apply_image(line.id)

        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'reload')
        self.assertTrue(bool(self.product.image_1920))
        self.assertEqual(self.product.ai_generation_count, initial_count + 1)
        self.assertTrue(bool(self.product.ai_last_generated_date))

    def test_action_apply_image_requires_approval(self):
        """Test action_apply_image sets pending_approval when approval_required is True."""
        self._set_config_param('smart_product_image_generator.approval_required', 'True')
        try:
            product = self.env['product.template'].create({
                'name': 'Pending Approval Product',
            })
            wizard = self.env['smart.product.image.generator'].create({
                'product_id': product.id,
                'prompt': 'Approval prompt',
            })
            line = self.env['product.ai.image.line'].create({
                'wizard_id': wizard.id,
                'image': self.sample_b64_str,
                'provider_used': 'Stability AI',
                'style_used': 'Professional Product Photo',
            })

            action = wizard.action_apply_image(line.id)
            self.assertEqual(action.get('type'), 'ir.actions.act_window')
            self.assertEqual(wizard.state, 'pending_approval')
            self.assertFalse(product.image_1920)
            self.assertEqual(product.ai_generation_count, 0)

            log = self.env['ai.image.generation.log'].search([
                ('product_id', '=', product.id),
            ], order='id desc', limit=1)
            self.assertTrue(log)
            self.assertEqual(log.status, 'pending_approval')
            self.assertFalse(log.image_applied)
            self.assertTrue(bool(log.image_generated))
        finally:
            self._set_config_param('smart_product_image_generator.approval_required', 'False')

    # ── action_generate_more ───────────────────────────────────────

    def test_action_generate_more(self):
        """Test action_generate_more calls action_generate_images."""
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': self.product.id,
            'prompt': 'Sample',
        })
        with patch.object(
            type(wizard), 'action_generate_images', return_value={'type': 'test_action'}
        ) as mock_gen:
            res = wizard.action_generate_more()
            self.assertEqual(res.get('type'), 'test_action')
            mock_gen.assert_called_once()

    # ── action_bulk_generate ───────────────────────────────────────

    def test_action_bulk_generate_no_products_raises(self):
        """Test action_bulk_generate raises UserError when no products need processing."""
        product_with_image = self.env['product.template'].create({
            'name': 'Product With Image',
            'image_1920': self.sample_b64_str,
        })
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': product_with_image.id,
            'bulk_mode': True,
            'bulk_product_ids': [(6, 0, [product_with_image.id])],
            'bulk_skip_existing': True,
        })
        with self.assertRaises(UserError):
            wizard.action_bulk_generate()

    def test_action_bulk_generate_success_and_partial_failure(self):
        """Test action_bulk_generate processes products and reports progress accurately."""
        p1 = self.env['product.template'].create({'name': 'Bulk Item 1'})
        p2 = self.env['product.template'].create({'name': 'Bulk Item 2'})

        wizard = self.env['smart.product.image.generator'].create({
            'product_id': p1.id,
            'ai_provider': 'stability',
            'bulk_mode': True,
            'bulk_product_ids': [(6, 0, [p1.id, p2.id])],
            'bulk_skip_existing': True,
        })

        def mock_stability_generator(prompt, *unused_args, **unused_kwargs):
            if 'Bulk Item 2' in prompt:
                raise UserError(self.env._('Simulated API failure on Item 2'))
            return [self.sample_b64_str]

        with patch.object(
            type(wizard), '_generate_stability', side_effect=mock_stability_generator
        ):
            res = wizard.action_bulk_generate()

        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'display_notification')
        self.assertEqual(res['params']['type'], 'warning')
        self.assertIn('✓1 ✗1 ⊘0', wizard.bulk_progress_log)
        self.assertTrue(bool(p1.image_1920))
        self.assertEqual(p1.ai_generation_count, 1)
        self.assertFalse(p2.image_1920)

    def test_action_bulk_generate_requires_approval(self):
        """Test action_bulk_generate queues pending_approval logs when approval_required is True."""
        self._set_config_param('smart_product_image_generator.approval_required', 'True')
        try:
            p1 = self.env['product.template'].create({'name': 'Bulk Approval Item 1'})
            wizard = self.env['smart.product.image.generator'].create({
                'product_id': p1.id,
                'ai_provider': 'stability',
                'bulk_mode': True,
                'bulk_product_ids': [(6, 0, [p1.id])],
                'bulk_skip_existing': True,
            })

            with patch.object(
                type(wizard), '_generate_stability', return_value=[self.sample_b64_str]
            ):
                res = wizard.action_bulk_generate()

            self.assertEqual(res.get('tag'), 'display_notification')
            self.assertEqual(wizard.state, 'pending_approval')
            self.assertIn('⏳1 ✗0 ⊘0', wizard.bulk_progress_log)
            self.assertFalse(p1.image_1920)
            self.assertEqual(p1.ai_generation_count, 0)

            log = self.env['ai.image.generation.log'].search([
                ('product_id', '=', p1.id),
            ], order='id desc', limit=1)
            self.assertEqual(log.status, 'pending_approval')
            self.assertFalse(log.image_applied)
            self.assertTrue(bool(log.image_generated))
        finally:
            self._set_config_param('smart_product_image_generator.approval_required', 'False')

    def test_action_bulk_generate_unknown_provider_raises(self):
        """Test action_bulk_generate raises UserError for an unknown AI provider."""
        p1 = self.env['product.template'].create({'name': 'Bulk Unknown Provider'})
        wizard = self.env['smart.product.image.generator'].create({
            'product_id': p1.id,
            'bulk_mode': True,
            'bulk_product_ids': [(6, 0, [p1.id])],
        })
        with patch.object(type(wizard), 'ai_provider', 'unknown_provider'):
            with self.assertRaises(UserError):
                wizard.action_bulk_generate()
