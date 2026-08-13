# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Prasudhi A(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'product_image_suggestion')
class TestProductImageSuggestion(TransactionCase):
    """Test cases for the ProductImageSuggestion transient model
    (product.image.suggestion)."""

    def setUp(self):
        super().setUp()
        # Create a minimal product template to use as the related product
        self.product = self.env['product.template'].create({
            'name': 'Test Product',
        })
        # A small 1x1 red PNG encoded in base64 to use as a dummy image
        self.dummy_image = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )

    def test_create_suggestion(self):
        """Test that a product.image.suggestion record can be created with
        an image binary and a related product template."""
        suggestion = self.env['product.image.suggestion'].create({
            'image': self.dummy_image,
            'product_tmpl_id': self.product.id,
        })
        self.assertTrue(suggestion.id,
                        "Suggestion record should have a valid ID after "
                        "creation.")
        self.assertEqual(suggestion.product_tmpl_id.id, self.product.id,
                         "The related product should match the one provided "
                         "during creation.")
        self.assertEqual(suggestion.image, self.dummy_image,
                         "The stored image binary should match the input.")

    def test_action_set_image_sets_product_image(self):
        """Test that action_set_image() copies the suggestion image to the
        product template's image_1920 field."""
        suggestion = self.env['product.image.suggestion'].create({
            'image': self.dummy_image,
            'product_tmpl_id': self.product.id,
        })
        suggestion.action_set_image()
        self.assertEqual(
            self.product.image_1920, self.dummy_image,
            "product_tmpl_id.image_1920 should be updated to the suggestion "
            "image after calling action_set_image()."
        )

    def test_action_set_image_returns_reload_action(self):
        """Test that action_set_image() returns the expected client reload
        action dictionary."""
        suggestion = self.env['product.image.suggestion'].create({
            'image': self.dummy_image,
            'product_tmpl_id': self.product.id,
        })
        result = suggestion.action_set_image()
        self.assertIsInstance(result, dict,
                              "action_set_image() should return a dict.")
        self.assertEqual(result.get('type'), 'ir.actions.client',
                         "Action type should be 'ir.actions.client'.")
        self.assertEqual(result.get('tag'), 'reload',
                         "Action tag should be 'reload'.")

    def test_action_set_image_no_image(self):
        """Test that when the suggestion has no image, the product's
        image_1920 field is not changed."""
        original_image = self.dummy_image
        self.product.image_1920 = original_image

        suggestion = self.env['product.image.suggestion'].create({
            'image': False,
            'product_tmpl_id': self.product.id,
        })
        suggestion.action_set_image()
        self.assertEqual(
            self.product.image_1920, original_image,
            "When suggestion has no image, product image_1920 should remain "
            "unchanged."
        )

    def test_suggestion_without_product(self):
        """Test that a suggestion record can be created without a related
        product (product_tmpl_id is optional)."""
        suggestion = self.env['product.image.suggestion'].create({
            'image': self.dummy_image,
        })
        self.assertFalse(suggestion.product_tmpl_id,
                         "product_tmpl_id should be empty when not provided.")

    def test_multiple_suggestions_for_same_product(self):
        """Test that multiple suggestion records can link to the same product
        template independently."""
        suggestion1 = self.env['product.image.suggestion'].create({
            'image': self.dummy_image,
            'product_tmpl_id': self.product.id,
        })
        suggestion2 = self.env['product.image.suggestion'].create({
            'image': self.dummy_image,
            'product_tmpl_id': self.product.id,
        })
        self.assertNotEqual(suggestion1.id, suggestion2.id,
                            "Each suggestion should be a distinct record.")
        suggestions = self.env['product.image.suggestion'].search(
            [('product_tmpl_id', '=', self.product.id)]
        )
        self.assertGreaterEqual(len(suggestions), 2,
                                "Both suggestions should be findable by "
                                "product template.")
