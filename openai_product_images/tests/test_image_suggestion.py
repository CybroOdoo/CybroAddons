# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import base64
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestImageSuggestion(TransactionCase):
    """Test cases for the image.suggestion wizard."""

    def setUp(self):
        super(TestImageSuggestion, self).setUp()
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test Product C',
            'list_price': 50.0,
        })
        self.wizard = self.env['image.suggestion'].create({
            'image_prompt': 'A high quality image of Test Product C',
            'product_tmpl_id': self.product_tmpl.id,
            'num_image': 2,
            'size_image': '1024x1024',
            'quality': 'standard',
        })

    def test_action_generate_images_no_api_key(self):
        """Test action_generate_images raises UserError if OpenAI API key is missing."""
        self.env['ir.config_parameter'].sudo().set_param('openai_api_key', False)

        with self.assertRaises(UserError) as exc:
            self.wizard.action_generate_images()
        self.assertIn("OpenAI API key is not configured", str(exc.exception))

    @patch('odoo.addons.openai_product_images.wizard.image_suggestion.urlopen')
    @patch('odoo.addons.openai_product_images.wizard.image_suggestion.OpenAI')
    def test_action_generate_images_success(self, mock_openai_class, mock_urlopen):
        """Test action_generate_images creates suggestions and updates product image when API key is set."""
        self.env['ir.config_parameter'].sudo().set_param('openai_api_key', 'dummy_key_123')

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_data = MagicMock()
        mock_data.url = 'http://example.com/generated_image.png'
        mock_response.data = [mock_data]
        mock_client.images.generate.return_value = mock_response

        mock_image_bytes = base64.b64decode(
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        )
        mock_urlopen.return_value.read.return_value = mock_image_bytes

        action = self.wizard.action_generate_images()

        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})

        mock_openai_class.assert_called_once_with(api_key='dummy_key_123')
        self.assertEqual(mock_client.images.generate.call_count, 2)
        mock_client.images.generate.assert_called_with(
            model="dall-e-3",
            prompt='A high quality image of Test Product C',
            size='1024x1024',
            quality='standard',
            n=1
        )

        suggestions = self.env['dalle.image.suggestion'].search([
            ('product_tmpl_id', '=', self.product_tmpl.id)
        ])
        self.assertEqual(len(suggestions), 2)

        expected_b64 = base64.b64encode(mock_image_bytes)
        self.assertEqual(self.product_tmpl.image_1920, expected_b64)
