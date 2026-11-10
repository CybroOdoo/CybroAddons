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
"""Test suite for website sale payment validation with table reservation."""
from datetime import date
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.table_reservation_on_website.controllers.table_reservation_on_website_website_sale import WebsiteSalePayment


@tagged('post_install', '-at_install')
class TestWebsiteSaleController(TransactionCase):
    """Test shop_payment_validate creates reservation upon payment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteSalePayment()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website Shopper',
            'email': 'shopper@example.com',
        })
        cls.floor = cls.env['restaurant.floor'].create({'name': 'Website Sale Floor'})
        cls.table = cls.env['restaurant.table'].create({
            'table_number': 8,
            'floor_id': cls.floor.id,
            'rate': 45.0,
        })

    def test_shop_payment_validate_with_tables(self):
        """Test shop_payment_validate creates table.reservation when order has booked tables."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'tables_ids': [(6, 0, [self.table.id])],
            'floors': self.floor.id,
            'date': date.today(),
            'starting_at': '13:00',
            'ending_at': '15:00',
            'booking_amount': 45.0,
        })

        with MockRequest(self.env):
            with patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment_validate',
                       return_value='super_result'):
                res = self.controller.shop_payment_validate(sale_order_id=order.id)
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'super_result')
                self.assertTrue(order.table_reservation_id)
                self.assertEqual(order.table_reservation_id.state, 'reserved')
                self.assertEqual(order.table_reservation_id.floor_id, self.floor)
                self.assertEqual(order.table_reservation_id.type, 'website')

    def test_shop_payment_validate_without_tables(self):
        """Test shop_payment_validate does not create table.reservation for normal orders."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        with MockRequest(self.env):
            with patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment_validate',
                       return_value='super_result'):
                res = self.controller.shop_payment_validate(sale_order_id=order.id)
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'super_result')
                self.assertFalse(order.table_reservation_id)

    def test_shop_payment_validate_public_user_uses_order_partner(self):
        """Test guest checkout payment attaches reservation to order.partner_id, not public user."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'tables_ids': [(6, 0, [self.table.id])],
            'floors': self.floor.id,
            'date': date.today(),
            'starting_at': '16:00',
            'ending_at': '18:00',
            'booking_amount': 45.0,
        })
        public_user = self.env.ref('base.public_user')
        with MockRequest(self.env(user=public_user)):
            with patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment_validate',
                       return_value='super_result'):
                res = self.controller.shop_payment_validate(sale_order_id=order.id)
                self.assertEqual(order.table_reservation_id.customer_id, self.partner)

