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
from odoo.tests.common import TransactionCase


class TestDalleImageSuggestion(TransactionCase):
    """Test cases for the dalle.image.suggestion model."""

    def setUp(self):
        super(TestDalleImageSuggestion, self).setUp()
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test Product A',
            'list_price': 100.0,
        })
        self.sample_image = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        self.dalle_image = self.env['dalle.image.suggestion'].create({
            'product_image': self.sample_image,
            'product_tmpl_id': self.product_tmpl.id,
        })

    def test_action_make_as_product_image(self):
        """Test action_make_as_product_image sets image on product template."""
        self.assertFalse(self.product_tmpl.image_1920)

        action = self.dalle_image.action_make_as_product_image()

        self.assertEqual(self.product_tmpl.image_1920, self.sample_image)

        self.assertEqual(action['res_model'], 'product.template')
        self.assertEqual(action['res_id'], self.product_tmpl.id)
        self.assertEqual(action['target'], 'current')
