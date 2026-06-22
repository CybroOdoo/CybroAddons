# -*- coding: utf-8 -*-

from unittest.mock import MagicMock, patch

from odoo.tests import common

from odoo.addons.website_model_viewer_widget.controllers import (
    website_model_viewer_widget,
)


class TestProductModelController(common.TransactionCase):
    """Tests for the product 3D model JSON controller."""

    def test_get_product_3d_model_returns_model_data(self):
        product = MagicMock()
        product.model_3d = b'Z2xURiBtb2RlbA=='
        request = self._mock_request(product)

        with patch.object(website_model_viewer_widget, 'request', request):
            result = website_model_viewer_widget.ProductModel().get_product_3d_model('12')

        request.env['product.template'].sudo().browse.assert_called_once_with(12)
        self.assertEqual(result, {'3D_model': product.model_3d})

    def test_get_product_3d_model_returns_false_without_model_data(self):
        product = MagicMock()
        product.model_3d = False
        request = self._mock_request(product)

        with patch.object(website_model_viewer_widget, 'request', request):
            result = website_model_viewer_widget.ProductModel().get_product_3d_model('13')

        request.env['product.template'].sudo().browse.assert_called_once_with(13)
        self.assertEqual(result, {'3D_model': False})

    def _mock_request(self, product):
        product_model = MagicMock()
        product_model.sudo.return_value.browse.return_value = product

        request = MagicMock()
        request.env.__getitem__.return_value = product_model
        return request
