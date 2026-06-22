# -*- coding: utf-8 -*-

import base64

from odoo.exceptions import ValidationError
from odoo.tests import common


class TestProductTemplate(common.TransactionCase):
    """Tests for the 3D model validation on product templates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env['product.template']

    def test_valid_glb_model_is_allowed(self):
        product = self.ProductTemplate.create({
            'name': 'Test 3D Product',
            'model_3d': base64.b64encode(b'glTF valid binary data'),
        })

        self.assertTrue(product.model_3d)

    def test_empty_model_is_allowed(self):
        product = self.ProductTemplate.create({
            'name': 'Test Product Without 3D Model',
        })

        self.assertFalse(product.model_3d)

    def test_invalid_model_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.ProductTemplate.create({
                'name': 'Test Invalid 3D Product',
                'model_3d': base64.b64encode(b'invalid binary data'),
            })
