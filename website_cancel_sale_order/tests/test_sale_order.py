# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Henna Mehjabin(<https://www.cybrosys.com>)
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
##############################################################################
import json
import logging

from odoo.tests.common import HttpCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestWebsiteCancelOrder(HttpCase):
    """Test cases for website cancel sale order controller."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        _logger.info("Setting up Website Cancel Order test data")

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })

    def test_cancel_sale_order_controller(self):
        """Test sale order cancellation through controller."""
        _logger.info("Starting test_cancel_sale_order_controller")

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })]
        })

        sale_order.action_confirm()

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'sale_order_id': sale_order.id,
                'reason': 'Customer requested cancellation',
            },
            'id': 1,
        }

        self.url_open(
            '/cancel/reason/edit',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        sale_order.invalidate_recordset()

        self.assertEqual(sale_order.state, 'cancel')
        self.assertTrue(sale_order.is_cancel)
        self.assertEqual(
            sale_order.cancellation_reason,
            'Customer requested cancellation'
        )

        _logger.info("Completed test_cancel_sale_order_controller")