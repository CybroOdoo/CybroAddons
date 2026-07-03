# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase


class TestDalleImageSuggestionMedia(TransactionCase):
    """Test cases for eCommerce Product Media image generation suggestions."""

    def setUp(self):
        super(TestDalleImageSuggestionMedia, self).setUp()
        self.product_tmpl = self.env['product.template'].create({
            'name': 'eCommerce Test Product',
            'list_price': 150.0,
        })
        self.sample_image = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        self.dalle_image = self.env['dalle.image.suggestion'].create({
            'product_image': self.sample_image,
            'product_tmpl_id': self.product_tmpl.id,
        })

    def test_action_make_as_media_image(self):
        """Test action_make_as_media_image creates a product.image record."""
        # Ensure no product media images exist initially for this template
        initial_media = self.env['product.image'].search([
            ('product_tmpl_id', '=', self.product_tmpl.id)
        ])
        self.assertFalse(initial_media)

        # Call action to make as media image
        action = self.dalle_image.action_make_as_media_image()

        # Check notification action details
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

        # Verify a product.image record was created for the product template
        media = self.env['product.image'].search([
            ('product_tmpl_id', '=', self.product_tmpl.id)
        ])
        self.assertEqual(len(media), 1)
        self.assertEqual(media.name, 'eCommerce Test Product')
        self.assertEqual(media.image_1920, self.sample_image)
