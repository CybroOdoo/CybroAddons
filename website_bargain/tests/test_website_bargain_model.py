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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields
from datetime import timedelta
import logging



class TestWebsiteBargainModel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.website = cls.env['website'].get_current_website()
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
            # 'sale_line_warn': 'no-message',
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