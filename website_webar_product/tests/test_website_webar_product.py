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

from odoo.exceptions import UserError
from odoo.tests import common, tagged

from odoo.addons.website_webar_product.controllers.website_webar_product import (
    ProductModel,
)


@tagged('post_install', '-at_install')
class TestWebsiteWebarProduct(common.TransactionCase):
    """Test suite for Website WebAR Product Viewer model and controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = ProductModel()
        cls.product = cls.env['product.template'].create({
            'name': 'AR Test Chair',
            'list_price': 150.0,
            'is_published': True,
            'enable_ar_images': True,
            'ar_image_type': 'url',
            'ar_url': 'https://example.com/chair.glb',
            'ar_scale': 'auto',
            'auto_rotate': True,
            'ar_placement': 'floor',
        })

    def test_create_product_without_ar(self):
        """Test creating a regular product without AR or filename."""
        standard_product = self.env['product.template'].create({
            'name': 'Standard Desk',
            'list_price': 80.0,
        })
        self.assertTrue(standard_product.id)
        self.assertFalse(standard_product.enable_ar_images)
        self.assertFalse(standard_product.filename)

    def test_configure_ar_url(self):
        """Test AR configuration using external model URL."""
        self.assertEqual(self.product.ar_image_type, 'url')
        self.assertEqual(self.product.ar_url, 'https://example.com/chair.glb')
        self.assertTrue(self.product.auto_rotate)

    def test_configure_ar_upload_valid(self):
        """Test uploading a valid GLB/GLTF model file using base64 string."""
        model_data = base64.b64encode(b'binary 3d glb content').decode('ascii')
        product_upload = self.env['product.template'].create({
            'name': 'Uploaded AR Table',
            'enable_ar_images': True,
            'ar_image_type': 'upload',
            'filename': 'table.glb',
            'model_ar': model_data,
        })
        self.assertTrue(product_upload.model_ar)
        self.assertEqual(product_upload.filename, 'table.glb')

    def test_configure_ar_upload_invalid_extension(self):
        """Test that non-GLB/GLTF extensions raise UserError."""
        invalid_data = base64.b64encode(b'invalid content').decode('ascii')
        with self.assertRaises(UserError):
            self.env['product.template'].create({
                'name': 'Invalid File Product',
                'enable_ar_images': True,
                'ar_image_type': 'upload',
                'filename': 'model.exe',
                'model_ar': invalid_data,
            })

    def test_controller_ar_image_published(self):
        """Test controller returns AR model data for published product."""
        res = self.controller.get_product_ar_model(
            self.product.id, env=self.env
        )
        self.assertEqual(res.get('type'), 'url')
        self.assertEqual(res.get('ar_url'), 'https://example.com/chair.glb')
        self.assertEqual(res.get('ar_scale'), 'auto')
        self.assertTrue(res.get('auto_rotate'))

    def test_controller_ar_image_disabled(self):
        """Test controller returns empty dict when AR is disabled."""
        self.product.enable_ar_images = False
        res = self.controller.get_product_ar_model(
            self.product.id, env=self.env
        )
        self.assertEqual(res, {})

    def test_controller_ar_image_unpublished_secured(self):
        """Test controller protects unpublished product from public access."""
        self.product.is_published = False
        public_user = self.env.ref('base.public_user')
        public_env = self.env(user=public_user)
        res = self.controller.get_product_ar_model(
            self.product.id, env=public_env
        )
        self.assertEqual(res, {})
