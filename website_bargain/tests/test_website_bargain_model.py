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

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo import fields
from datetime import timedelta


@tagged('post_install', '-at_install')
class TestWebsiteBargainModel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.website = cls.env.ref('base.default_website', raise_if_not_found=False) or cls.env['website'].search([], limit=1)
        cls.user = cls.env.ref('base.user_admin')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Auction Customer',
            'email': 'auction@test.com',
            'autopost_bills': 'never',
        })

        cls.product = cls.env['product.template'].create({
            'name': 'Auction Product',
            'type': 'service',
            'list_price': 100,
        })

        cls.template = cls.env['bargain.template'].create({
            'name': 'Auction Template',
            'product_id': cls.product.id,
        })

        cls.auction = cls.env['website.bargain'].create({
            'website_id': cls.website.id,
            'template_id': cls.template.id,
            'auction_manager_id': cls.user.id,
            'product_id': cls.product.id,
            'initial_price': 100,
            'start_time': fields.Datetime.now(),
            'end_time': fields.Datetime.now() + timedelta(days=1),
        })


    def test_01_onchange_template(self):
        """Test auction name auto generation"""


        self.auction._onchange_template_id()

        self.assertEqual(
            self.auction.name,
            f"Auction for {self.product.name}"
        )

    def test_02_invalid_end_date(self):
        """End date must be greater than start date"""

        with self.assertRaises(ValidationError):
            self.env['website.bargain'].create({
                'website_id': self.website.id,
                'template_id': self.template.id,
                'auction_manager_id': self.user.id,
                'product_id': self.product.id,
                'initial_price': 100,
                'start_time': fields.Datetime.now(),
                'end_time': fields.Datetime.now() - timedelta(days=1),
            })


    def test_03_confirm_auction(self):
        """Test confirm action"""


        self.auction.action_confirm()

        self.assertEqual(self.auction.state, 'confirmed')
        self.assertTrue(self.auction.product_id.is_published)


    def test_04_run_auction(self):
        """Test run auction"""


        self.auction.action_run_auction()

        self.assertEqual(self.auction.state, 'running')
        self.assertTrue(self.auction.product_id.is_auction)


    def test_05_complete_auction(self):
        """Test complete auction"""


        self.auction.action_complete()

        self.assertEqual(self.auction.state, 'finished')
        self.assertFalse(self.auction.product_id.is_auction)


    def test_06_close_auction(self):
        """Test close auction"""

        self.auction.action_close()

        self.assertEqual(self.auction.state, 'closed')

    def test_07_subscriber_creation(self):
        """Test subscriber creation"""

        subscriber = self.env['bargain.subscribers'].create({
            'subscriber_id': self.partner.id,
            'auction_id': self.auction.id,
            'is_subscribed': True,
        })

        self.assertTrue(subscriber.is_subscribed)

    def test_08_bid_creation(self):
        """Test bid creation"""

        bid = self.env['bargain.information'].create({
            'bidder_id': self.partner.id,
            'auction_id': self.auction.id,
            'bid_offer': 500,
            'status': 'Bid Placed'
        })

        self.assertEqual(bid.bid_offer, 500)

    def test_09_auction_auto_start(self):
        """Test cron auto start starts confirmed auctions whose start_time has arrived"""
        product = self.env['product.template'].create({
            'name': 'Auto Start Product',
            'type': 'service',
            'list_price': 50,
        })
        auction = self.env['website.bargain'].create({
            'website_id': self.website.id,
            'auction_manager_id': self.user.id,
            'product_id': product.id,
            'initial_price': 50,
            'start_time': fields.Datetime.now() - timedelta(minutes=1),
            'end_time': fields.Datetime.now() + timedelta(days=1),
        })
        auction.action_confirm()
        self.assertEqual(auction.state, 'confirmed')

        self.env['website.bargain'].auction_auto_start()

        self.assertEqual(auction.state, 'running')
        self.assertTrue(auction.product_id.is_auction)

    def test_10_auction_auto_end(self):
        """Test cron auto end finishes expired running auctions and creates sale order for winner"""
        product = self.env['product.template'].create({
            'name': 'Auto End Product',
            'type': 'service',
            'list_price': 80,
        })
        auction = self.env['website.bargain'].create({
            'website_id': self.website.id,
            'auction_manager_id': self.user.id,
            'product_id': product.id,
            'initial_price': 80,
            'start_time': fields.Datetime.now() - timedelta(hours=2),
            'end_time': fields.Datetime.now() - timedelta(minutes=1),
            'state': 'running',
            'is_winner_notification': True,
            'is_loser_notification': True,
        })
        product.is_auction = True

        # Place bids
        loser_partner = self.env['res.partner'].create({
            'name': 'Loser Partner',
            'email': 'loser@test.com',
            'autopost_bills': 'never',
        })
        self.env['bargain.information'].create({
            'bidder_id': loser_partner.id,
            'auction_id': auction.id,
            'bid_offer': 100,
            'status': 'Bid Placed'
        })
        self.env['bargain.information'].create({
            'bidder_id': self.partner.id,
            'auction_id': auction.id,
            'bid_offer': 150,
            'status': 'Bid Placed'
        })

        # Run auto end cron
        self.env['website.bargain'].auction_auto_end()

        self.assertEqual(auction.state, 'finished')
        self.assertFalse(auction.product_id.is_auction)

        # Check sale order creation for the winner
        order = self.env['sale.order'].search([
            ('partner_id', '=', self.partner.id),
            ('order_line.product_id', '=', product.product_variant_id.id)
        ], limit=1)
        self.assertTrue(order, "Sale order must be created for the winning bidder")
        self.assertEqual(order.order_line.price_unit, 150)

    def test_11_send_email_notification(self):
        """Test cron admin notification before auction ends"""
        auction = self.env['website.bargain'].create({
            'website_id': self.website.id,
            'auction_manager_id': self.user.id,
            'product_id': self.product.id,
            'initial_price': 80,
            'start_time': fields.Datetime.now() - timedelta(hours=2),
            'end_time': fields.Datetime.now() + timedelta(minutes=4),
            'state': 'running',
            'is_activate': True,
            'notify_on': 5,
            'notify_selection': 'minutes',
            'is_notification_send': False,
        })
        self.env['website.bargain'].send_email_notification()
        self.assertTrue(auction.is_notification_send)