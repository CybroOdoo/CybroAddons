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

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.click_and_collect_pos.controllers.click_and_collect_pos import (
    ClickAndCollectPos,
)


@tagged('post_install', '-at_install')
class TestClickAndCollectPos(TransactionCase):
    """Unit tests for ClickAndCollectPos controller in click_and_collect_pos."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for controller tests."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer Controller',
            'email': 'customer_ctrl@test.com',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Controller Test POS Store',
            'company_id': cls.company.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Controller Product',
            'list_price': 80.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        cls.order_line = cls.order.order_line[0]
        cls.controller = ClickAndCollectPos()

    def test_update_click_and_collect(self):
        """Test update_click_and_collect controller endpoint logic."""
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.cart = self.order

        # 1. Successful update of is_click_and_collect and pos_config_id
        with patch('odoo.addons.click_and_collect_pos.controllers.click_and_collect_pos.request', mock_request):
            res = self.controller.update_click_and_collect(
                line_id=self.order_line.id,
                is_click_and_collect=True,
                pos_config_id=self.pos_config.id,
            )
            self.assertEqual(res, {'status': 'success'})
            self.assertTrue(self.order_line.is_click_and_collect)
            self.assertEqual(self.order_line.pos_config_id.id, self.pos_config.id)

        # 2. Unchecking click and collect and resetting store
        with patch('odoo.addons.click_and_collect_pos.controllers.click_and_collect_pos.request', mock_request):
            res = self.controller.update_click_and_collect(
                line_id=self.order_line.id,
                is_click_and_collect=False,
                pos_config_id='select',
            )
            self.assertEqual(res, {'status': 'success'})
            self.assertFalse(self.order_line.is_click_and_collect)
            self.assertFalse(self.order_line.pos_config_id)

        # 3. Order line not found in cart
        with patch('odoo.addons.click_and_collect_pos.controllers.click_and_collect_pos.request', mock_request):
            res = self.controller.update_click_and_collect(
                line_id=999999,
                is_click_and_collect=True,
            )
            self.assertEqual(res.get('status'), 'error')
            self.assertIn('not found', res.get('message', ''))

        # 4. No active order
        mock_empty_request = MagicMock()
        mock_empty_request.cart = None
        mock_empty_env = MagicMock()
        mock_empty_env.website = None
        mock_empty_request.env = mock_empty_env
        with patch('odoo.addons.click_and_collect_pos.controllers.click_and_collect_pos.request', mock_empty_request):
            res = self.controller.update_click_and_collect(
                line_id=self.order_line.id,
                is_click_and_collect=True,
            )
            self.assertEqual(res.get('status'), 'error')
            self.assertIn('No active order', res.get('message', ''))
