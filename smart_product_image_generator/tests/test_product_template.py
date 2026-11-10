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

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes

from ..models.product_template import extract_raw_bytes


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for AI image generator features in product.template."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Ergonomic Office Chair',
            'list_price': 150.0,
        })
        cls.product_2 = cls.env['product.template'].create({
            'name': 'Wireless Mechanical Keyboard',
            'list_price': 85.0,
        })

    def test_default_fields(self):
        """Test default values of AI fields on product template."""
        self.assertEqual(self.product.ai_generation_count, 0)
        self.assertFalse(self.product.ai_last_generated_date)

    def test_action_open_ai_image_wizard(self):
        """Test action_open_ai_image_wizard returns the expected wizard action dict."""
        action = self.product.action_open_ai_image_wizard()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('name'), 'Generate Product Image with AI')
        self.assertEqual(action.get('res_model'), 'smart.product.image.generator')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context'), {
            'default_product_id': self.product.id,
        })

    def test_action_open_ai_image_wizard_multiple_records_raises(self):
        """Test action_open_ai_image_wizard raises ValueError if called on multi-recordset."""
        products = self.product | self.product_2
        with self.assertRaises(ValueError):
            products.action_open_ai_image_wizard()

    def test_action_bulk_generate_ai_images_with_active_ids(self):
        """Test action_bulk_generate_ai_images returns action configured with active_ids."""
        active_ids = [self.product.id, self.product_2.id]
        action = self.product.with_context(active_ids=active_ids).action_bulk_generate_ai_images()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('name'), 'Bulk Generate AI Images')
        self.assertEqual(action.get('res_model'), 'smart.product.image.generator')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('target'), 'new')

        context = action.get('context', {})
        self.assertTrue(context.get('default_bulk_mode'))
        self.assertEqual(context.get('default_bulk_product_ids'), [(6, 0, active_ids)])
        self.assertEqual(context.get('default_product_id'), self.product.id)

    def test_action_bulk_generate_ai_images_without_active_ids(self):
        """Test action_bulk_generate_ai_images returns False when no active_ids in context."""
        action = self.product.with_context(active_ids=[]).action_bulk_generate_ai_images()
        self.assertFalse(action)

        action_no_context = self.product.with_context().action_bulk_generate_ai_images()
        self.assertFalse(action_no_context)

    def test_extract_raw_bytes_helper(self):
        """Test extract_raw_bytes handles BinaryValue, bytes, strings, and empty values."""
        self.assertEqual(extract_raw_bytes(None), b'')
        self.assertEqual(extract_raw_bytes(''), b'')

        binary_val = BinaryBytes(b'binary-value-bytes')
        self.assertEqual(extract_raw_bytes(binary_val), b'binary-value-bytes')

        mock_obj = MagicMock()
        mock_obj.content = b'obj-content'
        self.assertEqual(extract_raw_bytes(mock_obj), b'obj-content')

        png_bytes = b'\x89PNG\r\n\x1a\n'
        self.assertEqual(extract_raw_bytes(png_bytes), png_bytes)

        raw = b'sample-payload'
        self.assertEqual(extract_raw_bytes(base64.b64encode(raw)), raw)
        self.assertEqual(extract_raw_bytes(base64.b64encode(raw).decode('ascii')), raw)
        self.assertEqual(extract_raw_bytes('not-base64!'), b'not-base64!')

    def test_apply_ai_generated_image_single_and_bulk(self):
        """Test _apply_ai_generated_image updates product image, metadata, and chatter."""
        sample_b64 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
            '+A8AAQUBAScY42YAAAAASUVORK5CYII='
        )
        product = self.env['product.template'].create({
            'name': 'Apply Image Target',
            'list_price': 120.0,
        })

        product._apply_ai_generated_image(
            image_data=sample_b64,
            provider_label='OpenAI DALL-E 3',
            style_label='Professional Product Photo',
            size='1024x1024',
            is_bulk=False,
        )
        self.assertTrue(bool(product.image_1920))
        self.assertEqual(product.ai_generation_count, 1)
        self.assertTrue(bool(product.ai_last_generated_date))
        self.assertIn('Generation #: 1', product.message_ids[0].body)

        product._apply_ai_generated_image(
            image_data=sample_b64,
            provider_label='stability',
            size='1792x1024',
            is_bulk=True,
        )
        self.assertEqual(product.ai_generation_count, 2)
        self.assertIn('(Bulk)', product.message_ids[0].body)

    def test_apply_ai_generated_image_chatter_failure_non_critical(self):
        """Test _apply_ai_generated_image still succeeds when message_post fails."""
        sample_b64 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
            '+A8AAQUBAScY42YAAAAASUVORK5CYII='
        )
        product = self.env['product.template'].create({'name': 'Chatter Error Product'})
        with patch.object(
            type(product), 'message_post', side_effect=RuntimeError('Mail server down')
        ):
            product._apply_ai_generated_image(
                image_data=sample_b64,
                provider_label='Gemini',
                style_label='Minimal',
                size='1024x1024',
            )
        self.assertTrue(bool(product.image_1920))
        self.assertEqual(product.ai_generation_count, 1)
