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

from odoo.tests.common import HttpCase, tagged
from odoo import fields
from datetime import timedelta
import json


@tagged('post_install', '-at_install')
class TestWebsiteBargainController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.website = cls.env.ref('base.default_website', raise_if_not_found=False) or cls.env['website'].search([], limit=1)

        cls.user = cls.env.ref('base.user_admin')

        cls.product = cls.env['product.product'].create({
            'name': 'Auction Product',
            'type': 'consu',
        })

        cls.template = cls.env['bargain.template'].create({
            'name': 'Auction Template',
            'product_id': cls.product.product_tmpl_id.id,
        })

        cls.auction = cls.env['website.bargain'].create({
            'website_id': cls.website.id,
            'template_id': cls.template.id,
            'auction_manager_id': cls.user.id,
            'product_id': cls.product.product_tmpl_id.id,
            'initial_price': 100,
            'is_buy_now': True,
            'price_buy_now': 150,
            'start_time': fields.Datetime.now(),
            'end_time': fields.Datetime.now() + timedelta(days=1),
            'state': 'running',
        })


    def test_01_auction_timer(self):
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/auction/timer',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id,
                    'product_id': self.product.product_tmpl_id.id,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('error', data)
        self.assertEqual(data.get('result', {}).get('state'), 'running')

    def test_02_subscribe(self):
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/subscribe/bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id,
                    'text': 'subscribe',
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('error', data)

    def test_03_buy_now(self):
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/buy/now',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id,
                    'product_id': self.product.id,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('error', data)
        self.assertTrue(data.get('result'))
        self.assertEqual(self.auction.state, 'finished')
        order = self.env['sale.order'].search([
            ('partner_id', '=', self.user.partner_id.id),
            ('order_line.product_id', '=', self.product.id),
        ], limit=1)
        self.assertTrue(order, "Sale order must be created upon Buy Now")

    def test_04_place_bid_and_auction_close(self):
        """Test placing a bid and closing auction generates winner sale order"""
        auction2 = self.env['website.bargain'].create({
            'website_id': self.website.id,
            'template_id': self.template.id,
            'auction_manager_id': self.user.id,
            'product_id': self.product.product_tmpl_id.id,
            'initial_price': 50,
            'start_time': fields.Datetime.now() - timedelta(hours=1),
            'end_time': fields.Datetime.now() + timedelta(days=1),
            'state': 'running',
        })
        self.authenticate(self.user.login, 'admin')

        # Place bid
        bid_response = self.url_open(
            '/place_bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction2.id,
                    'bid_amount': 75.0,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(bid_response.status_code, 200)
        bid_data = bid_response.json()
        self.assertNotIn('error', bid_data)
        self.assertTrue(bid_data.get('result', {}).get('success'))

        # Close auction
        close_response = self.url_open(
            '/auction/close',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction2.id,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(close_response.status_code, 200)
        close_data = close_response.json()
        self.assertNotIn('error', close_data)
        self.assertEqual(auction2.state, 'finished')

        # Check winner sale order
        winner_order = self.env['sale.order'].search([
            ('partner_id', '=', self.user.partner_id.id),
            ('order_line.price_unit', '=', 75.0),
        ], limit=1)
        self.assertTrue(winner_order, "Winner sale order must be created when auction closes")

    def test_05_winner_sale_order_route(self):
        """Test /shop/sale/order creates winner sale order when auction is expired"""
        auction = self.env['website.bargain'].create({
            'website_id': self.website.id,
            'template_id': self.template.id,
            'auction_manager_id': self.user.id,
            'product_id': self.product.product_tmpl_id.id,
            'initial_price': 50,
            'start_time': fields.Datetime.now() - timedelta(hours=2),
            'end_time': fields.Datetime.now() - timedelta(minutes=1),
            'state': 'running',
        })
        self.env['bargain.information'].create({
            'bidder_id': self.user.partner_id.id,
            'auction_id': auction.id,
            'bid_offer': 90.0,
            'status': 'Bid Placed',
        })
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/shop/sale/order',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction.id,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('error', data)
        self.assertTrue(data.get('result'))
        self.assertEqual(auction.state, 'finished')

    def test_06_subscribe_status(self):
        """Test /subscribe/status returns boolean subscription status"""
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/subscribe/status',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('error', data)
        self.assertIn('result', data)

    def test_07_bid_cancel(self):
        """Test cancelling a bid via /bid/cancel route"""
        bid = self.env['bargain.information'].create({
            'bidder_id': self.user.partner_id.id,
            'auction_id': self.auction.id,
            'bid_offer': 120.0,
            'status': 'Bid Placed',
        })
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(f'/bid/cancel/{bid.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(bid.status, 'cancelled')

    def test_08_place_bid_validation_errors(self):
        """Test /place_bid returns structured errors for low bids and duplicate bids"""
        auction = self.env['website.bargain'].create({
            'website_id': self.website.id,
            'template_id': self.template.id,
            'auction_manager_id': self.user.id,
            'product_id': self.product.product_tmpl_id.id,
            'initial_price': 100,
            'start_time': fields.Datetime.now(),
            'end_time': fields.Datetime.now() + timedelta(days=1),
            'state': 'running',
        })
        self.authenticate(self.user.login, 'admin')

        # Test bid below initial price
        low_resp = self.url_open(
            '/place_bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction.id,
                    'bid_amount': 50.0,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        low_data = low_resp.json()
        self.assertNotIn('error', low_data)
        self.assertEqual(low_data.get('result', {}).get('error'), 'low_initial')

        # Valid bid
        valid_resp = self.url_open(
            '/place_bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction.id,
                    'bid_amount': 150.0,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        valid_data = valid_resp.json()
        self.assertTrue(valid_data.get('result', {}).get('success'))

        # Duplicate bid
        dup_resp = self.url_open(
            '/place_bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction.id,
                    'bid_amount': 150.0,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        dup_data = dup_resp.json()
        self.assertEqual(dup_data.get('result', {}).get('error'), 'duplicate_bid')

        # Low bid (lower than current highest bid 150)
        low_bid_resp = self.url_open(
            '/place_bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': auction.id,
                    'bid_amount': 120.0,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        low_bid_data = low_bid_resp.json()
        self.assertEqual(low_bid_data.get('result', {}).get('error'), 'low_bid')

