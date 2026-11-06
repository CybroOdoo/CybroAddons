# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64

from odoo.tests.common import TransactionCase, tagged

PNG = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff'
    b'\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82'
).decode()  # Odoo 20 binary fields reject raw bytes; pass a base64 str


@tagged('post_install', '-at_install')
class TestMediaImage(TransactionCase):
    """Test creating product media images from OpenAI suggestions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env['product.template'].create({
            'name': 'Media Test Product',
        })
        cls.suggestion_model = cls.env['openai.image.suggestion']

    def _count_images(self):
        return self.env['product.image'].search_count(
            [('product_tmpl_id', '=', self.template.id)])

    def test_make_as_media_image_creates_image(self):
        suggestion = self.suggestion_model.create({
            'product_tmpl_id': self.template.id,
            'product_image': PNG,
        })
        before = self._count_images()
        result = suggestion.action_make_as_media_image()
        self.assertEqual(self._count_images(), before + 1)
        self.assertEqual(result['params']['type'], 'success')
        media = self.env['product.image'].search(
            [('product_tmpl_id', '=', self.template.id)])
        self.assertEqual(media.name, 'Media Test Product')
        self.assertTrue(media.image_1920)

    def test_make_as_media_image_skips_without_image(self):
        suggestion = self.suggestion_model.create({
            'product_tmpl_id': self.template.id,
        })
        before = self._count_images()
        result = suggestion.action_make_as_media_image()
        self.assertEqual(self._count_images(), before)
        self.assertEqual(result['params']['type'], 'warning')

    def test_make_as_media_image_skips_without_product(self):
        # product_tmpl_id is NOT NULL in the DB, so use an in-memory record
        suggestion = self.suggestion_model.new({'product_image': PNG})
        before = self._count_images()
        result = suggestion.action_make_as_media_image()
        self.assertEqual(self._count_images(), before)
        self.assertEqual(result['params']['type'], 'warning')
