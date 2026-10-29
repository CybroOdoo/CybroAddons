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
from odoo.addons.product_import.models import product_image_url_mixin
from odoo.exceptions import UserError
from odoo.tests import tagged
from .common import MISSING_PATH, NOT_FOUND_URL, OK_URL, ProductImportCommon


@tagged('post_install', '-at_install')
class TestImageSources(ProductImportCommon):
    """ Loading images from web URLs and local paths """

    def setUp(self):
        super().setUp()
        self.Mixin = self.env['product.image.url.mixin']

    def test_fetch_image_success(self):
        image, reason = self.Mixin._get_image_from_source(' %s ' % OK_URL)
        self.assertEqual(image, self.png_b64)
        self.assertIsNone(reason)
        self.assertEqual(self.http.request.call_args.args, ('GET', OK_URL))
        self.assertIn('User-Agent', self.http.request.call_args.kwargs['headers'])

    def test_fetch_image_without_content_type(self):
        self.http.request.side_effect = None
        self.http.request.return_value = MagicMock(
            status=200, headers={}, data=self.png_bytes)
        self.assertEqual(self.Mixin._fetch_image_b64(OK_URL),
                         (self.png_b64, None))

    def test_fetch_image_connection_error(self):
        self.http.request.side_effect = OSError('network down')
        self.assertEqual(self.Mixin._fetch_image_b64(OK_URL),
                         (False, 'connection error: network down'))

    def test_fetch_image_http_error(self):
        self.assertEqual(self.Mixin._fetch_image_b64(NOT_FOUND_URL),
                         (False, 'HTTP 404'))

    def test_fetch_image_wrong_content_type(self):
        self.http.request.side_effect = None
        self.http.request.return_value = MagicMock(
            status=200, headers={'Content-Type': 'text/html'}, data=b'<html>')
        image, reason = self.Mixin._fetch_image_b64(OK_URL)
        self.assertFalse(image)
        self.assertIn("unexpected content-type 'text/html'", reason)

    def test_read_local_image_success(self):
        image, reason = self.Mixin._get_image_from_source(self.make_image_file())
        self.assertEqual(image, self.png_b64)
        self.assertIsNone(reason)

    def test_read_local_image_missing(self):
        self.assertEqual(self.Mixin._read_local_image_b64(MISSING_PATH),
                         (False, 'file does not exist on the Odoo server'))

    def test_read_local_image_unreadable(self):
        path = self.make_image_file()
        with patch.object(product_image_url_mixin, 'open', create=True,
                          side_effect=PermissionError('access denied')):
            self.assertEqual(self.Mixin._read_local_image_b64(path),
                             (False, 'access denied'))

    def test_relative_path_rejected(self):
        self.assertEqual(self.Mixin._get_image_from_source('images/a.png'),
                         (False, 'not a web URL or an absolute file path'))


@tagged('post_install', '-at_install')
class TestProductImageUrl(ProductImportCommon):
    """ The 'Image URL' field on product templates and variants """

    def _check_create_from_url(self, model):
        record = self.env[model].create({
            'name': 'URL Image Product',
            'image_url': OK_URL,
        })
        self.assertTrue(record.image_1920)
        self.assertEqual(record.image_url, OK_URL)

    def _check_write_from_local_path(self, model):
        record = self.env[model].create({'name': 'Local Image Product'})
        self.assertFalse(record.image_1920)
        record.write({'image_url': self.make_image_file()})
        self.assertTrue(record.image_1920)

    def _check_load_error(self, model, source):
        with self.assertRaisesRegex(UserError, 'Could not load the image from'):
            self.env[model].create({'name': 'Broken Image', 'image_url': source})

    def _check_other_writes_keep_image(self, model):
        record = self.env[model].create({
            'name': 'Image Kept Product',
            'image_1920': self.png_b64,
        })
        record.write({'list_price': 5.0, 'image_url': False})
        self.assertTrue(record.image_1920)
        self.http.request.assert_not_called()

    def test_template_create_from_url(self):
        self._check_create_from_url('product.template')

    def test_template_write_from_local_path(self):
        self._check_write_from_local_path('product.template')

    def test_template_url_error(self):
        self._check_load_error('product.template', NOT_FOUND_URL)

    def test_template_local_path_error(self):
        self._check_load_error('product.template', MISSING_PATH)

    def test_template_other_writes_keep_image(self):
        self._check_other_writes_keep_image('product.template')

    def test_variant_create_from_url(self):
        self._check_create_from_url('product.product')

    def test_variant_write_from_local_path(self):
        self._check_write_from_local_path('product.product')

    def test_variant_url_error(self):
        self._check_load_error('product.product', NOT_FOUND_URL)

    def test_variant_local_path_error(self):
        self._check_load_error('product.product', MISSING_PATH)

    def test_variant_other_writes_keep_image(self):
        self._check_other_writes_keep_image('product.product')
