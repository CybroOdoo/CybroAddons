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
import base64

from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

PARAM = 'sale_product_image.is_show_product_image_in_sale_report'
# 1x1 transparent PNG
IMAGE = BinaryBytes(base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA'
    '60e6kgAAAABJRU5ErkJggg=='))


@tagged('post_install', '-at_install')
class TestSaleProductImage(TransactionCase):
    """Tests for product images in sale order lines and the sale report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Image Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Image Product',
            'image_1920': IMAGE,
        })
        cls.product_no_image = cls.env['product.product'].create({
            'name': 'Plain Product',
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {'product_id': cls.product.id, 'product_uom_qty': 1}),
                (0, 0, {'product_id': cls.product_no_image.id,
                        'product_uom_qty': 1}),
            ],
        })

    def _set_show_image(self, value):
        settings = self.env['res.config.settings'].create({
            'is_show_product_image_in_sale_report': value,
        })
        settings.execute()
        self.order.invalidate_recordset(['is_image_true'])

    def _render_report(self):
        html, _report_type = self.env['ir.actions.report']._render_qweb_html(
            'sale.action_report_saleorder', self.order.ids)
        return html.decode() if isinstance(html, bytes) else str(html)

    def test_setting_stored_in_config_parameter(self):
        """The settings checkbox writes and reads the config parameter."""
        icp = self.env['ir.config_parameter'].sudo()
        self._set_show_image(True)
        self.assertTrue(icp.get_bool(PARAM))
        self.assertTrue(self.env['res.config.settings'].create(
            {}).is_show_product_image_in_sale_report)
        self._set_show_image(False)
        self.assertFalse(icp.get_bool(PARAM))

    def test_is_image_true_follows_setting(self):
        """The order flag mirrors the setting."""
        self._set_show_image(True)
        self.assertTrue(self.order.is_image_true)
        self._set_show_image(False)
        self.assertFalse(self.order.is_image_true)

    def test_order_line_image(self):
        """Order lines expose the product image."""
        line_image, line_plain = self.order.order_line
        self.assertTrue(line_image.order_line_image)
        self.assertEqual(bytes(line_image.order_line_image),
                         bytes(self.product.image_1920))
        self.assertFalse(line_plain.order_line_image)

    def test_report_with_images(self):
        """The report shows the image column when the setting is enabled."""
        self._set_show_image(True)
        html = self._render_report()
        self.assertIn('th_product_image', html)
        self.assertIn('td_product_image', html)
        self.assertIn('alt="Product Image"', html)

    def test_report_without_images(self):
        """The report hides the image column when the setting is disabled."""
        self._set_show_image(False)
        html = self._render_report()
        self.assertNotIn('th_product_image', html)
        self.assertNotIn('td_product_image', html)
