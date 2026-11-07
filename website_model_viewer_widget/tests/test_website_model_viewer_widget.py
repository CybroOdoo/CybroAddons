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
from unittest.mock import MagicMock, patch

from odoo.http import Response
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.website_model_viewer_widget.controllers import (
    website_model_viewer_widget,
)


@tagged('post_install', '-at_install')
class TestProductModelController(TransactionCase):
    """Tests for the product 3D model HTTP/JSON controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = website_model_viewer_widget.ProductModel()
        cls.valid_glb = base64.b64encode(b'glTF test binary').decode('ascii')
        cls.product_with_model = cls.env['product.template'].create({
            'name': 'Product With 3D',
            'model_3d': cls.valid_glb,
        })
        cls.product_without_model = cls.env['product.template'].create({
            'name': 'Product Without 3D',
        })

    def _setup_mock_request(self):
        req = MagicMock()
        req.env = self.env
        req.make_response.side_effect = (
            lambda data, headers=None: Response(data, headers=headers)
        )
        req.not_found.side_effect = lambda: Response(status=404)
        return req

    def test_get_product_3d_model_success(self):
        """Test returning 3D model data for product with 3D model."""
        req = self._setup_mock_request()
        with patch.object(website_model_viewer_widget, 'request', req):
            res = self.controller.get_product_3d_model(
                str(self.product_with_model.id),
            )
        self.assertTrue(res.get('3D_model'))

    def test_get_product_3d_model_without_model(self):
        """Test returning False for product without 3D model."""
        req = self._setup_mock_request()
        with patch.object(website_model_viewer_widget, 'request', req):
            res = self.controller.get_product_3d_model(
                str(self.product_without_model.id),
            )
        self.assertEqual(res, {'3D_model': False})

    def test_get_product_3d_model_invalid_id(self):
        """Test handling empty or invalid product_id."""
        req = self._setup_mock_request()
        with patch.object(website_model_viewer_widget, 'request', req):
            res_none = self.controller.get_product_3d_model(None)
            res_invalid = self.controller.get_product_3d_model("abc")
        self.assertEqual(res_none, {'3D_model': False})
        self.assertEqual(res_invalid, {'3D_model': False})

    def test_get_product_3d_model_file_success(self):
        """Test returning raw 3D model file with proper headers."""
        req = self._setup_mock_request()
        with patch.object(website_model_viewer_widget, 'request', req):
            res = self.controller.get_product_3d_model_file(
                self.product_with_model.id,
            )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data.startswith(b'glTF'))
        self.assertEqual(
            res.headers.get('Content-Type'), 'model/gltf-binary',
        )

    def test_get_product_3d_model_file_not_found(self):
        """Test returning 404 for product without 3D model or non-existent."""
        req = self._setup_mock_request()
        with patch.object(website_model_viewer_widget, 'request', req):
            res_no_model = self.controller.get_product_3d_model_file(
                self.product_without_model.id,
            )
            res_non_existent = self.controller.get_product_3d_model_file(
                999999,
            )
        self.assertEqual(res_no_model.status_code, 404)
        self.assertEqual(res_non_existent.status_code, 404)
