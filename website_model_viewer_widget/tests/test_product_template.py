# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Tests for the 3D model validation on product templates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env['product.template']

    def test_valid_glb_model_is_allowed(self):
        """Test valid base64 glb data is accepted."""
        encoded = base64.b64encode(b'glTF valid binary data').decode('ascii')
        product = self.ProductTemplate.create({
            'name': 'Test 3D Product',
            'model_3d': encoded,
        })
        self.assertTrue(product.model_3d)

    def test_update_valid_glb_model(self):
        """Test updating product with another valid glb model."""
        product = self.ProductTemplate.create({
            'name': 'Test Update 3D Product',
            'model_3d': base64.b64encode(b'glTF initial').decode('ascii'),
        })
        self.assertTrue(product.model_3d)
        new_encoded = base64.b64encode(b'glTF updated').decode('ascii')
        product.write({'model_3d': new_encoded})
        self.assertTrue(product.model_3d)

    def test_empty_model_is_allowed(self):
        """Test product without 3D model can be created."""
        product = self.ProductTemplate.create({
            'name': 'Test Product Without 3D Model',
        })
        self.assertFalse(product.model_3d)

    def test_invalid_model_raises_validation_error(self):
        """Test invalid 3D model raises ValidationError."""
        encoded = base64.b64encode(b'invalid binary data').decode('ascii')
        with self.assertRaises(ValidationError):
            self.ProductTemplate.create({
                'name': 'Test Invalid 3D Product',
                'model_3d': encoded,
            })

    def test_invalid_base64_content_raises_validation_error(self):
        """Test non-glTF payload raises ValidationError."""
        encoded = base64.b64encode(b'corrupted data').decode('ascii')
        with self.assertRaises(ValidationError):
            self.ProductTemplate.create({
                'name': 'Test Corrupt Product',
                'model_3d': encoded,
            })
